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
    


def create_dom_front(dominator_map, b_dict):
    """
    Finds and populates dominance frontier for all blocks in the block dictionary.

    Input: b_dict: dict of {block_name:block_obj}
    Output: df: map of block name to blocks on the frontier
    """
    df = {}
    for A in b_dict:
        df[A] = []                      # initialize the dominance frontier
        for B in b_dict:
            B_block_obj = b_dict[B]
            if B in dominator_map[A]:   # B can't be in the dominance of A if it is dominated by A
                continue

            for b_pred_obj in B_block_obj.parent_list:          # B is in the dom front of A if B has a predecessor that A dominates
                if b_pred_obj.name in dominator_map[A]:
                    df[A].append(B)
    return df
            

def renaming_pass(b_dict, dom_map, top_level, block_ordering):
    """
    This is the renaming pass, which will rename all of the variables in the program in the case there are multiple definitions to the same variable.

    Input: 
    b_dict: Dict {block_name: Block()} - we will be iterating through this for all of the instructions
    dom_map: Map {block_name: List[block_name]} - a map of the immediate dominators for the block
    top_level: str - the entry block where we have the start the renaming
    """
    rename(top_level, b_dict, dom_map, {}, block_ordering)

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

def rename(block_name, b_dict, dom_map, stack, block_order):
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
    
    for block in block_order:
        if block in dom_map[block_name]:
    # for child_block_name in dom_map[block_name]:
            rename(block, b_dict, dom_map, stack, block_order)


    


def insert_phi(dom_front_map, var_def_map, var_list, block_dict):
    """
    Converts function into ssa format. The function will have blocks that all relate as a CFG together.
    Input:
    dom_front_map: (Dict) {str(block_name): List[blocks_in_dom_front]}
    var_def_map: (Dict) {str(variable_names): set[blocks_that_define_v]}
    var_list: List[variables_names]
    block_dict: (Dict) {block_name: Block()}
    """
    # print("var list: ", var_list)
    for var in var_list:
        # print("--------------")
        # print("var: ", var)
        worklist = var_def_map[var].copy() #inspired from chatgpt - worklist
        # print("starting worklist: ", worklist)
        seen = []
        while worklist:
            # print("--------------------------")
            # print("worklist: ", worklist)
            defining_block = worklist.pop()
            if defining_block in seen:
                continue
            seen.append(defining_block)
            # print("looking at block: ", defining_block)
            # print("defining block: ", defining_block)
            # print("frontier: ", dom_front_map[defining_block] )
            for block in dom_front_map[defining_block]: # this is the block name
                new_phi = {"dest": var, "op": "phi", "args":[var], "labels":[defining_block]}
                # print("block: ", block)
                # insert phi function into the block
                # go through the block to make sure the phi function isn't there, and if it is there then add the var and defining block
                block_obj = block_dict[block]
                added_phi = False
                for instr in block_obj.instruction_list:
                    if "op" in instr and "args" in instr and "labels" in instr:
                        if instr["op"] == "phi" and var in instr["args"]:
                            if defining_block not in instr["labels"]:
                                # print("adding defining block: ", defining_block)
                                # print("spotted ding ding ding instruction: ", instr)
                                instr["args"].append(var)
                                instr["labels"].append(defining_block)

                            # instr["args"] = list(set(instr["args"]))
                            # instr["labels"] = list(set(instr["labels"]))
                            added_phi = True
                            break   # we can't have multiple phi functions for the same variable
                
                if not added_phi:       #if we haven't added phi, then we must not have seen it before and we can add it to the instruction list
                    # print("added instruction into: ", block)
                    block_obj.instruction_list.insert(1, new_phi)       # insert at position 1 because usually the label is defined in the first spot
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

def find_dominators(b_dict, top_level):
    cfg = list(b_dict.keys())
    dom_map = {}
    for block in cfg:
        if block == top_level:
            dom_map[block] = {top_level}
        else:
            dom_map[block] = set(cfg.copy())


    fixed_point = False
    while not fixed_point:
        fixed_point = True
        for block in cfg:
            # print("----------------")
            # print("looking at block: ", block)
            if block == top_level:
                continue
                
            previous_dom = copy.deepcopy(dom_map[block])
            # print("previous_dom: ", previous_dom)
            if b_dict[block].parent_list:
                parent_list = list(b_dict[block].parent_list)
                new_dom = dom_map[parent_list[0].name]
                # new_dom = b_dict[parent_list[0].name].dominated_by.copy()
                # print("new_dom start: ", new_dom)
                for parent in b_dict[block].parent_list:
                    # parent = b_dict[parent.name]
                    new_dom = new_dom.intersection(dom_map[parent.name])
                    # print("parents dominated by: ", parent.dominated_by)
                    # print("looking at parent: ", parent.name)
                    # print("new_dom: ", new_dom)
                
                new_dom.add(block)
                # print("new_dom after: ", new_dom)
            

            
            if new_dom != previous_dom:
                dom_map[block] = new_dom
                fixed_point = False
    dominating_map = {}
    for b_name in dom_map:
        if b_name not in dominating_map:
            dominating_map[b_name] = []
        for b_name_two in dom_map:
            if b_name in dom_map[b_name_two]:    
                dominating_map[b_name].append(b_name_two)
    dom_map = dominating_map.copy()
    return dom_map
                
