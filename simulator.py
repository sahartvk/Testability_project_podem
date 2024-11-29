class Net:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.value = []     # Stores '0', '1', 'U', or 'Z'


class Gate:
    def __init__(self, type_, inputs, output, delay=0):
        self.type = type_  
        self.inputs = inputs  
        self.output = output  
        self.delay = delay  


class CircuitSimulator:
    def __init__(self, file_name):
        self.file_name = file_name
        self.gates = []
        self.inputs = []
        self.outputs = []
        self.input_values = []
        self.nets = []


    def read_isc_file(self):
        # TODO: store delays
        with open(self.file_name, 'r') as f:
            lines = f.readlines()

        max_net_number = 0
        for line in lines:
            if line.strip() and not line.startswith("*"):
                tokens = line.split()
                max_net_number = max(max_net_number, int(tokens[0]))

        self.nets = [None] * (max_net_number + 1)

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("*"):  
                i += 1
                continue

            tokens = line.split()
            net_number = int(tokens[0])  
            gate_type = tokens[2]   
            self.nets[net_number] = Net(net_number, f"Net{net_number}")    

            if gate_type == 'inpt':  
                self.inputs.append(net_number)
                
            elif gate_type == 'from':  
                input_net = int(tokens[3].replace("gat", ""))
                output_net = net_number
                self.gates.append(Gate("FANOUT", [input_net], output_net))

            elif gate_type in ['and', 'nand', 'or', 'nor', 'xor', 'xnor', 'not', 'buf']: 
                output_net = net_number
                num_inputs = int(tokens[4])
                i += 1
                input_line = lines[i].strip()
                input_tokens = input_line.split()
                input_nets = [int(token) for token in input_tokens[:num_inputs]]

                delay = 0
                if len(input_tokens) > num_inputs:  
                    delay = int(input_tokens[num_inputs]) 

                self.gates.append(Gate(gate_type.upper(), input_nets, output_net, delay))
                
            i += 1


    def read_inputs(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        input_order = list(map(int, lines[0].strip().split()))
        self.input_values = []
        input_indices = [input_order.index(input_net) for input_net in self.inputs]
        for line in lines[1:]:
            bits = line.strip()
            bits = bits.split()
            time_step_values = []

            for idx in input_indices:
                value = bits[idx]
                if value in {'0', '1'}:  
                    time_step_values.append(int(value))
                else:
                    time_step_values.append(value)

            self.input_values.append(time_step_values)



    # def true_value_simulation(self):
    # # need to delete values before each simulation
    #     # print(len(self.input_values))
    #     for time in range(len(self.input_values)): 
    #         for idx, input_net in enumerate(self.inputs):
    #             self.nets[input_net].value.append(self.input_values[time][idx])

    #         for gate in self.gates:
    #             gate_inputs_value = [self.nets[net].value[time] for net in gate.inputs]
    #             gate_output_value = self.calculate_gate_output(gate.type, gate_inputs_value)
    #             self.nets[gate.output].value.append(gate_output_value)

    #     print("\nTrue Value Simulation:")
    #     for net in self.nets:
    #         if net:
    #             print(f"Net {net.number}: {net.value}")
    #             # print(f"Net {net.number}: {''.join(net.value)}")

    def true_value_simulation(self):
        max_time = len(self.input_values)
        for net in self.nets:
            if net:
                net.value = [None] * max_time

        for time in range(max_time):
            for idx, input_net in enumerate(self.inputs):
                self.nets[input_net].value[time] = self.input_values[time][idx]

            for gate in self.gates:
                gate_inputs_value = [self.nets[net].value[time] for net in gate.inputs]
                gate_output_value = self.calculate_gate_output(gate.type, gate_inputs_value)
                self.nets[gate.output].value[time] = gate_output_value

        # print("\nTrue Value Simulation:")
        # for net in self.nets:
        #     if net:
        #         print(f"Net {net.number}: {net.value}")


    @staticmethod
    def calculate_gate_output(gate_type, inputs):
        if gate_type == 'AND':
            if 0 in inputs:
                return 0
            elif 'Z' in inputs:
                return 'Z'
            elif 'U' in inputs:
                return 'U'
            else:
                return 1 

        elif gate_type == 'NAND':
            if 0 in inputs:
                return 1
            elif 'Z' in inputs:
                return 'Z'
            elif 'U' in inputs:
                return 'U'
            else:
                return 0 
       
        elif gate_type == 'OR':
            if 1 in inputs:
                return 1
            elif 'Z' in inputs:
                return 'Z'
            elif 'U' in inputs:
                return 'U'
            else:
                return 0 

        elif gate_type == 'NOR':
            if 1 in inputs:
                return 0
            elif 'Z' in inputs:
                return 'Z'
            elif 'U' in inputs:
                return 'U'
            else:
                return 1

        elif gate_type == 'XOR':
            if 'Z' in inputs or 'U' in inputs:
                return 'U'
            else:
                return int(sum(inputs) % 2 == 1)

        elif gate_type == 'XNOR':
            if 'Z' in inputs or 'U' in inputs:
                return 'U'
            else:
                return int(sum(inputs) % 2 == 0) 
        
        elif gate_type == 'NOT':
            input_value = inputs[0]
            if input_value == 'Z' or input_value == 'U':
                return input_value
            else:
                return 1 if input_value == 0 else 0

        elif gate_type in ['BUF', 'FANOUT']:
            return inputs[0]

        else:
            return 'U' 
    

    #TODO:it may have problems
    def simulation_with_delay(self):
        self.true_value_simulation()

        max_time = max(len(self.nets[net].value) for net in range(len(self.nets)) if self.nets[net])

        for gate in self.gates:
            all_inputs_are_circuit_inputs = all(input_net in self.inputs for input_net in gate.inputs)
            #TODO: check that is it reference access?
            output_net = self.nets[gate.output]
            delay = gate.delay

            if all_inputs_are_circuit_inputs:
                output_net.value = ['U'] * delay + output_net.value
            else:
                gate_inputs_values = [self.nets[input_net].value for input_net in gate.inputs]

                #TODO:is it necessary? accoarding to last lines
                for idx in range(len(gate_inputs_values)):
                    gate_inputs_values[idx] += [gate_inputs_values[idx][-1]] * (max_time - len(gate_inputs_values[idx]))

                new_output_values = []
                for time in range(max_time):
                    input_values_at_time = [inputs[time] for inputs in gate_inputs_values]
                    new_output_values.append(self.calculate_gate_output(gate.type, input_values_at_time))

                new_output_values = ['U'] * delay + new_output_values
                output_net.value = new_output_values

           
            output_net.value += [output_net.value[-1]] * (max_time - len(output_net.value))

            max_time = max(max_time, len(output_net.value))

        for net in self.nets:
            if net:
                net.value += [net.value[-1]] * (max_time - len(net.value))

        # print("\nSimulation with Delay:")
        # for net in self.nets:
        #     if net:
        #         print(f"Net {net.number}: {net.value}")
        #         # print(f"Net {net.number}: {''.join(net.value)}")




if __name__ == "__main__":
    simulator = CircuitSimulator("D:/courses/sharif/term1/Testability/project/1/code/Testability_project/c17.isc")
    simulator.read_isc_file()
    simulator.read_inputs("D:/courses/sharif/term1/Testability/project/1/code/Testability_project/input.txt")
    simulator.true_value_simulation()

    print("\nTrue Value Simulation:")
    for net in simulator.nets:
        if net:
            print(f"Net {net.number}: {net.value}")

    simulator.simulation_with_delay()
    print("\nSimulation with Delay:")
    for net in simulator.nets:
        if net:
            print(f"Net {net.number}: {net.value}")


