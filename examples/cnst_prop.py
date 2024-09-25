import json
import sys
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

def create_blocks(prog):
    """
    Takes in a program and returns a list of blocks of instructions.
    Input: Dict - program
    Output: List[Dict] - list of blocks, with each block containing the instructions for that block
    """
    # print("prog: ", prog)
    list_of_instr = prog["functions"][0]["instrs"]
    terminator_list = ["br", "jmp", "ret"]
    
    curr_block = Block(name="main")
    block_list = {}
    # go through all instructions
    for instr in list_of_instr:
        # print("instr: ", instr)
        # some instr have operations, while others like label instr just have `label` defined
        if "label" in instr:
            # print("current block is: ", curr_block)

            ret_block = block_list[instr["label"]]
            # print("returned block is: ", ret_block)
            
            curr_block = ret_block
            # print("new block is: ", curr_block)
                    
        if "op" in instr:
            if instr["op"] in terminator_list:
                # print("seen a terminator: ", instr)
                # terminator instr is counted, but next instr is not guaranteed
                curr_block.add_instr(instr)
                if instr["op"] == "ret":
                    break
                child_list_as_blocks = curr_block.add_child_blocks(instr["labels"])
                for block in child_list_as_blocks:
                    block_list[block.name] = block      # this needs to be saved because its a reference that is tricky to deal with
                block_list[curr_block.name] = curr_block
                # print("curr_block_instr list: ", curr_block.instruction_list)
                # print("curr_block child block list: ", curr_block.children_list)
                continue
        
        # this is the default for all instructions if they are not terminator
        curr_block.add_instr(instr)

    # need to consider the current block that was made, but didn't have a terminator
    block_list[curr_block.name] = curr_block
    return block_list

class Block():
    def __init__(self, name="", input_table = [], instruction_list = [], children_list=[], output_table={}):
        self.name = name                                # each block has to have a name, just please don't have multiple labels with the same name
        self.input_table = input_table
        self.instruction_list = instruction_list
        self.children_list = children_list
        self.output_table = output_table
    
    def add_instr(self, instr):
        self.instruction_list.append(instr)
    
    def add_child_blocks(self, label_list):
        # print("adding child blocks")
        # print("label list: ", label_list)
        for label in label_list:
            self.children_list.append(Block(name=label, input_table=[], instruction_list=[], children_list=[], output_table= {}))
        
        # print("self.children_list: ", self.children_list)
        return self.children_list
    
    def __repr__(self):
        return f""" Block with name: {self.name} and children: {[block.name for block in self.children_list]}"""
    
    def ret_block_with_label(self,label):
        """
        Returns the block with name that equals `label`.
        """
        for child_block in self.children_list:
            if child_block.name == label:
                return child_block
        print("could not find child block")
        return None

    
def const_prop(instruction_list, starting_table):
    """
    Local value numbering pass through the program.
    DESIGN CHOICE: ONE PASS OR TWO PASS: If you go in one pass, you keep checking backwards to see what value it takes on.
    If you do in two pass, your first pass just dumbly goes through adding values and the second pass will be in charge of propagating the values
    """
    # print("instruction_list: ", instruction_list)
    # print("starting table: ", starting_table)
    table = starting_table
    new_instruction_list = []
    for instr in instruction_list:
        # if the instruction is a constant, add it to the table, overriding if it was already in the table
        # print("looking at instruction: ", instr)
        if "op" in instr:         #{'dest': 'x', 'op': 'const', 'type': 'int', 'value': 4}
            if instr["op"] == "const":
                var_name = instr["dest"]
                table[var_name] = instr
                new_instruction_list.append(instr)
            elif instr["op"] == "id":
                var_to_pull_from = instr["args"][0]     # this is the variable that we want to pull from
                if var_to_pull_from in table:
                    var_to_pull_from_instr = table[var_to_pull_from]   # this is the stored instruction
                    new_instr = var_to_pull_from_instr.copy()       # we want a copy of the stored instruction          
                    new_instr["dest"] = instr["dest"]      # change the destination to be the current                  
                    table[new_instr["dest"]] = new_instr            # update the table
                    new_instruction_list.append(new_instr) #add to list of instructions

                else:
                    new_instruction_list.append(instr)  # if the var is not in the table, we can't necessarily do propagation, but this is still a valid program

            else:
                new_instruction_list.append(instr)
        
        else:
            new_instruction_list.append(instr)
            
        # print("instr: ", instr)

        # if the instruction has an id, then find the variable with the value and pull it
        
    # print("end table: ", table)
    return new_instruction_list, table

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
    # print("consolidating input table: ", len(input_table_list))
    all_unique_dicts = []
    for assignment_dict in input_table_list:
        # print("assignment dict: ", assignment_dict)
        
        for var in assignment_dict:
            # print("looking at var: ", var)
            if len(all_unique_dicts) == 0:            # if no added, trivially add the first one
                first_dict = assignment_dict[list(assignment_dict.keys())[0]]
                all_unique_dicts.append(first_dict)
                # print("saw no unique dicts so added one: ", all_unique_dicts)
                continue
            # print("var_dict: ", var)
            var_value = assignment_dict[var]
            var_in_list = False
            for dict in all_unique_dicts:
                if dict["dest"] == var:
                    var_in_list = True
                    break

            if var_in_list:
                if var_consistency(var_value, all_unique_dicts):
                    continue
                else:
                    # remove var from all_unique_dicts
                    for dict in all_unique_dicts:
                        if var == dict["dest"]:
                            all_unique_dicts.remove(dict)
            else:
                all_unique_dicts.append(var_value)

    if len(all_unique_dicts) == 0:
        all_unique_dicts.append({})

    all_unique_dicts = [{instr["dest"]: instr} for instr in all_unique_dicts]
    return all_unique_dicts

