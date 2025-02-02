from simulator import CircuitSimulator, Gate, Net
import os


class TestGenerator:
    def __init__(self, circuit_file_name):
        # self.simulator = circuit_simulator
        self.circuit_file_name = os.path.join(os.getcwd(), circuit_file_name)
        self.simulator = CircuitSimulator(self.circuit_file_name)
        self.simulator.read_isc_file()
        self.simulator.calculate_scoap()
        # self.fault_file = fault_file
        # self.faults = self.load_faults(fault_file)
        self.d_frontier = []


    def run_podem_for_faults(self, fault_file="fault_file.txt", out_file="test_vector.txt"):
        """
        Reads faults from fault_file, runs PODEM, and writes test vectors to out_file.
        """
        faults = []
        with open(fault_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue
                fault_net = int(parts[0])
                stuck_val = parts[1].lower()
                faults.append((fault_net, stuck_val))

        results = []
        for (fault_net, stuck_val) in faults:
            fault_net, stuck_val, test_vec = self.call_podem(fault_net, stuck_val)
            results.append((fault_net, stuck_val, test_vec))

        # Save test vectors
        with open(out_file, "w") as wf:
            wf.write("net\tfault\t" + "\t".join(map(str, self.simulator.inputs)) + "\n")
            for (fault_net, stuck_val, tv) in results:
                fault_str = f"{fault_net}\t{stuck_val}"
                if tv is None:
                    wf.write(f"{fault_str}\tnone found\n")
                else:
                    tv_str = "\t".join(map(str, tv))
                    wf.write(f"{fault_str}\t{tv_str}\n")

        print(f"PODEM completed. Results saved to {out_file}.")



    def call_podem(self, fault_net, fault_type):
        self.initialize_nets_to_x()
        
        if self.podem(fault_net, fault_type) == False:
            return fault_net, fault_type, None
        
        test_vec =[]
        for input_net in self.simulator.inputs:
            input_val = self.simulator.nets[input_net].value[0]
            test_vec.append(input_val)

        return fault_net, fault_type, test_vec

    def XPathCheck(self, fault_net):
        if fault_net in self.simulator.inputs:
            return self.simulator.nets[fault_net].value[0] == 'X'
        
        while True:
            for gate in self.d_frontier:
                if gate.output == fault_net:
                    if gate.type in ["BUF", "NOT", "FANOUT"]:
                        if self.simulator.nets[gate.inputs[0]].value[0] == 'X':
                            # TODO: below ????
                            fault_net = gate.inputs[0]
                            return True
                        else:
                            return False
                    else:
                        for input_net in gate.inputs:
                            if self.simulator.nets[input_net].value[0] == 'X':
                                fault_net = input_net
                                return True
                        return False
            return True
        

    def initialize_nets_to_x(self):
        for net in self.simulator.nets:
            if net:
                net.value = ['X']
            

    def podem(self, fault_net, fault_type):
        self.UpdateDFrontier()

        for output_net in self.simulator.outputs:
            if self.simulator.nets[output_net].value[0] in ['D', "Db"]:
                return True
            
        if len(self.d_frontier) < 1 and self.XPathCheck(fault_net) == False:
            return False
        
        objective_input, objective_value = self.objective(fault_net, fault_type)
        pi_net, pi_value = self.backtrace(objective_input, objective_value)
        
        # TODO: check
        self.simulator.nets[pi_net].value[0] = pi_value
        if pi_net == fault_net:
            if pi_value == 1 and fault_type == 'sa0':
                self.simulator.nets[pi_net].value[0] = 'D'
            elif pi_value == 0 and fault_type == 'sa1':
                self.simulator.nets[pi_net].value[0] = 'Db'

        self.imply(fault_net, fault_type)

        if self.podem(fault_net, fault_type) == True:
            return True

        # TODO: backtrack -> it has problems
        if pi_value == '1':
            pi_value = '0'
        else:
            pi_value = '1'
        self.simulator.nets[pi_net].value[0] = pi_value

        self.imply(fault_net, fault_type)

        if self.podem(fault_net, fault_type) == True:
            return True

        pi_value = 'X'
        self.simulator.nets[pi_net].value[0] = pi_value

        return False
    


    def UpdateDFrontier(self):
        self.d_frontier = [
            g for g in self.simulator.gates 
            if self.simulator.nets[g.output].value and self.simulator.nets[g.output].value[0] == 'X' and 
            any(self.simulator.nets[i].value and self.simulator.nets[i].value[0] in ['D', "Db"] for i in g.inputs)
        ]


    def objective(self, fault_net, fault_type):
        # TODO: 1 or D?
        if self.simulator.nets[fault_net].value[0] == 'X':
            return fault_net, 1 if fault_type == 'sa0' else 0

        gate = self.d_frontier[0]
        unassigned_inputs = [i for i in gate.inputs if self.simulator.nets[i].value[0] == 'X']

        # TODO: return none, none 
        selected_input = unassigned_inputs[0] 
        controlling_values = {'AND': 0, 'OR': 1, 'NAND': 0, 'NOR': 1}
        if gate.type in controlling_values:
            c = controlling_values[gate.type]
        elif self.simulator.nets[selected_input].cc0 < self.simulator.nets[selected_input].cc1:
            c = 0
        else:
            c = 1
        return selected_input, 1-c
    

    def backtrace(self, s, v):
        while s not in self.simulator.inputs:
            gates = [g for g in self.simulator.gates if g.output == s]
            gate = gates[0]
            # TODO: xor and xnor?
            last_v = v
            if gate.type in {'NAND', 'NOR', 'NOT'}:
                v = 1 - v

            # TODO: xor and xnor?
            if self.requires_all_inputs(gate, last_v):
                a = self.select_hardest_control_input(gate, v)
            else:
                a = self.select_easiest_control_input(gate, v)

            s = a 
        return s, v


    def requires_all_inputs(self, gate, v):
        if (gate.type == 'AND' and v == 1) or (gate.type == 'NAND' and v == 0) or (gate.type == 'OR' and v == 0) or (gate.type == 'NOR' and v == 1):
            return True 
        return False


    def select_hardest_control_input(self, gate: Gate, v):
        unassigned_inputs = [net for net in gate.inputs if self.simulator.nets[net].value[0] == 'X']
        if unassigned_inputs:
            if v == 0:
                return max(unassigned_inputs, key=lambda net: self.simulator.nets[net].cc0)
            elif v == 1:
                return max(unassigned_inputs, key=lambda net: self.simulator.nets[net].cc1)
        return None


    def select_easiest_control_input(self, gate, v):
        unassigned_inputs = [net for net in gate.inputs if self.simulator.nets[net].value[0] == 'X']
        if unassigned_inputs:
            if v == 0:
                return min(unassigned_inputs, key=lambda net: self.simulator.nets[net].cc0)
            elif v == 1:
                return min(unassigned_inputs, key=lambda net: self.simulator.nets[net].cc1)
        return None


    def imply(self, fault_net, fault_type):
        # for net in self.simulator.nets:
        #     if net and net.number not in self.simulator.inputs:
        #         net.value[0] = ['X']
        for gate in self.simulator.gates:
            gate_inputs_value = [self.simulator.nets[net].value[0] for net in gate.inputs]
            gate_output_value = Gate.calculate_5valued_gate_output(gate.type, gate_inputs_value)
            if fault_net == gate.output:
                if gate_output_value == 1 and fault_type == 'sa0':
                    gate_output_value = 'D'
                elif gate_output_value == 0 and fault_type == 'sa1':
                    gate_output_value = 'Db'
                # else:
                #     return False
            self.simulator.nets[gate.output].value[0] = gate_output_value
        # return True

        # for net in self.simulator.nets:
        #     if net:
        #         print(f"{net.name}: {net.value}", end=" ")
        # print("")




if __name__ == "__main__":

    # test_atpg = TestGenerator("c17.isc")
    test_atpg = TestGenerator("c5.isc")
    test_atpg.run_podem_for_faults()