from simulator import CircuitSimulator, Gate


class TestGenerator:
    def __init__(self, circuit_simulator: CircuitSimulator, fault_file):
        self.simulator = circuit_simulator
        self.fault_file = fault_file
        self.faults = self.load_faults(fault_file)
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
            test_vec = self.call_podem(fault_net, stuck_val)
            results.append((fault_net, stuck_val, test_vec))

        # Save test vectors
        with open(out_file, "w") as wf:
            wf.write("net   fault " + " ".join(map(str, self.inputs)) + "\n")
            for (fault_net, stuck_val, tv) in results:
                fault_str = f"{fault_net}\t{stuck_val}"
                if tv is None:
                    wf.write(f"{fault_str} none found\n")
                else:
                    tv_str = "  ".join(map(str, tv))
                    wf.write(f"{fault_str} {tv_str}\n")

        print(f"PODEM completed. Results saved to {out_file}.")

    def XPathCheck(self):
        pass

    def XPathCheck(self, fault_net):
        """
        بررسی می‌کند که آیا مقداری نامشخص (X) در مسیر انتشار اشکال وجود دارد یا نه.
        """
        # اگر خطای مشخص‌شده در یکی از ورودی‌های مدار باشد، مقدار X را بررسی می‌کنیم
        if fault_net in self.simulator.inputs:
            return self.simulator.nets[fault_net].value[0] == 'X'
        
        # پیمایش از طریق DFrontier
        while True:
            for gate in self.d_frontier:
                if gate.output == fault_net:
                    # بررسی گیت‌های یک ورودی (INV, BUF)
                    if gate.gate_type in ["BUF", "INV"]:
                        if self.simulator.nets[gate.inputs[0]].value[0] == 'X':
                            fault_net = gate.inputs[0]
                            return True
                        else:
                            return False
                    else:
                        # بررسی گیت‌های چندورودی (AND, OR, NAND, NOR, XOR, XNOR)
                        for input_net in gate.inputs:
                            if self.simulator.nets[input_net].value[0] == 'X':
                                fault_net = input_net
                                return True
                        return False
            return True

    
    def call_podem(self, fault_net, fault_type):
        self.initialize_nets_to_x()
        # TODO: throw exception
        # TODO: is ot necessary to activate the fault?
        # if(self.activate_fault() == False):
        #     return fault_net, fault_type, None
        
        if self.podem(fault_net, fault_type) == False:
            return fault_net, fault_type, None
        
        test_vec =[]
        for input_net in self.simulator.inputs:
            input_val = self.simulator.nets[input_net].value[0]
            test_vec.append[input_val]

        return fault_net, fault_type, test_vec
        

    def initialize_nets_to_x(self):
        for net in self.simulator.nets:
            if net:
                net.value = ['X']


    def activate_fault(self, fault_net, fault_type):
        if fault_type == 'sa0':
            self.simulator.nets[fault_net] = 'D'
        elif fault_type == 'sa1':
            self.simulator.nets[fault_net] = 'Db'
        else:
            return False
        return True
            

    def podem(self, fault_net, fault_type):
        self.UpdateDFrontier()

        for output_net in self.simulator.outputs:
            if self.simulator.nets[output_net].value in ['D', "Db"]:
                return True
            
        if len(self.d_frontier) < 1 and self.XPathCheck() == False:
            return False
        
        objective_input, objective_value = self.objective(fault_net, fault_type)
        pi_net, pi_value = self.backtrace(objective_input, objective_value)
        
        # TODO: check
        self.simulator.nets[pi_net] = pi_value
        if pi_net == fault_net:
            if pi_value == 1 and fault_type == 'sa0':
                self.simulator.nets[pi_net] = 'D'
            elif pi_value == 0 and fault_type == 'sa1':
                self.simulator.nets[pi_net] = 'Db'


        # TODO: is it okay?  ->  logicSimulate(faultNode, stuckAt, wires)
        self.imply(fault_net, fault_type)

        if self.podem(fault_net, fault_type) == True:
            return True

        # TODO: backtrack -> it has problems
        if pi_value == '1':
            pi_value = '0'
        else:
            pi_value = '1'
        self.simulator.nets[pi_net] = pi_value

        # TODO: is it okay?  ->  logicSimulate(faultNode, stuckAt, wires)
        self.imply(fault_net, fault_type)

        if self.podem(fault_net, fault_type) == True:
            return True

        pi_value = 'X'
        self.simulator.nets[pi_net] = pi_value

        return False
    


    def UpdateDFrontier(self):
        # TODO: check function
        self.d_frontier = [g for g in self.simulator.gates if self.simulator.nets[g.output].value == 'X' and 
                    any(self.nets[i].value in ['D', "Db"] for i in g.inputs)]



    def objective(self, fault_net, fault_type):
        # TODO: 1 or D?
        if self.simulator.nets[fault_net].value == 'X':
            return fault_net, 1 if fault_type == 'sa0' else 0

        gate = self.d_frontier[0]
        unassigned_inputs = [i for i in gate.inputs if self.simulator.nets[i].value == 'X']

        # TODO: return none, none 
        selected_input = unassigned_inputs[0] 
        controlling_values = {'AND': 0, 'OR': 1, 'NAND': 0, 'NOR': 1}
        if gate.gate_type in controlling_values:
            c = controlling_values[gate.gate_type]
        elif self.simulator.nets[selected_input].cc0 < self.simulator.nets[selected_input].cc1:
            c = 0
        else:
            c = 1
        return selected_input, ~c
    

    def backtrace(self, s, v):
        while s not in self.simulator.inputs:
            gate = [g for g in self.simulator.gates if g.output == s][0]
            # TODO: xor and xnor?
            if gate.gate_type in {'NAND', 'NOR', 'NOT'}:
                v = ~v

            # TODO: xor and xnor?
            if self.requires_all_inputs(gate, v):
                a = self.select_hardest_control_input(gate, v)
            else:
                a = self.select_easiest_control_input(gate, v)

            s = a 
        return s, v


    def requires_all_inputs(self, gate, v):
        if (gate.gate_type == 'AND' and v == 1) or (gate.gate_type == 'NAND' and v == 0) or (gate.gate_type == 'OR' and v == 0) or (gate.gate_type == 'NOR' and v == 1):
            return True 
        return False


    def select_hardest_control_input(self, gate: Gate, v):
        if v == 0:
            return max(gate.inputs, key=lambda net: self.simulator.nets[net].cc0)
        elif v == 1:
            return max(gate.inputs, key=lambda net: self.simulator.nets[net].cc1)
        return None


    def select_easiest_control_input(self, gate, v):
        if v == 0:
            return min(gate.inputs, key=lambda net: self.simulator.nets[net].cc0)
        elif v == 1:
            return min(gate.inputs, key=lambda net: self.simulator.nets[net].cc1)
        return None

    def imply(self, fault_net, fault_type):
        for net in self.simulator.nets:
            if net and net.number not in self.simulator.inputs:
                net.value = ['X']

        for gate in self.simulator.gates:
            gate_inputs_value = [self.simulator.nets[net].value[0] for net in gate.inputs]
            gate_output_value = Gate.calculate_5valued_gate_output(gate.type, gate_inputs_value)
            if fault_net == gate.output:
                if gate_output_value == 1 and fault_type == 'sa0':
                    gate_output_value = 'D'
                elif gate_output_value == 0 and fault_type == 'sa1':
                    gate_output_value = 'Db'
                else:
                    return False
            self.simulator.nets[gate.output].value[0] = gate_output_value
        return True
