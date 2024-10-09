import json
import sys
import copy
"""
Constant Propagation for Task 2

Design Choices:
- Linear Code
- Branching code
    - One branch
    - Multiple sequential branches 

Approach:
- Start off with an empty list because we don't have any values defined
1. Start off with basic constant 
"""
def print_block_dict(block_dict):
    for key in block_dict:
        print(key)
        print(block_dict[key].instruction_list)

def create_blocks(instr_list, start_name):
    """
    Takes in a program and returns a list of blocks of instructions.
    Input: Dict - program
    Output: List[Dict] - list of blocks, with each block containing the instructions for that block
    """
    # print("prog: ", prog)
    # list_of_instr = prog["functions"][0]["instrs"]
    list_of_instr = instr_list
    terminator_list = ["br", "jmp", "ret"]
    hit_terminator = False
    terminator = None
    curr_block = Block(name=start_name)
    block_list = {}
    # go through all instructions
    for instr in list_of_instr:
        # some instr have operations, while others like label instr just have `label` defined
        if "label" in instr:
            # print("found label: ", instr["label"])
            block_list[curr_block.name] = curr_block
            if instr["label"] in block_list:
                ret_block = block_list[instr["label"]]      # pull this new block from the list

                if terminator != "jmp" and terminator != "br":
                    # print("added children / parents")
                    curr_block.children_list.add(ret_block)
                    ret_block.parent_list.add(curr_block)  

                curr_block = copy.deepcopy(ret_block)
            else:
                # we haven't seen this label before
                new_block_obj = Block(name=instr["label"])                        # create a new block object
                if terminator != "jmp" and terminator != "br":
                    block_list[curr_block.name].children_list.add(new_block_obj) # add this new label as a child of the block we were working on
                    new_block_obj.parent_list.add(block_list[curr_block.name])
                block_list[new_block_obj.name] = new_block_obj                  # need to add the new block to our block dict
                curr_block = new_block_obj                                      # need to change our current to be the new block
            terminator = None
            hit_terminator = False
        if "op" in instr:
            if instr["op"] in terminator_list:
                # print("seen a terminator: ", instr)
                hit_terminator = True
                terminator = instr["op"]
                # terminator instr is counted, but next instr is not guaranteed
                curr_block.instruction_list.append(copy.deepcopy(instr))
                if instr["op"] == "ret":    # ret doesn't always mean the end of the instr, so we just end this block and keep going
                    block_list[curr_block.name] = curr_block
                    continue

                for label in instr["labels"]:
                    if label in block_list:
                        curr_block.children_list.add(block_list[label])
                        block_list[label].parent_list.add(curr_block)
                    else:
                        new_block_obj = Block(name=label)
                        
                        curr_block.children_list.add(new_block_obj)
                        new_block_obj.parent_list.add(curr_block)
                        block_list[label] = new_block_obj

                block_list[curr_block.name] = curr_block

                continue
        
        # this is the default for all instructions if they are not terminator
        curr_block.instruction_list.append(copy.deepcopy(instr))
        # print("after adding instructions: ", curr_block.instruction_list)

    
    # if curr block is None, that means that it had a terminator
    if curr_block is not None:
        # need to consider the current block that was made, but didn't have a terminator
        block_list[curr_block.name] = curr_block

    # print("--------at the end of block creation--------")
    # print_block_dict(block_list)
    return block_list

class Block():
    def __init__(self, name="", input_table=None, instruction_list=None, children_list=None, output_table=None, parent_list=None):
        self.name = name
        self.input_table = input_table if input_table is not None else []
        self.instruction_list = instruction_list if instruction_list is not None else []
        self.parent_list = parent_list if parent_list is not None else set()
        self.children_list = children_list if children_list is not None else set()
        self.output_table = output_table if output_table is not None else {}
        self.visited = False
        self.use_ = set()
        self.def_ = set()
        self.in_ = []
        self.out_ = []

    def add_instr(self, instr):
        self.instruction_list.append(copy.deepcopy(instr))
    # NEED WHILE LOOP TO ITERATE TO FIXED POINT
    def add_child_blocks(self, label_list, block_dict):
        """
        For label in label list, 
        # label list should only be creating blocks that are not created already
        """
        for label in label_list:
            # Create and append a new Block for each label
            if label not in block_dict:
                self.children_list.append(Block(name=label, parent_list=[self.name]))  #??
            else:
                # block_dict[label].parent_list.append(self.name) # since this block is now a child to the block called this fn, we have to add parents accordingly
                self.children_list.append(block_dict[label])
        
        return self.children_list
    
    def __repr__(self):
        # return f""" Block with name: {self.name} \n children: {[block.name for block in self.children_list]} \n parents {[block for block in self.parent_list]}"""
        # return f"""Block: {self.name} | Children : {[block.name for block in self.children_list]}"""
        return f"""Block: {self.name}"""
        return f"""Block: {self.name} | Input : {self.input_table}"""
    
    def ret_block_with_label(self,label):
        """
        Returns the block with name that equals `label`.
        """
        for child_block in self.children_list:
            if child_block.name == label:
                return child_block
        print("could not find child block")
        return None