# print(consolidate_input_tables([{'a': {'dest': 'a', 'op': 'const', 'type': 'int', 'value': 2}, 'b': {'dest': 'b', 'op': 'const', 'type': 'int', 'value': 1}, 'c': {'dest': 'c', 'op': 'const', 'type': 'int', 'value': 5}}, {'a': {'dest': 'a', 'op': 'const', 'type': 'int', 'value': 2}, 'b': {'dest': 'b', 'op': 'const', 'type': 'int', 'value': 1}, 'c': {'dest': 'c', 'op': 'const', 'type': 'int', 'value': 10}}]))
def const_prop_on_blocks(starting_block_name, block_dict):

    queue = [starting_block_name]
    visited = []
    while queue:
        # print("starting const prop on block: ", starting_block_name)
        # print("queue: ", queue)
        block_name = queue.pop(0)
        if block_name in visited:
            continue
        visited.append(block_name)
        init_block = block_dict[block_name]         # we always start with the main block
        # if len(init_block.children_list) == 0 and len(queue) != 0:   #heuristic for determining that we have reached the end block
        #     continue
        # print("looking at block: ", init_block.name)
        # print(f"{init_block.name} is given: ", init_block.input_table)
        
        # in the case there were multiple parents, need to consolidate into one
        if len(init_block.input_table) == 0:
            init_block.input_table = [{}]
        elif len(init_block.input_table) > 1:
            init_block.input_table = consolidate_input_tables(init_block.input_table)
        
        # perform constant prop
        init_block.instruction_list, init_block.output_table = const_prop(init_block.instruction_list, init_block.input_table[0])
        # print(f"after const prop: {init_block.name} gives: ", init_block.output_table)


        # final_list = []
        for child_block in init_block.children_list:
            # print("child block has name: ", child_block.name)
            queue.append(child_block.name)      # need to append this to the list of blocks to visit
            child_block = block_dict[child_block.name]      # get the block info from centralized source
            # print("child block input before: ", child_block.input_table)
            child_block.input_table.append(init_block.output_table.copy())     # add our output to our child's to consider
            block_dict[child_block.name] = child_block
            # print("child block input after: ", child_block.input_table)
            # print("\n")
            # final_list.append(const_prop_on_blocks(child_block.name, block_dict))
        # init_block.children_list = final_list
    # print("finished going through all of the queue")
    return visited
############################################
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)
    # print("init program: ", prog)
    
    block_dict = create_blocks(prog)
    # print("block_dict: ", block_dict)
    # return_prog = const_prop(prog)
    block_ordering = const_prop_on_blocks("main", block_dict)
    # print("")
    # return_prog = const_prop(prog, {})
    # print(return_prog)
    # print("return_prog: ", return_prog)
    instruction_list = []
    while block_ordering:
        visited_block = block_ordering.pop(0)
        instruction_list.extend(block_dict[visited_block].instruction_list)
    
    # print("final instruction list: ", instruction_list)
    return_prog = {
        "functions": [
            {
                "instrs": instruction_list,
                "name" : "main"
            }
        ],
        
    }
    # TODO: DOES LIVENESS program need to take into consideration the boolean values for the conditions?
    json.dump(return_prog, sys.stdout, indent=2)