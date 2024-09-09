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

def create_blocks(prog):
    """
    Takes in a program and returns a list of blocks of instructions.
    Input: Dict - program
    Output: List[Dict] - list of blocks, with each block containing the instructions for that block
    """
    # print("prog: ", prog)
    list_of_instr = prog["functions"][0]["instrs"]
    terminator_list = ["br", "jmp", "ret"]
    
    block_list = []
    curr_block = []
    # go through all instructions
    for instr in list_of_instr:
        # some instr have operations, while others like label instr just have `label` defined
        if "op" in instr:
            if instr["op"] in terminator_list:
                # terminator instr is counted, but next instr is not guaranteed
                curr_block.append(instr)
                # curr block is finished so we need to move to next instr
                block_list.append(curr_block)
                # reset curr block for new blocks
                curr_block = []
                continue
        
        # this is the default for all instructions if they are not terminator
        curr_block.append(instr)

    # need to consider the current block that was made, but didn't have a terminator
    block_list.append(curr_block)
    return block_list

def local_dce(block):
    """
    Performs local dead code elimination on a single block.

    TODO: Think about what the loop iterations should all look like together, first global and then local? or finish all global and then go local or...?
    """
    unused = {} # keeps track of the variable declarations
    """
    Problem: ordering of instructions afterwards
    tuple of var : (instr num, instr) and then at the end, go through and just list the instr ascending order
    """
    for instr in block:
        # if a var shows up as an arg, that means that it was used so we take it out of unused
        # print("instr: ", instr)
        if "args" in instr:
            for arg in instr['args']:
                if arg in unused:   # when var is used as an arg, but 
                    del unused[arg]
        
        # if the instr has a destination and if we haven't used it, then that means that we are
        # overriding the previous entry, so we should delete the old instruction that was there
        if "dest" in instr:
            if instr["dest"] in unused:
                # if we reach here, that means that we are creating a new assignment of a variable alr assigned before
                remove_instruction = unused[instr["dest"]]

                block.remove(remove_instruction)
            unused[instr["dest"]] = instr
        
        # if there is no destination, then currently we have no way of handling it and we just
        # let it be for now
    
    return block


    
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)
    # print("prog: ", prog)
    rm_vars = ["trivial"] # make non-empty to go through first pass
    while rm_vars:
        # we get our variable dictionary after the first pass
        variable_dictionary = first_pass(prog)
        # find out which variables we can remove
        rm_vars = find_vars_to_remove(variable_dictionary)
        # return the program once we have removed those variables
        return_prog = second_pass(rm_vars, prog)

    blocked_instructions = create_blocks(return_prog)
    
    final_instr_list = []
    for block in blocked_instructions:
        # print("block before")
        # print(block)
        local_filtered_instr = local_dce(block)
        # print("block after")
        # print(local_filtered_instr)
        final_instr_list += local_filtered_instr
    
    return_prog = {
        "functions": [
            {
                "instrs": final_instr_list,
                "name" : "main"
            }
        ],
        
    }
        
    
    json.dump(return_prog, sys.stdout, indent=2)
