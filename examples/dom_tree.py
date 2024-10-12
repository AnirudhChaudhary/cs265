"""
Dominance Tree code
"""
import copy
import json
import sys
from is_ssa import is_ssa
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
        self.dom = {self.name}   # all the blocks that dominate this block; trivially a block is dominated by itself
        self.dominated_by = set() # extended, this is all of the blocks above that dominate this block

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
                if terminator != "jmp" and terminator != "br":                  # we only want to automatically add the next block as a child/parent pairing if there is no jump or branch instruction because those jumps could cause a change in control flow
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
    
def fixed_point_analysis(dict_of_blocks, starting_block):
    """
    Computes the dominance relation between all of the blocks in the CFG
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

            fixed_point = fixed_point and dominance_transfer_analysis(dict_of_blocks, block_name)      # if any of fixed points come back as false, this will always evaluate to false and we have to go through again

            # print("block name: ", block_name)
            for parent in dict_of_blocks[block_name].parent_list:
                worklist.append(parent.name)

    return dict_of_blocks

def dominance_transfer_analysis(b_dict, b_name):
    """
    This is the dominance transfer analysis, that simply does the domainance transfer function.

    dom(b) = {b} U (intersection of all doms of parents)
    Input: 
    - b_dict: dictionary of block names : block objects
    - b_name: name of the block we are currently operating on

    Output:
    - None: Should change the block object in the dictionary
    """

    block_obj = b_dict[b_name]
    orig_len = len(block_obj.dom)
    parent_list = block_obj.parent_list     # contains all of the objects for the parent blocks
    parent_block_doms = [p_block.dom for p_block in parent_list]
    # print("parent block doms: ", parent_block_doms)
    if parent_block_doms:
        pred_dom = set.intersection(*parent_block_doms)
    else:
        pred_dom = {}
    block_obj.dom = block_obj.dom.union(pred_dom)

    # may need to assert that the changed blocks are persisted
    b_dict[b_name] = block_obj
    return orig_len == len(block_obj.dom)

def create_dom_front(b_dict):
    """
    Finds and populates dominance frontier for all blocks in the block dictionary.

    Input: b_dict: dict of {block_name:block_obj}
    Output: df: map of block name to blocks on the frontier
    """
    df = {}
    for b in b_dict:
        df[b] = []
        # this loops through all of the blocks to find the dominance frontier
        # i is a prospective frontier block
        for i in b_dict:
            # a prospect cannot be dominated by the parent
            if b in block_dict[i].dom:
                continue
            
            # go through i's parent list and we should check that prospect's parents are dominated by the original
            for predecessor in b_dict[i].parent_list:
                if b in predecessor.dom:
                    df[b].append(i)
    return df

def find_imm_domin(b_dict, top_level):
    """
    Creates the dom tree for each block. It creates the tree of immediately dominating blocks.
    Input: b_dict - Dict[str, Block()]
    Output: Dict[str, List[str]]
    """
    cfg = list(b_dict.keys())
    for block in cfg:
        if block == top_level:
            b_dict[block].dominated_by = {top_level}
        else:
            b_dict[block].dominated_by = set(cfg.copy())


    fixed_point = False
    while not fixed_point:
        fixed_point = True
        for block in cfg:
            # print("----------------")
            # print("looking at block: ", block)
            if block == top_level:
                continue
                
            previous_dom = copy.deepcopy(b_dict[block].dominated_by)
            # print("previous_dom: ", previous_dom)
            if b_dict[block].parent_list:
                parent_list = list(b_dict[block].parent_list)
                new_dom = b_dict[parent_list[0].name].dominated_by.copy()
                # print("new_dom start: ", new_dom)
                for parent in b_dict[block].parent_list:
                    parent = b_dict[parent.name]
                    new_dom = new_dom.intersection(parent.dominated_by)
                    # print("parents dominated by: ", parent.dominated_by)
                    # print("looking at parent: ", parent.name)
                    # print("new_dom: ", new_dom)
                
                new_dom.add(block)
                # print("new_dom after: ", new_dom)
            

            
            if new_dom != previous_dom:
                b_dict[block].dominated_by = new_dom
                fixed_point = False
    
    # remove self reference
    for block_name in cfg:
        block_obj = block_dict[block_name]
        block_obj.dominated_by.remove(block_name)
        block_dict[block_name] = block_obj
    

    for block_name in cfg:      #C
        block_obj = block_dict[block_name]
        dominated_by = block_obj.dominated_by
        imm_dom_by = dominated_by.copy()
        # print("-----------------")
        # print("block name: ", block_name)
        # print("dominated by: ", dominated_by)
        for candidate in dominated_by:     #B,A  
            # print("candidate: ", candidate)
            # print("candidate dominated by: ", block_dict[candidate].dominated_by)
            if candidate == block_name:     
                imm_dom_by.remove(candidate)
            else:
                # if the candidate is not dominated by any other
                # if candidate dominated by
                
                # if any block dominates the current block and a neighbor, it can't be in contention
                for block in block_dict[candidate].dominated_by:
                    # print("block: ", block)
                    if block in dominated_by:
                        imm_dom_by.remove(block)
        
        block_obj.dominated_by = imm_dom_by
        # print("~~~~~~~~~~~~~~~~")
        # print(f"block: {block_name} dominated by: {imm_dom_by}" )
        block_dict[block_name] = block_obj


def renaming_pass(b_dict, dom_map, top_level):
    """
    This is the renaming pass, which will rename all of the variables in the program in the case there are multiple definitions to the same variable.

    Input: 
    b_dict: Dict {block_name: Block()} - we will be iterating through this for all of the instructions
    dom_map: Map {block_name: List[block_name]} - a map of the immediate dominators for the block
    top_level: str - the entry block where we have the start the renaming
    """
    rename(top_level, b_dict, dom_map, {})

fresh_name_dict = {}

def fresh_name(var_name):
    """
    Gets a fresh name for variable based off fresh_name_dict.
    """
    global fresh_name_dict
    if var_name not in fresh_name_dict:
        fresh_name_dict[var_name] = -1
    
    new_num = fresh_name_dict[var_name] + 1
    fresh_name_dict[var_name] += 1
    return var_name +"_"+str(new_num)

def rename(block_name, b_dict, dom_map, stack):
    """
    Renames all the variables in the block based off variable definitions before.
    Input:
    block_name: str - name of the block to rename
    b_dict: dict - {block_name: Block()}
    dom_map: dict - {block_name: block_name (that dominates it)}
    stack: dict - {var: most_recent_name} = the stack is utilized for the uses
    """
    block_obj = b_dict[block_name]
    
    for instr in block_obj.instruction_list:
        # args
        # this instruction's arguments are changed based off whatever the most recent thing on the stack is
        # we do the arguments first and we are confident that this will work because you can't use a variable before initializing it, and when you initalize, the stack will get populated
        # print("stack: ", stack)
        # print("orig_instr: ", instr)
        if "args" in instr:
            final_args_list = []
            if not("op" in instr and "phi" == instr["op"]):
                for arg in instr["args"]:
                    if arg in stack:
                        final_args_list.append(stack[arg][-1])
                    else:
                        final_args_list.append(arg)
                # instr["args"] = [stack[arg][-1] for arg in instr["args"] if arg in stack]
                instr["args"] = final_args_list
        #dest
        # instruction's arguments have to be something fresh that has not been used globally
        if "dest" in instr:
            fresh = fresh_name(instr["dest"])

            #add the new fresh variable to stack because all subsequent uses have to use this name
            if not instr["dest"] in stack:
                stack[instr["dest"]] = []
            stack[instr["dest"]].append(fresh)

            # set the destination to be the fresh name
            instr["dest"] = fresh

        # print("new_instr: ", instr)
    
    # may need to assign back to block
    b_dict[block_name] = block_obj

    # print("current block is: ", block_name)
    for child_block in block_obj.children_list:
        # print("looking at child: ", child_block.name)
        child_block = b_dict[child_block.name]
        for instr in child_block.instruction_list:
            # print("looking at instr: ", instr)
            if "op" in instr and instr["op"] == "phi":
                i = 0
                while i < len(instr["labels"]):
                    if instr["labels"][i] == block_name:
                        # print("instr: ", instr)
                        instr["args"][i] = stack[instr["args"][i]][-1]      #renaming a phi
                        # print("new instr: ", instr)
                    i += 1
        b_dict[child_block.name] = child_block
    
    for child_block_name in dom_map[block_name]:
        rename(child_block_name, b_dict, dom_map, stack)


    

def invert_dom_graph(b_dict):
    """
    For each block, finds all the blocks that it dominates.
    """
    dominating_map = {}
    for b_name in b_dict:
        for b_name_two in b_dict:
            if b_name in b_dict[b_name_two].dominated_by:
                if b_name not in dominating_map:
                    dominating_map[b_name] = []
                dominating_map[b_name].append(b_name_two)
    
    return dominating_map
def insert_phi(dom_front_map, var_def_map, var_list, block_dict):
    """
    Converts function into ssa format. The function will have blocks that all relate as a CFG together.
    Input:
    dom_front_map: (Dict) {str(block_name): List[blocks_in_dom_front]}
    var_def_map: (Dict) {str(variable_names): set[blocks_that_define_v]}
    var_list: List[variables_names]
    block_dict: (Dict) {block_name: Block()}
    """
    for var in var_list:
        worklist = var_def_map[var].copy() #inspired from chatgpt - worklist
        # print("starting worklist: ", worklist)
        while worklist:
            defining_block = worklist.pop()
            # print("looking at block: ", defining_block)
            for block in dom_front_map[defining_block]: # this is the block name
                new_phi = {"dest": var, "op": "phi", "args":[var], "labels":[defining_block]}

                # insert phi function into the block
                # go through the block to make sure the phi function isn't there, and if it is there then add the var and defining block
                block_obj = block_dict[block]
                added_phi = False
                for instr in block_obj.instruction_list:
                    if "op" in instr and "args" in instr and "labels" in instr:
                        if instr["op"] == "phi" and var in instr["args"]:
                            if defining_block not in instr["labels"]:
                                # print("spotted ding ding ding instruction: ", instr)
                                instr["args"].append(var)
                                instr["labels"].append(defining_block)

                            # instr["args"] = list(set(instr["args"]))
                            # instr["labels"] = list(set(instr["labels"]))
                            added_phi = True
                            break   # we can't have multiple phi functions for the same variable
                
                if not added_phi:       #if we haven't added phi, then we must not have seen it before and we can add it to the instruction list
                    # print("added instruction into: ", block)
                    block_obj.instruction_list.insert(1, new_phi)       # putting a deepcopy here because we dont want reference issues
                    # print("block: ", block)
                    # print("block instruction list: ", block_obj.instruction_list)

                block_dict[block] = block_obj   #just making sure the references are properly added to the global map

                var_def_map[var].add(block)      # this new defined variable 
                worklist.add(block)
    
    # prune phi
    for block_name in block_dict:
        final_instr_list = []
        block_obj = block_dict[block_name]
        for instr in block_obj.instruction_list:
            if "op" in instr and "dest" in instr and "args" in instr and "labels" in instr:
                if instr["op"] == "phi":
                    if len(instr["args"]) < 2:
                        continue
            final_instr_list.append(instr)
        
        block_obj.instruction_list = final_instr_list
        block_dict[block_name] = block_obj
                

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
        var_def_map = {}
        variables = []
        curr_label = func["name"]
        for instr in instruction_list:
            if "label" in instr:
                curr_label = instr["label"]
                block_order.append(curr_label)

            if "dest" in instr:
                var_name = instr["dest"]
                if var_name not in var_def_map:
                    var_def_map[var_name] = set()     # need to make it a set because we don't want repeats
                    variables.append(var_name)
                var_def_map[var_name].add(curr_label)
                    
        # print("var def map: ", var_def_map)
        block_order = [func["name"]] + block_order

        # print("block order: ", block_order)

        # print("instruction_list: ", instruction_list)
        block_dict = create_blocks(instruction_list, start_name=func["name"]).copy()

        # for block in block_dict:
        #     print("name: ", block_dict[block].name)
        #     # print("parents: ", block_dict[block].parent_list)
        #     print("parent set: ", set(block_dict[block].parent_list))
        #     # print("children: ", block_dict[block].children_list)
        #     print("children set: ", set(block_dict[block].children_list))
        
        fixed_point_analysis(block_dict, block_order[-1])
        # dominance_transfer_analysis(block_dict, "B")

        # for b in block_dict:
        #     print(f"b: {b} dom: {block_dict[b].dom}")

        df_map = create_dom_front(block_dict)
        # print(find_dominating_map(block_dict))
        find_imm_domin(block_dict, func["name"])
        # for block in block_dict:
        #     print(f"block: {block} dominated by: {block_dict[block].dominated_by}")
        dom_graph = invert_dom_graph(block_dict)
        # for block in block_dict:
        #     print(f"block: {block} dominated by: {block_dict[block].dominated_by}")
        # print("df map: ", df_map)

        insert_phi(df_map, var_def_map, variables, block_dict)

        for block_name in block_order:
            if block_name not in dom_graph:
                dom_graph[block_name] = []
        renaming_pass(block_dict, dom_graph, func["name"])

        instruction_list = []
        seen_blocks = []
        # remove duplicates
        while block_order:
            visited_block = block_order.pop(0)

            if visited_block not in seen_blocks:
                seen_blocks.append(visited_block)
                instruction_list = instruction_list + copy.deepcopy(block_dict[visited_block].instruction_list)
        func["instrs"] = instruction_list.copy()
    
    print(is_ssa(prog))

    # json.dump(prog, sys.stdout, indent=2)
