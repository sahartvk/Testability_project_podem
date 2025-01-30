from simulator import CircuitSimulator


class TestGenerator:
    def __init__(self, circuit_simulator, fault_file):
        self.simulator = circuit_simulator
        self.fault_file = fault_file
        self.faults = self.load_faults(fault_file)

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

    
    def podem():
        pass


    def objective(self, fault_net, fault_type):
        if self.simulator.nets[fault_net].value == 'X':
            return fault_net, 1 if fault_type == 'sa0' else 0

        # TODO: fix
        d_frontier = [g for g in self.simulator.gates if self.nets[g.output].value == 'X' and 
                    any(self.nets[i].value in ['D', "D'"] for i in g.inputs)]
        
        if not d_frontier:
            return None, None

        gate = d_frontier[0]
        unassigned_inputs = [i for i in gate.inputs if self.simulator.nets[i].value == 'X']
        if not unassigned_inputs:
            return None, None
        selected_input = unassigned_inputs[0] 
        controlling_values = {'AND': 0, 'OR': 1}
        if gate.gate_type in controlling_values:
            c = controlling_values[gate.gate_type]
        elif self.simulator.nets[selected_input].cc0 < self.simulator.nets[selected_input].cc1:
            c = 0
        else:
            c = 1

        return selected_input, ~c