loop_map = {}
def find_loops(b_dict, top_level, be_map):
    """
    Goes through the control flow graph and finds all the loops.
    """
    # print("back edge map: ", be_map)
    loops = []
    for header in be_map:
        for latch in be_map[header]:
            loop = set()
            print(f"header: {header}  latch: {latch}")
            for b_name in b_dict:
                print("---------------------------")
                print("looking at: ", b_name)
                reachable = dfs(b_name, latch, b_dict)
                print("reachable: ", reachable)
                if latch not in reachable:
                    continue
                else:
                    if header in reachable:
                        continue
                    else:
                        loop.add(b_name) # it is possible for the current node to make it to the end without going through header
            loop.add(header)
            loop.add(latch)
            loops.append(loop)

    #         seen = []
    #         desired = latch
    #         loops.extend(find_path_to(desired, seen, b_dict, header))
    return loops
    print("all loops found: ", loops)




    
def inv_map(map):
    dominating_map = {}
    for b_name in map:
        if b_name not in dominating_map:
            dominating_map[b_name] = []
        for b_name_two in map:
            if b_name in map[b_name_two]:    
                dominating_map[b_name].append(b_name_two)
    return dominating_map




    
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
        terminator_list = ["br", "jmp"]
        # for block_name in block_dict:                                                                           # go through all of the blocks to identify any self referencing ones
        #     block_obj = block_dict[block_name]                                               # Go through all of the instructions to find the branch instruction
        #     instruction_list = block_obj.instruction_list
        #     last_instr = instruction_list[-1]                                               # If there is a conditional branch then itll be the last instruction in the list
        #     if "op" in instr and instr["op"] in terminator_list:
        #         branching_labels = instr["labels"]
        #         if block_name in instr["labels"]:
        #             new_block_name = block_name+"_entry"
        #             orig_index = block_order.index(block_name)
        #             block_order.insert(orig_index, new_block_name)                      # want to preserve ordering of the flow by inserting the entry where the original block used to be
        #             new_entry_block = Block(name=new_block_name)

        #             jump_instr = {"op":"jmp", "labels":[block_name]}
        #             new_entry_block.instruction_list.append(jump_instr.copy())
        #             new_entry_block.children_list.append(copy.deepcopy(block_dict[block_name]))
        #             for b_name in block_dict:
        #                 b_obj = block_dict[block_name]
        #                 instr_list = b_obj.instruction_list
        #                 l_inst = instr_list[-1]
        #                 if "op" in l_inst and l_inst["op"] in terminator_list:
        #                     branching_labels = l_inst["labels"]
        #                     num_labels = enumerate(branching_labels)
        #                     for label in num_labels:
        #                         if label[1] == block_name:
        #                             l_inst["labels"][label[0]] = new_block_name
        #                 block_dict[b_name] = b_obj

        #             block_dict[new_block_name] = new_entry_block

                                        


        # original_block_dict = copy.deepcopy(block_dict)
        # block_dict = remove_back_edges(original_block_dict, func["name"])

        # for block in block_dict:
        #     print("name: ", block_dict[block].name)
        #     # print("parents: ", block_dict[block].parent_list)
        #     print("parent set: ", set(block_dict[block].parent_list))
        #     # print("children: ", block_dict[block].children_list)
        #     print("children set: ", set(block_dict[block].children_list))
        
        # fixed_point_analysis(block_dict, block_order[-1])       # finds the dominance relation for the blocks
        # for block in block_dict:
        #     print(f"block {block} dominated by: ", block_dict[block].dom)
        # dominators = invert_dom_graph(block_dict)
        # dominance_transfer_analysis(block_dict, "B")

        # for b in block_dict:
        #     print(f"b: {b} dom: {block_dict[b].dom}")
        dominators = find_dominators(block_dict, func["name"])
        # print("dominators: ", dominators)
        df_map = create_dom_front(dominators, block_dict)
        # print("df_map: ", df_map)

        # for key in back_edge_map:
        #     back_edge_map[key] = list(back_edge_map[key])
        # print("df map: ", df_map)
        # print("frontier map: ", df_map)
        # print(find_dominating_map(block_dict))
        # find_imm_domin(block_dict, func["name"])
        # for block in block_dict:
        #     print(f"block: {block} dominated by: {block_dict[block].dominated_by}")
        dom_graph = inv_map(dominators)     # dom graph has all of the nodes that dominate it
        print("dom graph: ", dom_graph)
        # for block in block_dict:
        #     print(f"block: {block} dominated by: {block_dict[block].dominated_by}")
        # print("df map: ", df_map)

        # inserts phi based off frontier
        insert_phi(df_map, var_def_map, variables, block_dict)

        for block_name in block_order:
            if block_name not in dom_graph:
                dom_graph[block_name] = []
        renaming_pass(block_dict, dom_graph, func["name"], block_order)

        ########### LOOP INVARIANCE ####################
        # need to be careful that values in one loop don't interfere with anything in a different loop with the same header
        # print(find_loops(block_dict, func["name"], back_edge_map))

        instruction_list = []
        seen_blocks = []
        # remove duplicates
        while block_order:
            visited_block = block_order.pop(0)

            if visited_block not in seen_blocks:
                seen_blocks.append(visited_block)
                instruction_list = instruction_list + copy.deepcopy(block_dict[visited_block].instruction_list)
        func["instrs"] = instruction_list.copy()
    
    # print(is_ssa(prog))

    # json.dump(prog, sys.stdout, indent=2)
# 