def const_prop_transfer(instruction_list, starting_table):
    """
    The person calling me should handle any sort of meeting of variables that needs to be done.
    For a given block, we will perform constant propagation. We don't change any of instructions, just the final table
    """
    final_table = copy.deepcopy(starting_table) # our final table should start with the values in the starting table
    arith_ops = ["add", "sub", "mul", "div"]
    # print("final table: ", final_table)
    for instr in instruction_list:
        if type(final_table) == list:
            # print("instr: ", instr)
            # print("final table turned into a list!!")
            final_table = final_table[0]
        # if the instruction is a constant, add it to the table, overriding if it was already in the table
        if "op" in instr:         #{'dest': 'x', 'op': 'const', 'type': 'int', 'value': 4}
            if instr["op"] == "const":
                var_name = instr["dest"]        # pick out the var name from the instruction
                final_table[var_name] = instr["value"]         # assign the value of var from instr
            elif instr["op"] == "id":
                var_to_pull_from = instr["args"][0]                          # this is the variable that we want to pull from
                if var_to_pull_from in final_table:
                    stored_var_val = final_table[var_to_pull_from]   # this is the stored instruction
                    final_table[instr["dest"]] = stored_var_val               # update the table
                
                # else should be handled by the dead code elimination pass. The variable isn't in the table so when it is referenced, it is dead code

            elif instr["op"] in arith_ops:
                arg_0_name = instr["args"][0]
                arg_1_name = instr["args"][1]

                # need to get the value of arg 0, which can either be in the final_table or the starting table
                # we want to start from the final_table because that will have the most recent value
                if arg_0_name not in final_table:      # if there is a use for a term that hasn't been defined in the scope of this block, then we just ignore it and let it go on
                    continue
                else:
                    arg_0_val = final_table[arg_0_name]
                
                if arg_1_name not in final_table:
                    continue
                else:
                    arg_1_val = final_table[arg_1_name]

                match instr["op"]:
                    case "add":
                        final_table[instr["dest"]] = arg_0_val + arg_1_val
                    case "sub":
                        final_table[instr["dest"]] = arg_0_val - arg_1_val
                    case "mul":
                        final_table[instr["dest"]] = arg_0_val * arg_1_val
                    case "div":
                        final_table[instr["dest"]] = arg_0_val // arg_1_val
        
        # if type(final_table) == list:
            # print("instr: ", instr)
            # print("final table turned into a list during this instruction!!")
        # print("final table end loop: ", final_table)
    return final_table

