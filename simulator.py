class Net:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.value = []


class Gate:
    def __init__(self, type_, inputs, output, delay=0):
        self.type = type_  # Gate type (e.g., AND, NAND, etc.)
        self.inputs = inputs  # List of input net numbers
        self.output = output  # Output net number
        self.delay = delay  # Gate delay


class CircuitSimulator:
    def __init__(self, file_name):
        file_name = file_name
        gates = []
        inputs = []
        outputs = []
        input_values = []
        nets = []


    def read_isc_file(self):
        with open(self.file_name, 'r') as f:
            lines = f.readlines()

        self.nets = [None] * len(lines)
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
                self.gates.append(Gate("BUF", [input_net], output_net))

            elif gate_type in ['and', 'nand', 'or', 'nor', 'xor', 'xnor', 'not']: 
                output_net = net_number
                
                i += 1
                input_line = lines[i].strip()
                input_tokens = input_line.split()
                input_nets = [int(token) for token in input_tokens]
                self.gates.append(Gate(gate_type.upper(), input_nets, output_net))
                self.nets.append(Net(output_net, f"Net{output_net}"))

            i += 1

    
    def read_inputs(self):
        pass


    def true_value_simulation(self):

        # TODO: read inputs

        for time in range(len(self.input_values)): 
        # Assign input values to nets
            for idx, input_net in enumerate(self.inputs):
                self.nets[input_net].value.append(self.input_values[time][idx])

            # Process gates
            for gate in self.gates:
                gate_inputs_value = [self.nets[net].value[time] for net in gate.inputs]
                gate_output_value = self.calculate_gate_output(gate.type, gate_inputs_value)
                self.nets[gate.output].value[time] = gate_output_value

        # Print net values
        # print("Simulation Result:")
        # for net in self.nets:
        #     print(f"Net {net.number}: {net.value}")

    
    @staticmethod
    def calculate_gate_output(gate_type, inputs):
        if gate_type == 'AND':
            return int(all(inputs))
        elif gate_type == 'NAND':
            return int(not all(inputs))
        elif gate_type == 'OR':
            return int(any(inputs))
        elif gate_type == 'NOR':
            return int(not any(inputs))
        elif gate_type == 'XOR':
            return int(sum(inputs) % 2 == 1)
        elif gate_type == 'XNOR':
            return int(sum(inputs) % 2 == 0)
        elif gate_type == 'NOT':
            return int(not inputs[0])
        elif gate_type == 'BUF':
            return inputs[0]
        else:
            return 'U'  # Unknown for unsupported gates
    
    def simulation_with_delay(self):
        pass



