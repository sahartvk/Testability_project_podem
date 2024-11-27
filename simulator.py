class Net:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.value = None


class Gate:
    def __init__(self, type_, inputs, output, delay=0):
        self.type = type_  # Gate type (e.g., AND, NAND, etc.)
        self.inputs = inputs  # List of input net numbers
        self.output = output  # Output net number
        self.delay = delay  # Gate delay


class CircuitSimulator:
    def __init__(self):
        file_name = ''
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
        pass

    
    def simulation_with_delay(self):
        pass