# TODO: MAKE SURE THAT WE CHECK IF THE NUMBER OF RECEIVED IS EQUAL TO THe PARENTS WE HAVE 
# TODO: We only actually change the instructions once we know that the intro tables have stabilized - Fixed point should handle this
def const_prop(instruction_list, starting_table):
    """
    Local value numbering pass through the program.
    DESIGN CHOICE: ONE PASS OR TWO PASS: If you go in one pass, you keep checking backwards to see what value it takes on.
    If you do in two pass, your first pass just dumbly goes through adding values and the second pass will be in charge of propagating the values
    """
    new_instruction_list = []
    table_for_block = copy.deepcopy(starting_table)
    arith_ops = ["add", "sub", "mul", "div"]
    for instr in instruction_list:
        # if the instruction is a constant, add it to the table, overriding if it was already in the table
        # print(instr)
        if type(table_for_block) == list:
            # print("instr: ", instr)
            # print("final table turned into a list!!")
            table_for_block = table_for_block[0]
        if "op" in instr:         #{'dest': 'x', 'op': 'const', 'type': 'int', 'value': 4}
            if instr["op"] == "const":
                var_name = instr["dest"]        # pick out the var name from the instruction
                table_for_block[var_name] = instr["value"]         # assign the value of var from instr
            if instr["op"] == "id":                 #{'args': ['i'], 'dest': 'v8', 'op': 'id', 'type': 'int'}
                var_to_pull_from = instr["args"][0]     # this is the variable that we want to pull from
                if var_to_pull_from in table_for_block and table_for_block[var_to_pull_from] != {}:     # can only pull if there is something to pull from
                    new_instr = {'dest': instr["dest"], 'op': 'const', 'type': instr["type"], 'value': table_for_block[var_to_pull_from]}
                    table_for_block[instr["dest"]] = table_for_block[var_to_pull_from]    # still need to update the table in the current iteration but it won't persist past
                    new_instruction_list.append(new_instr) #add to list of instructions
                else:
                    table_for_block[instr["dest"]] = {}     # although we could not get a value, this var changed so it could affect things later
                    new_instruction_list.append(instr)  # if the var is not in the table, we can't necessarily do propagation, but this is still a valid program


            elif instr["op"] in arith_ops:
                arg_0_name = instr["args"][0]
                arg_1_name = instr["args"][1]
                if (arg_0_name not in table_for_block or arg_1_name not in table_for_block):      # if there is a use for a term that hasn't been defined in the scope of this block, then we just ignore it and let it go on
                    table_for_block[instr["dest"]] = {}     # although we could not get a value, this var changed so it could affect things later
                    new_instruction_list.append(instr)
                    continue
                if (table_for_block[arg_0_name] == {} or table_for_block[arg_1_name] == {}):
                    table_for_block[instr["dest"]] = {}     # although we could not get a value, this var changed so it could affect things later
                    new_instruction_list.append(instr)
                    continue
                arg_0_val = table_for_block[arg_0_name]
                arg_1_val = table_for_block[arg_1_name]
                match instr["op"]:
                    case "add":
                        new_instr = {"dest": instr["dest"], "op": "const", "type":instr["type"], "value":arg_0_val+arg_1_val}
                    case "sub":
                        new_instr = {"dest": instr["dest"], "op": "const", "type":instr["type"], "value":arg_0_val-arg_1_val}
                    case "mul":
                        new_instr = {"dest": instr["dest"], "op": "const", "type":instr["type"], "value":arg_0_val*arg_1_val}
                    case "div":
                        new_instr = {"dest": instr["dest"], "op": "const", "type":instr["type"], "value":arg_0_val//arg_1_val}

                table_for_block[new_instr["dest"]] = new_instr["value"]
                new_instruction_list.append(new_instr)
                    
            else:
                new_instruction_list.append(instr)
        
        else:
            new_instruction_list.append(instr)
            
        # print("instr: ", instr)

        # if the instruction has an id, then find the variable with the value and pull it
        
    return new_instruction_list, table_for_block

def var_consistency(var_dict, all_unique_dicts):
    """
    We want to check consistency of variables with the existing dictionaries that we've seen. This is 
    because we don't want to propagate constants that don't have a fixed value by that point in execution.
    """
    # print("var dict: ", var_dict)
    # print("all unique dicts: ", all_unique_dicts)
    var_dict_value = var_dict["value"]
    var_dict_name = var_dict["dest"]
    for dict in all_unique_dicts:
        dict_value = dict["value"]
        dict_name = dict["dest"]


        if var_dict_name == dict_name:
            if dict_value == var_dict_value:
                # print("consistency")
                return True
            else:
                return False
    return True

def consolidate_input_tables(input_table_list):
    """
    We want to consolidate all of the value tables that we receive from our predecessors. As such, if theres a value defined in one table, it should only be added to the final list if it's in all of the input tables.
    {'a': {'dest': 'a', 'op': 'const', 'type': 'int', 'value': 2}
    """

    all_unique_dicts = {}
    # we can only meet at max on the assignment_dict with the least number of items, they all can't agree on more than the min, bc the min doesn't have more 
    largest_dict_len = 0
    largest_dict = None
    for assignment_dict in input_table_list:
        if len(assignment_dict) > largest_dict_len:
            largest_dict_len = len(assignment_dict)
            largest_dict = assignment_dict
    
    if not largest_dict:
        return [{}]
    for var in largest_dict:   # go through the largest assignment
        var_val = largest_dict[var]         # this is the starting value, if all dicts agree, then we can safely add this one
        add = True                          # assume that we can start by adding it and find a case where can't add it
        for assignment_dict in input_table_list:    # go through and find out if that assignment is in every dict
            if var in assignment_dict:
                if assignment_dict[var] != var_val:
                    add = False
                    break
            # no else: if its not in another block, then that means it wasn't defined there so we don't have to worry about it

        if not add:
            all_unique_dicts[var] = {}
        else:
            all_unique_dicts[var] = var_val

    if len(all_unique_dicts) == 0:
        return [{}]
    return [all_unique_dicts]

def fixed_point_analysis(dict_of_blocks, starting_block):
    """
    We need to go through all of the blocks, starting from the main block.
    1. Go through the block's instructions and update your table
    2. Pass your table to children and add them to the queue.
    3. Pop the next item of the queue and keep going.

    IMPORTANT: THIS FUNCTION SHOULD NOT BE CHANGING ANY OF THE INSTRUCTIONS
    """
    # initialize worklist
    # print("starting fixed point analysis")
    fixed_point = False
    while not fixed_point:
        worklist = [starting_block]
        visited = []
        fixed_point = True
        while worklist:
            # print("worklist: ", worklist)
            block_name = worklist.pop(0) # gets the most recent worklist item ( order doesn't matter)
            if block_name in visited:
                continue
            visited.append(block_name)
            # print("working on: ", block_name)

            block_obj = dict_of_blocks[block_name]
            block_obj.visited = True
            # starting_block_table = dict_of_blocks[block_name].input_table.copy()

            if len(block_obj.input_table) == 0:
                block_obj.input_table = {}
            elif len(block_obj.input_table) > 1:
                block_obj.input_table = consolidate_input_tables(block_obj.input_table).copy()

            
            # transfer function
            old_output_table = copy.deepcopy(block_obj.output_table)
            instr_list, block_obj.output_table = const_prop(copy.deepcopy(block_obj.instruction_list), copy.deepcopy(block_obj.input_table.copy()))

            if block_obj.output_table != old_output_table:
                fixed_point = False  # Set flag to False if any block's output changed
            # print("output: ", output_table)
            # print("\n")
            # if not blockChanged(block_obj.input_table, output_table):
            #     early_break = True
            #     for cb in block_obj.children_list:
            #         if not cb.visited:      # if there is a child that hasn't been visited then it doesn't matter, i have to go to the next one
            #             early_break = False

            #     if early_break:
            #         continue

            # since we updated the parent, this information could carry over to the next case
            # print("block object children: ", block_obj.children_list)
            for child_block in block_obj.children_list:

                worklist.append(child_block.name)      # need to append this to the list of blocks to visit
                child_block = dict_of_blocks[child_block.name]      # get the block info from centralized source

                if type(child_block.input_table) == dict:
                    child_block.input_table = [child_block.input_table]
                child_block.input_table.append(block_obj.output_table.copy())     # add our output to our child's to consider
                dict_of_blocks[child_block.name] = child_block  # update the block dict with the new block obj information

            # print(child_block)
    # print("finished fix point analysis")
    
    # for key in dict_of_blocks:
    #     print(dict_of_blocks[key])
    return dict_of_blocks

def blockChanged(input_dict, output_dict):
    """
    Return whether or not two dicts are the same, but in the context of a blocks input and output dict.
    """
    if type(input_dict) == list:
        input_dict = input_dict[0]
    if type(output_dict) == list:
        output_dict = output_dict[0]
    # different number of keys auto means the block has changed
    if len(input_dict.keys()) != len(output_dict.keys()):
        return True
    else:
        for key in input_dict.keys():
            # if a var not in one dict, that means that the block changed
            if key not in output_dict:
                return True
            # if the values are not the same then the block also changed
            if input_dict[key] != output_dict[key]:
                return True
    
    return False

# print(consolidate_input_tables([{'a': 3, 'b': 4, 'c':5, 'd':{}}, {'a': 2, 'b': 1, 'c': 10, 'd':5, 'e':6}]))
def const_prop_on_blocks(starting_block_name, this_func_block_dict):
    #TODO: Can't do constant prop on a block unless we know it has received all information from it's parents
    queue = [starting_block_name]
    visited = []
    while queue:
        # print("starting const prop on block: ", starting_block_name)
        # print("queue: ", queue)
        block_name = queue.pop(0)
        if block_name in visited:
            continue
        visited.append(block_name)
        init_block = this_func_block_dict[block_name]         # we always start with the main block
        # if len(init_block.children_list) == 0 and len(queue) != 0:   #heuristic for determining that we have reached the end block
        #     continue
        
        # in the case there were multiple parents, need to consolidate into one
        if len(init_block.input_table) == 0:
            init_block.input_table = [{}]
        elif len(init_block.input_table) > 1:
            init_block.input_table = consolidate_input_tables(init_block.input_table).copy()
        

        # perform constant prop
        init_block.instruction_list, output_table = const_prop(init_block.instruction_list, init_block.input_table[0])


        for child_block in init_block.children_list:

            queue.append(child_block.name)      # need to append this to the list of blocks to visit
            child_block = this_func_block_dict[child_block.name]      # get the block info from centralized source

            child_block.input_table.append(init_block.output_table.copy())     # add our output to our child's to consider
            this_func_block_dict[child_block.name] = child_block

    return visited

def get_block_use_def(block_obj):
    use_list = set()
    terminator_list = ["jmp"]
    for instr in block_obj.instruction_list:
        if "op" in instr:
            if instr["op"] in terminator_list:
                continue
        if "args" in instr:
            for arg in instr["args"]:
                use_list.add(arg)
    
    return use_list
def add_use_defs(start_block_name, block_dict_):
    """
    Does the liveness analysis for the block dict.
    """
    # USE & DEF
    queue = [start_block_name]
    visited = []
    while queue:
        curr_block_name = queue.pop(0)
        if curr_block_name in visited:
            continue
        visited.append(curr_block_name)
        current_block_obj = block_dict_[curr_block_name]
        # print("computing use/def for: ", curr_block_name)
        current_block_obj.use_ = get_block_use_def(copy.deepcopy(current_block_obj))

        for parent_block_obj in current_block_obj.parent_list:
            queue.append(parent_block_obj.name)

    return block_dict_

def liveness_transfer_analysis(block_obj, out_set):
    """
    Go backwards through the block obj.
    If a variable is used, add it to the live set. If a variable is defined remove it from the live set.
    Perform defs before uses
    """
    # print("looking at block: ", block_obj.name)
    live_var = out_set
    instruction_list = copy.deepcopy(block_obj.instruction_list)
    i = len(instruction_list) - 1
    while i != -1:
        instr = instruction_list[i]
        # print("instr: ", instr)
        # having a definition means that we don't need that variable to be live
        if "dest" in instr:
            if instr["dest"] in live_var:
                live_var.remove(instr["dest"])
        
        # use that variable means that it has to be live above it
        if "op" in instr:
            if "args" in instr:
                for arg in instr["args"]:
                    live_var.add(arg)
        
        i -=1 
    
    return live_var



def liveness_analysis(starting_block_name, block_dict):
    """
    1. start at the end block.
    2. out[B] = ∪ in[S]
    3. in[B] = use[B] ∪ (out[B] - def[B])
    4. iterate through the algorithm again until fixed point is hit
    """
    fixed_point = False
    while not fixed_point:
        queue = [starting_block_name]
        visited = []
        fixed_point = True
        while queue:
            curr_block_name = queue.pop(0)
            # print("working on: ", curr_block_name)
            if curr_block_name in visited:
                continue
            visited.append(curr_block_name)
            curr_block_obj = copy.deepcopy(block_dict[curr_block_name])
            # take a snapshot of the obj before
            out_copy = copy.deepcopy(curr_block_obj.out_)
            in_copy = copy.deepcopy(curr_block_obj.in_)
            
            # print("BEFORE")
            # print("curr block name: ", curr_block_name)
            # print("use_: ", curr_block_obj.use_)
            # print("def_: ", curr_block_obj.def_)
            # print("out_: ", curr_block_obj.out_)
            # print("in_: ", curr_block_obj.in_)
            # if curr_block_name == "next.ret":
            #     print("looking at next.ret")
            #     print("out_: ", curr_block_obj.out_)
            #     print("in_: ", curr_block_obj.in_)
            live_out = set().union(*[block_dict[block.name].in_ for block in curr_block_obj.children_list])
            live_in = liveness_transfer_analysis(curr_block_obj, copy.deepcopy(live_out))

            # out[B] = u in[S]
            # print("curr_block children: ", curr_block_obj.children_list)
            # print("in for children: ", [block_dict[block.name].in_ for block in curr_block_obj.children_list])
            # new_out = set().union(*[block_dict[block.name].in_ for block in curr_block_obj.children_list])
            # # print("new out: ", new_out)
            # # in[B] = use[B] ∪ (out[B] - def[B])
            # diff_ = new_out.difference(curr_block_obj.def_)
            # new_in = curr_block_obj.use_.union(diff_)
            # print("new out: ", new_in)

            curr_block_obj.out_ = live_out
            curr_block_obj.in_ = live_in

            # print("AFTER")
            # print("curr block name: ", curr_block_name)
            # print("use_: ", curr_block_obj.use_)
            # print("def_: ", curr_block_obj.def_)
            # print("out_: ", curr_block_obj.out_)
            # print("in_: ", curr_block_obj.in_)
            # print("----------------------------------")
            block_dict[curr_block_name] = curr_block_obj
            if live_out != out_copy or live_in != in_copy:
                fixed_point = False
            
            for parent in curr_block_obj.parent_list:
                queue.append(parent.name)
            
    return block_dict

def dead_code_elimination(block_dict):
    for block in block_dict:
        final_instr_list = []
        block_obj = block_dict[block]
        # print(block_obj.out_)
        for instr in block_obj.instruction_list:
            # print(instr)
            if "dest" in instr:
                if instr["dest"] not in block_obj.out_ and instr["dest"] not in block_obj.use_:
                    continue
            final_instr_list.append(instr)
        
        block_obj.instruction_list = final_instr_list
    return
############################################
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)
    # print("init program: ", prog)
    # total_args = 0
    # for func in prog["functions"]:
    #     instruction_list = func["instrs"]
    #     for instr in instruction_list:
    #         if "args" in instr:
    #             total_args += len(instr["args"])

    
    # json.dump(total_args, sys.stdout, indent=2)

    for func in prog["functions"]:
        instruction_list = []
        instruction_list = func["instrs"]

        block_order = []
        for instr in instruction_list:
            if "label" in instr:
                block_order.append(instr["label"])
        block_order = [func["name"]] + block_order

        # print("instruction_list: ", instruction_list)
        block_dict = create_blocks(instruction_list, start_name=func["name"]).copy()

        # for block in block_dict:
        #     print("name: ", block_dict[block].name)
        #     print("parents: ", block_dict[block].parent_list)
        #     print("parent set: ", set(block_dict[block].parent_list))
        #     print("children: ", block_dict[block].children_list)
        #     print("children set: ", set(block_dict[block].children_list))

        block_dict_copy = copy.deepcopy(block_dict)

        new_block_dict = fixed_point_analysis(block_dict_copy, func["name"])

        # ATP: new block dict contains the fixed point of all of the blocks so we can safely propagate constants now

        block_ordering = const_prop_on_blocks(func["name"], new_block_dict)

        # NEED TO DO LIVENESS ANALYSIS
        # print("start LA")
        block_dict_post_liveness = add_use_defs(block_order[-1], new_block_dict)
        # for block in block_dict_post_liveness:
        #     print("block name: ", block_dict_post_liveness[block].name)
        #     print("block use: ", block_dict_post_liveness[block].use_)
        #     print("block def: ", block_dict_post_liveness[block].def_)

        new_block_dict = liveness_analysis(block_order[-1], block_dict_post_liveness)
        # print("--------- AFTER LIVENESS IS COMPLETE ---------")
        # for block in new_block_dict:
            # print("---------------------------------------------")
            # print("block name: ", new_block_dict[block].name)
            # print("block in: ", new_block_dict[block].in_)
            # print("block out: ", new_block_dict[block].out_)
            
        dead_code_elimination(new_block_dict)

        # print("end LA")
        instruction_list = []
        seen_blocks = []
        # remove duplicates
        while block_order:
            visited_block = block_order.pop(0)

            if visited_block not in seen_blocks:
                seen_blocks.append(visited_block)
                instruction_list = instruction_list + copy.deepcopy(new_block_dict[visited_block].instruction_list)
        func["instrs"] = instruction_list.copy()
    
    # total_args = 0
    # for func in prog["functions"]:
    #     instruction_list = func["instrs"]
    #     for instr in instruction_list:
    #         if "args" in instr:
    #             total_args += len(instr["args"])

    
    # json.dump(total_args, sys.stdout, indent=2)

    # json.dump(3, sys.stdout, indent=2)
    json.dump(prog, sys.stdout, indent=2)