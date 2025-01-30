import os


class Net:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.value = []     # Stores '0', '1', 'U', or 'Z'
        self.cc1 = float('inf')
        self.cc0 = float('inf')
        self.co = float('inf')


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
        # list of input numbers
        self.inputs = []
        self.outputs = []
        self.input_values = []
        self.nets = []


    def read_isc_file(self):
        with open(self.file_name, 'r') as f:
            lines = f.readlines()

        max_net_number = 0
        for line in lines:
            if line.strip() and not line.startswith("*"):
                tokens = line.split()
                max_net_number = max(max_net_number, int(tokens[0]))

        self.nets = [None] * (max_net_number + 1)
        used_as_input = set()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("*"):  
                i += 1
                continue

            tokens = line.split()
            net_number = int(tokens[0])  
            gate_type = tokens[2]   

            if gate_type == 'inpt':  
                self.inputs.append(net_number)
                self.nets[net_number] = Net(net_number, f"Net {net_number}")    

            elif gate_type == 'from':  
                input_net = int(tokens[3].replace("gat", ""))
                output_net = net_number
                self.gates.append(Gate("FANOUT", [input_net], output_net))
                self.nets[net_number] = Net(net_number, f"Net {input_net}-{net_number}")    
                used_as_input.add(input_net)

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
                self.nets[net_number] = Net(net_number, f"Net {net_number}")    
                used_as_input.update(input_nets)
                
            i += 1

        all_outputs = {gate.output for gate in self.gates}
        self.outputs = list(all_outputs - used_as_input)

        # TODO: comment
        print(f"Outputs: {self.outputs}")



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


    def calculate_scoap(self):
        for net in self.nets:
            if net:
                net.cc0 = float('inf')  
                net.cc1 = float('inf')  
                net.co = float('inf')  

        for input_net in self.inputs:
            self.nets[input_net].cc0 = 1
            self.nets[input_net].cc1 = 1

        for gate in self.gates:
            gate_inputs = [self.nets[net] for net in gate.inputs]
            gate_output = self.nets[gate.output]

            if gate.type == 'AND':
                gate_output.cc0 = min(net.cc0 for net in gate_inputs) + 1
                gate_output.cc1 = sum(net.cc1 for net in gate_inputs) + 1

            if gate.type == 'NAND':
                gate_output.cc1 = min(net.cc0 for net in gate_inputs) + 1
                gate_output.cc0 = sum(net.cc1 for net in gate_inputs) + 1

            elif gate.type == 'OR':
                gate_output.cc0 = sum(net.cc0 for net in gate_inputs) + 1
                gate_output.cc1 = min(net.cc1 for net in gate_inputs) + 1

            elif gate.type == 'NOR':
                gate_output.cc1 = sum(net.cc0 for net in gate_inputs) + 1
                gate_output.cc0 = min(net.cc1 for net in gate_inputs) + 1

            elif gate.type == 'NOT':
                gate_output.cc0 = gate_inputs[0].cc1 + 1
                gate_output.cc1 = gate_inputs[0].cc0 + 1
            # TODO: fix code below for more than 2 inputs
            elif gate.type == 'XOR':
                gate_output.cc0 = min(
                    gate_inputs[0].cc0 + gate_inputs[1].cc0,
                    gate_inputs[0].cc1 + gate_inputs[1].cc1
                ) + 1
                gate_output.cc1 = min(
                    gate_inputs[0].cc0 + gate_inputs[1].cc1,
                    gate_inputs[0].cc1 + gate_inputs[1].cc0
                ) + 1
            # TODO: fix code below for more than 2 inputs
            elif gate.type == 'XNOR':
                gate_output.cc0 = min(
                    gate_inputs[0].cc0 + gate_inputs[1].cc1,
                    gate_inputs[0].cc1 + gate_inputs[1].cc0
                ) + 1
                gate_output.cc1 = min(
                    gate_inputs[0].cc0 + gate_inputs[1].cc0,
                    gate_inputs[0].cc1 + gate_inputs[1].cc1
                ) + 1

            elif gate.type in ['BUF', 'FANOUT']:
                gate_output.cc0 = gate_inputs[0].cc0
                gate_output.cc1 = gate_inputs[0].cc1

        # Compute observability
        for output_net in self.outputs:
            self.nets[output_net].co = 0

        for gate in reversed(self.gates):  # Back-propagate observability
            gate_inputs = [self.nets[net] for net in gate.inputs]
            gate_output = self.nets[gate.output]
            
            for input_net in gate_inputs:
                if gate.type == 'AND' or gate.type == 'NAND':
                    input_net.co = min(input_net.co, gate_output.co + sum(
                        [n.cc1 for n in gate_inputs if n != input_net]) + 1)

                elif gate.type == 'OR' or gate.type == 'NOR':
                    input_net.co = min(input_net.co, gate_output.co + sum(
                        [n.cc0 for n in gate_inputs if n != input_net]) + 1)

                elif gate.type == 'NOT':
                    input_net.co = min(input_net.co, gate_output.co + 1)

                # TODO: test this part
                elif gate.type == 'XOR' or gate.type == 'XNOR':
                    input_net.co = min(input_net.co, gate_output.co + sum(
                            [min(n.cc0, n.cc1) for n in gate_inputs if n != input_net]) + 1)
                    
                elif gate.type in ['BUF', 'FANOUT']:
                    input_net.co = min(input_net.co, gate_output.co)


        with open("SCOAP.txt", "w") as f:
            for net in self.nets:
                if net:
                    line = f"{net.name}\t({net.cc0},{net.cc1})\t{net.co}\n"
                    f.write(line)

        print("SCOAP analysis completed. Results saved to SCOAP.txt")




if __name__ == "__main__":
    # isc file name
    file_name = os.path.join(os.getcwd(), "c17.isc")
    simulator = CircuitSimulator(file_name)
    simulator.read_isc_file()
    # input file anme
    input_file = os.path.join(os.getcwd(), "input.txt")
    simulator.read_inputs(input_file)
    simulator.true_value_simulation()

    print("\nTrue Value Simulation:")
    for net in simulator.nets:
        if net:
            print(f"{net.name}: {net.value}")

    simulator.simulation_with_delay()
    print("\nSimulation with Delay:")
    for net in simulator.nets:
        if net:
            print(f"{net.name}: {net.value}")


