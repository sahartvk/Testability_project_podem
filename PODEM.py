def podem(self, fault_file="fault_file.txt", out_file="test_vector.txt"):
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
            stuck_val = 1 if "sa1" in parts[1].lower() else 0
            faults.append((fault_net, stuck_val))

    results = []
    for (fault_net, stuck_val) in faults:
        test_vec = self.run_podem_for_fault(fault_net, stuck_val)
        results.append((fault_net, stuck_val, test_vec))

    # Save test vectors
    with open(out_file, "w") as wf:
        wf.write("net fault " + " ".join(map(str, self.inputs)) + "\n")
        for (fault_net, stuck_val, tv) in results:
            fault_str = f"{fault_net} sa{stuck_val}"
            if tv is None:
                wf.write(f"{fault_str} no_test_found\n")
            else:
                tv_str = " ".join(map(str, tv))
                wf.write(f"{fault_str} {tv_str}\n")

    print(f"PODEM completed. Results saved to {out_file}.")


def run_podem_for_fault(self, fault_net, stuck_val):
    """
    Runs PODEM algorithm for a given fault and returns a test vector if found.
    """
    assignment = {inp: 'X' for inp in self.inputs}  # Initialize all inputs to 'X' (unknown)
    
    # Start recursive search
    solution_found, final_assignment = self.podem_recursive(fault_net, stuck_val, assignment)

    if solution_found:
        return [final_assignment[i] for i in self.inputs]  # Return test vector in correct order
    else:
        return None


def podem_recursive(self, fault_net, stuck_val, assignment):
    """
    Recursive PODEM algorithm with backtracking.
    """
    # Step 1: Check if the current assignment detects the fault
    detect = self.check_fault_detected(fault_net, stuck_val, assignment)
    if detect:
        return True, assignment.copy()  # Fault detected → return the test vector
    
    # Step 2: Pick an unassigned PI
    unassigned_pis = [i for i in self.inputs if assignment[i] == 'X']
    if not unassigned_pis:
        return False, None  # No inputs left to assign

    # Pick the first unassigned PI (a heuristic using SCOAP could be added here)
    next_pi = unassigned_pis[0]

    # Step 3: Try assigning next_pi = 0, then 1
    for val in [0, 1]:
        assignment[next_pi] = val
        print(f"Trying input {next_pi} = {val}")  # Debugging step
        
        # Recurse
        ok, result_asgn = self.podem_recursive(fault_net, stuck_val, assignment)
        if ok:
            return True, result_asgn  # Test vector found
        
        # Backtrack
        assignment[next_pi] = 'X'

    return False, None  # No valid test vector found


def check_fault_detected(self, fault_net, stuck_val, assignment):
    """
    Runs forward simulation to check if the fault is detected at a primary output.
    """
    # Step 1: Simulate good circuit
    pi_values = {inp: (0 if assignment[inp] == 'X' else assignment[inp]) for inp in self.inputs}
    good_output = self.forward_simulate(pi_values)

    # Step 2: Simulate faulty circuit
    faulty_output = self.forward_simulate_fault(pi_values, fault_net, stuck_val)

    # Step 3: Compare outputs → If different, fault is detected
    detected = any(go != fo for go, fo in zip(good_output, faulty_output))
    
    return detected


def forward_simulate(self, pi_values):
    """
    Simulates the circuit with given primary input assignments.
    Returns a list of primary output values.
    """
    for inp in self.inputs:
        self.nets[inp].value = pi_values[inp]

    for gate in self.gates:
        vals = [self.nets[i].value for i in gate.inputs]
        self.nets[gate.output].value = self.eval_gate(gate.type, vals)

    return [self.nets[o].value for o in self.outputs]


def forward_simulate_fault(self, pi_values, fault_net, stuck_val):
    """
    Simulates the circuit while forcing 'fault_net' to 'stuck_val'.
    Returns the primary output values.
    """
    out_vals = self.forward_simulate(pi_values)
    self.nets[fault_net].value = stuck_val  # Force the fault

    # Recompute gates that depend on fault_net
    for gate in self.gates:
        if fault_net in gate.inputs:
            vals = [self.nets[i].value for i in gate.inputs]
            self.nets[gate.output].value = self.eval_gate(gate.type, vals)

    return [self.nets[o].value for o in self.outputs]


def eval_gate(self, gate_type, input_values):
    """
    Evaluates a logic gate given its inputs.
    """
    if gate_type == 'AND':
        return int(all(input_values))
    elif gate_type == 'NAND':
        return int(not all(input_values))
    elif gate_type == 'OR':
        return int(any(input_values))
    elif gate_type == 'NOR':
        return int(not any(input_values))
    elif gate_type == 'XOR':
        return sum(input_values) % 2
    elif gate_type == 'XNOR':
        return int(not (sum(input_values) % 2))
    elif gate_type == 'NOT':
        return int(not input_values[0])
    elif gate_type in ['BUF', 'FANOUT']:
        return input_values[0]
    else:
        return 0
