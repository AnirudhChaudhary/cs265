import json
import sys

def first_pass(prog_dict):
    """
    Goes through the program and finds all the variables that are used and not used.
    """
    var_dict = {"used":set(), "unused":set()}
    for fn in prog_dict["functions"]:
        for instr in fn["instrs"]:
            if "dest" in instr.keys():
                var_dict["unused"].add(instr["dest"])
            if "args" in instr.keys():
                for arg in instr["args"]:
                    var_dict["used"].add(arg)
    
    return var_dict

def find_vars_to_remove(var_dict):
        remove_variables = []
        for var in var_dict["unused"]:
            if var not in var_dict["used"]:
                remove_variables.append(var)
        return remove_variables

def second_pass(rm_vars, orig_prog):
    """
    Second pass goes through the var_dict to find out which variables not used, and removes them from orig_prog
    """
    if rm_vars:
        for fn in orig_prog["functions"]:
            fn["instrs"] = [instr for instr in fn["instrs"] if should_keep(instr, rm_vars)]
    
    return orig_prog

def should_keep(instr, forbidden_variables):
    if "dest" in instr.keys():
        if instr["dest"] in forbidden_variables:
            return False
    return True


    
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)
    rm_vars = ["trivial"]
    while rm_vars:
        variable_dictionary = first_pass(prog)
        rm_vars = find_vars_to_remove(variable_dictionary)
        return_prog = second_pass(rm_vars, prog)
    
    json.dump(return_prog, sys.stdout, indent=2)
