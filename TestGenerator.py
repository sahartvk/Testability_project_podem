from simulator import CircuitSimulator, Gate


class TestGenerator:
    def __init__(self, circuit_simulator: CircuitSimulator, fault_file):
        self.simulator = circuit_simulator
        self.fault_file = fault_file
        self.faults = self.load_faults(fault_file)
        self.d_frontier = []

    def load_faults(self, fault_file):
        faults = []
        with open(fault_file, 'r') as f:
            for line in f:
                if line.strip():  
                    tokens = line.split()
                    fault_net = tokens[0]
                    fault_type = tokens[1]
                    faults.append((fault_net, fault_type))
        return faults



    # TODO:fix
    def generate_all_test_vectors(self, output_file='test_vectors.txt'):
        with open(output_file, 'w') as f:
            
            f.write("net fault " + " ".join(map(str, self.simulator.inputs)) + "\n")

            for fault in self.faults:
                test_vector = self.generate_test_vector_for_fault(fault)
                fault_line, fault_type = fault
                if test_vector:
                    f.write(f"{fault_line} {fault_type} " + " ".join(map(str, test_vector)) + "\n")
                else:
                    f.write(f"{fault_line} {fault_type} none found\n")

    def XPathCheck(self):
        if (len(self.d_frontier) < 1):
            return False
        return True

    def podem(self, fault_net, fault_type):
        # TODO: trigger fault for first time.
        self.UpdateDFrontier()

        for output_net in self.simulator.outputs:
            if self.simulator.nets[output_net].value in ['D', "Db"]:
                return True
            
        if (self.XPathCheck() == False):
            return False
        
        objective_input, objective_value = self.objective(fault_net, fault_type)
        pi_net, pi_value = self.backtrace(objective_input, objective_value)
        
        # TODO: check
        self.simulator.nets[pi_net] = pi_value
        if (pi_net == fault_net):
            if (pi_value == 1 and fault_type == 'sa0'):
                self.simulator.nets[pi_net] = 'D'
            elif (pi_value == 0 and fault_type == 'sa1'):
                self.simulator.nets[pi_net] = 'Db'


        # TODO: is it okay?  ->  logicSimulate(faultNode, stuckAt, wires)
        self.imply()

        if (self.podem(fault_net, fault_type) == True):
            return True

        # TODO: backtrack -> it has problems
        if(pi_value == '1'):
            pi_value = '0'
        else:
            pi_value = '1'
        self.simulator.nets[pi_net] = pi_value

        # TODO: is it okay?  ->  logicSimulate(faultNode, stuckAt, wires)
        self.imply()

        if (self.podem(fault_net, fault_type) == True):
            return True

        pi_value = 'X'
        self.simulator.nets[pi_net] = pi_value

        return False

    def UpdateDFrontier(self):
        # TODO: check function
        self.d_frontier = [g for g in self.simulator.gates if self.simulator.nets[g.output].value == 'X' and 
                    any(self.nets[i].value in ['D', "Db"] for i in g.inputs)]



    def objective(self, fault_net, fault_type):
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

    def imply(self):
        # TODO: 5-value logic in calculate_gate_output
        for gate in self.simulator.gates:
            gate_inputs_value = [self.simulator.nets[net].value for net in gate.inputs]
            gate_output_value = self.simulator.calculate_gate_output(gate.type, gate_inputs_value)
            self.simulator.nets[gate.output].value = gate_output_value
