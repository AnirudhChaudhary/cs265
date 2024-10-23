"""
Dominance Tree code
"""
import copy
import json
import sys
from is_ssa import is_ssa
from from_ssa import from_ssa
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
            if B in dominator_map[A] and A != B:   # B can't be in the dominance of A if it is dominated by A
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
    init_stack = {}
    for var in fresh_name_dict:
        init_stack[var] = [var]
    rename(top_level, b_dict, dom_map, init_stack, block_ordering)



def fresh_name(var_name):
    """
    Gets a fresh name for variable based off fresh_name_dict.
    """
    global fresh_name_dict
    if var_name not in fresh_name_dict:
        fresh_name_dict[var_name] = -1
    
    new_num = fresh_name_dict[var_name] + 1
    fresh_name_dict[var_name] += 1
    return var_name +"."+str(new_num)

def rename(block_name, b_dict, dom_map, stack, block_order):
    """
    Renames all the variables in the block based off variable definitions before.
    Input:
    block_name: str - name of the block to rename
    b_dict: dict - {block_name: Block()}
    dom_map: dict - {block_name: block_name (that dominates it)}
    stack: dict - {var: most_recent_name} = the stack is utilized for the uses
    """
    new_stack = stack.copy()
    block_obj = b_dict[block_name]
    
    # print("block name: ", block_name)
    for instr in block_obj.instruction_list:
        # args
        # this instruction's arguments are changed based off whatever the most recent thing on the stack is
        # we do the arguments first and we are confident that this will work because you can't use a variable before initializing it, and when you initalize, the stack will get populated
        if "args" in instr:                             # this means that we are using the variable, so pull from the stack
            final_args_list = []
            if not("op" in instr and "phi" == instr["op"]):
                for arg in instr["args"]:
                    if arg in new_stack:
                        final_args_list.append(new_stack[arg][-1])
                    else:
                        final_args_list.append(arg)
                instr["args"] = final_args_list
        #dest
        # instruction's arguments have to be something fresh that has not been used globally
        if "dest" in instr:
            fresh = fresh_name(instr["dest"])

            #add the new fresh variable to stack because all subsequent uses have to use this name
            if not instr["dest"] in stack:
                new_stack[instr["dest"]] = []
            new_stack[instr["dest"]].append(fresh)

            # set the destination to be the fresh name
            instr["dest"] = fresh

        # print("new_instr: ", instr)
    
    # may need to assign back to block
    b_dict[block_name] = block_obj

    # print("current block is: ", block_name)
    # look into your children and change the phis
    for child_block in block_obj.children_list:
        # print("looking at child: ", child_block.name)
        child_block = b_dict[child_block.name]
        for instr in child_block.instruction_list:
            # print("looking at instr: ", instr)
            if "op" in instr and instr["op"] == "phi":
                if None in instr["labels"]:
                    i = instr["labels"].index(None)             # find the index of the label that is None in the labels
                    var_name  = instr["args"][i]                # find out what the variable name is in the corresponding spot in the args

                    # look up the var name in the new stack

                    if var_name in new_stack:                   # if the var name is in the new stack then change the arg
                        instr["args"][i] = new_stack[instr["args"][i]][-1]      #renaming a phi
                    else:
                        instr["args"][i] = "__undefined"        # o.w replace the instruction with undefined

                    instr["labels"][i] = block_obj.name

                
                
        b_dict[child_block.name] = child_block
    
    original_stack = copy.deepcopy(new_stack)
    # print("After going through instructions -> stack: ", original_stack)
    for block in block_order:
        if block in dom_map[block_name]:
            rename(block, b_dict, dom_map, copy.deepcopy(original_stack), block_order)


    


def insert_phi(dom_front_map, var_def_map, var_type_map, var_list, block_dict):
    """
    Converts function into ssa format. The function will have blocks that all relate as a CFG together.
    Input:
    dom_front_map: (Dict) {str(block_name): List[blocks_in_dom_front]}
    var_def_map: (Dict) {str(variable_names): set[blocks_that_define_v]}
    var_list: List[variables_names]
    block_dict: (Dict) {block_name: Block()}
    """

    for var in var_list:
        worklist = var_def_map[var].copy()     # our defined block list could change as the program goes on so thats why it is in a while loop         #inspired from chatgpt - worklist 
        seen = []
        while worklist:
            defining_block = worklist.pop()
            if defining_block in seen:
                continue
            seen.append(defining_block)

            for block in dom_front_map[defining_block]: # this is the block name
                block_obj = block_dict[block]

                new_phi = {"dest": var, "op": "phi", "type": var_type_map[var], "args":[var for _ in block_obj.parent_list], "labels":[None for _ in block_obj.parent_list]}
                added_phi = False
                for instr in block_obj.instruction_list:
                    if "dest" in instr and "op" in instr:
                        if instr["dest"] == var and instr["op"] == "phi":
                            added_phi = True

                if not added_phi:
                    block_obj.instruction_list.insert(1, new_phi)

                block_dict[block] = block_obj   #just making sure the references are properly added to the global map

                var_def_map[var].add(block)      # this new defined variable 
                worklist.add(block)


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
            if block == top_level:
                continue
                
            previous_dom = copy.deepcopy(dom_map[block])

            if b_dict[block].parent_list:
                parent_list = list(b_dict[block].parent_list)
                new_dom = dom_map[parent_list[0].name]
                for parent in b_dict[block].parent_list:
                    new_dom = new_dom.intersection(dom_map[parent.name])
                
                new_dom.add(block)

            
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
                
def dfs_(start_name, desired, b_dict):
    """
    Performs a depth first search on the control flow graph starting from the start block. 
    Stops when it reaches the desired block.
    Input: 
    - start_name: str - the block name to start the search from
    - desired: str - the block name to stop the search at
    - b_dict: dict[str, Block] - the block dictionary
    Output:
    - list[str] - the list of blocks visited in the order they were visited
    """
    q = [start_name]
    visited = []
    while q:
        block = q.pop(0)
        if block in visited:
            continue
        visited.append(block)
        if block == desired:
            break
        block_obj = b_dict[block]
        for child in block_obj.children_list:
            q.append(child.name)
    return visited
loop_map = {}

def find_loops_starting_from(start_name, b_dict):
    """
    Goes through the control flow graph starting from a block and finds all the loops.
    """
    loops = []
    
    def dfs(block_name, path):
        if block_name in path:  # Detected a cycle (loop)
            loop_start_idx = path.index(block_name)
            loops.append(path[loop_start_idx:])  # Capture the loop portion of the path
            return
        
        path.append(block_name)
        block_obj = b_dict[block_name]
        for child in block_obj.children_list:
            dfs(child.name, path[:])  # Pass a copy of the path to avoid modification
        path.pop()  # Backtrack after exploring all children
    
    dfs(start_name, [])
    return loops
def find_loops(b_dict, top_level, be_map):
    """
    Goes through the control flow graph and finds all the loops.
    """
    print("back edge map: ", be_map)
    loops = []
    for header in be_map:
        for latch in be_map[header]:
            loop = set()
            # print(f"header: {header}  latch: {latch}")
            for b_name in b_dict:
                # print("---------------------------")
                # print("looking at: ", b_name)
                reachable = dfs(b_name, latch, b_dict)
                # print("reachable: ", reachable)
                if latch not in reachable:
                    continue
                else:
                    if header in reachable:
                        continue
                    else:
                        for r in reachable:
                            loop.add(r) # it is possible for the current node to make it to the end without going through header
            loop.add(header)
            loop.add(latch)
            loops.append(loop)

    #         seen = []
    #         desired = latch
    #         loops.extend(find_path_to(desired, seen, b_dict, header))
    # print("all loops found: ", loops)
    return loops

  
def inv_map(map):
    dominating_map = {}
    for b_name in map:
        if b_name not in dominating_map:
            dominating_map[b_name] = []
        for b_name_two in map:
            if b_name in map[b_name_two]:    
                dominating_map[b_name].append(b_name_two)
    return dominating_map

def create_dominator_tree(block_dict, start_node, dom):
    """
    Create the tree to find what the immediate dominators for each of the nodes is.
    """
    parent = {b: start_node for b in block_dict}

    # print(dom)
    # you can't be your own immediate dominator
    # Removes self as a dominator 
    for d in dom:
        for dominat in dom[d]:
            if dominat == d:
                dom[d].remove(d)

    # go through all of the blocks to find their immediate dominators
    for b in block_dict:
        potential_parent = dom[b].copy()
        for dominator in dom[b]:                    #go through all blocks that dominate the current node, we want to eliminate any node that dominates any other node in the list
            for pred in dom[dominator]:            
                if pred in potential_parent:        # if there is a node (A) that dominates a node (B) that dominates our current node then A cannot be an immediate dominator of our current node. A block can't have two dominators so we are guaranteed to have 1 or zero left
                    potential_parent.remove(pred)
        assert len(potential_parent) <= 1, "found more than one potential parent"
        
        parent[b] = potential_parent

    return parent


    
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)

    for func in prog["functions"]:
        
        instruction_list = []
        instruction_list = func["instrs"]
        # add entry block to the beginning
        entry_block_instr = {"label": "b1"}             # need to add the label for the entry block so that later phi's can find any var that is in the entry block (it can't recognize the function name as a label)
        instruction_list.insert(0, entry_block_instr)

        if "args" in func:
            func_args = func["args"]
        else:
            func_args = []
        variables = []
        var_def_map = {}
        var_type_map = {}           # each variable has it's own type
        fresh_name_dict = {}
        for arg_dict in func_args:                  # for each argument TO THE FUNCTION, need to add it to the defined variable and their corresponding types
            var_name = arg_dict["name"]
            variables.append(var_name)
            var_def_map[var_name] = {func["name"]}
            var_type_map[var_name] = arg_dict["type"]
            fresh_name(var_name)

        block_order = []
        curr_label = func["name"]

        # Create variable definition map which will be used for inserting phis
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
                var_type_map[var_name] = instr["type"]


                    
        # print("var type map: ", var_type_map)
        
        # block_order = func["name"] + block_order
    

        # print("block order: ", block_order)

        # print("instruction_list: ", instruction_list)
        block_dict = create_blocks(instruction_list, start_name=func["name"]).copy()
        # for b in block_dict:
        #     print("block: ", b)
        #     print("parents: ", block_dict[b].parent_list)
        terminator_list = ["br", "jmp"]

        ###### INSERTING PREHEADERS #######
        # worklist = block_order.copy()
        # while worklist:                       # go through all of the blocks to identify any self referencing ones
        #     block_name = worklist.pop(0)
        #     # print("working on block name: ", block_name)
        #     block_obj = block_dict[block_name]              # Go through all of the instructions to find the branch instruction
        #     instruction_list = block_obj.instruction_list
        #     if len(instruction_list) == 0:              # if the block is empty then we don't need to do anything
        #         continue
        #     last_instr = instruction_list[-1]                      # If there is a conditional branch then itll be the last instruction in the list
        #     # print("last instruction: ", last_instr)
        #     if "op" in last_instr and last_instr["op"] in terminator_list:
        #         branching_labels = last_instr["labels"]             # if the last instruction is a branch or jump then it will have a list of labels
        #         if block_name in last_instr["labels"]:              # if we are self referencing then we need to create an entry block
        #             new_block_name = block_name+"_entry"
        #             orig_index = block_order.index(block_name)          # get the index of the original block
        #             block_order.insert(orig_index, new_block_name)                      # want to preserve ordering of the flow by inserting the entry where the original block used to be
        #             new_entry_block = Block(name=new_block_name)

        #             jump_instr = {"op":"jmp", "labels":[block_name]}
        #             new_entry_block.instruction_list.append({"label": new_block_name})
        #             new_entry_block.instruction_list.append(copy.deepcopy(jump_instr))
        #             new_entry_block.children_list.add(copy.deepcopy(block_dict[block_name]))
        #             for b_name in block_dict:               # go through all of the blocks and update if they used the self referencing block
        #                 b_obj = block_dict[b_name]
        #                 instr_list = b_obj.instruction_list
        #                 if instr_list == []:
        #                     continue
        #                 l_inst = instr_list[-1]
        #                 # print("l_inst: ", l_inst)
        #                 # print("b_name: ", b_name)
        #                 if "op" in l_inst and l_inst["op"] in terminator_list:
        #                     branching_labels = l_inst["labels"]
        #                     num_labels = enumerate(branching_labels)
        #                     # print("num labels: ", [l for l in num_labels])
        #                     for label in num_labels:
        #                         if label[1] == block_name:
        #                             # print("making a change")
        #                             l_inst["labels"][label[0]] = new_block_name
        #                 block_dict[b_name] = b_obj

        #             block_dict[new_block_name] = new_entry_block
                # else:
                    # print("didn't self reference block: ", block_name)
    
        dominators = find_dominators(block_dict, func["name"])

        df_map = create_dom_front(dominators, block_dict)

        dom_graph = inv_map(dominators)     # dom graph has all of the nodes that dominate it

        dominator_tree = create_dominator_tree(block_dict, func["name"], dom_graph)

        insert_phi(df_map, var_def_map, var_type_map, variables, block_dict)

        for block_name in block_order:
            if block_name not in dom_graph:
                dom_graph[block_name] = []

        inv_dom_tree = inv_map(dominator_tree)
        
        renaming_pass(block_dict, inv_dom_tree, func["name"], block_order)

        ########### LOOP INVARIANCE ####################
        def find_back_edges(block_dict, dom_graph):
            """
            Finds all of the back edges in a control flow graph. A backedge is between a node to a node that dominates it.
            """
            # print("dom graph: ", dom_graph)
            back_edges = {}
            for block_name in block_dict:           # go through all of the blocks
                b_obj = block_dict[block_name]
                for child in b_obj.children_list:     # go through all edges
                    if block_name in dom_graph[child.name]:       # if the parent dominates the block
                        if child.name not in back_edges:
                            back_edges[child.name] = set()
                        back_edges[child.name].add(block_name)
            return back_edges

        # print("dominators: ", dominators)
        back_edge_map = find_back_edges(block_dict, dominators)
        # print("back edge map: ", back_edge_map)
        # need to be careful that values in one loop don't interfere with anything in a different loop with the same header
        loops =[]
        for header in back_edge_map:
            for latch in back_edge_map[header]:
                loops = find_loops_starting_from(header, block_dict)

                # print("loops: ", loops)

        # Combine loops into bigger loops by looking at the headers
        # Few considerations to make:
        # Nested loops can have one loop be a part of another loop so you can make a big loop out of a small loop BCE + CD -> BCDE
        all_final_loops = []
        if loops:
            for loop in loops:                                          # go through all loops
                final_loop = loop.copy()                                # we can't become smaller than the original loop, we are looking to add more to the loop
                starting_node = loop[0]                                 
                for nested_loop in loops:
                    nested_loop_start = nested_loop[0]
                    if nested_loop_start in loop and nested_loop_start != starting_node:        # we want all nested loops to be included so if the nested loop header is in the loop, then add. OW if nested_loop_start == starting node then both share the same header and are separate loops
                        node_index = loop.index(nested_loop_start)
                        final_loop = final_loop[:node_index] + nested_loop + final_loop[node_index+1:]
                        # final_loop = final_loop.union(nested_loop)
                all_final_loops.append(final_loop)

            # print("all final loops: ", all_final_loops)
            # A loop can be nested or shared. First check that the instruction is loop invariant to the shared loop
            # An instruction is loop invariant to the shared loop if 

            # how does it work for shared loops?

            ################ LOOP INVARIANT CODE MOTION ######################
            # initialize an empty list of loop invariant code

            loop_var_def_map = {}
            for loop in all_final_loops:
                header = loop[0]
                for block_name in loop:
                    b_obj = block_dict[block_name]
                    for instruction in b_obj.instruction_list:
                        if "dest" in instruction:
                            if header not in loop_var_def_map:
                                loop_var_def_map[header] = []
                            loop_var_def_map[header].append(instruction["dest"])
            
            # print("loop var def map: ", loop_var_def_map)
            deterministic_ops = ["add", "sub", "mul", "id", "const"]
            # for each instruction, if the args are defined outside the loop OR the args are defined inside the loop and all args are loop invariant and the instruction is deterministic, then add it to the loop_invariant_code list
            # order all_final_loops based on length of loop
            
            # want to start from the smallest loop and go to the largest
            all_final_loops.sort(key=len)

            for loop in all_final_loops:        # go through all of the loops
                loop_invariant_code = []    
                loop_invariant_vars = []
                header = loop[0]
                found_loop_invariant = True
                while found_loop_invariant:     #iterate to fixed point
                    found_loop_invariant = False
                    for block_name in loop:      #go through all of the blocks in the loop looking for an invariant instruction
                        b_obj = block_dict[block_name]
                        for instruction in b_obj.instruction_list:     # go through all of the instructions
                            # print("instruction: ", instruction)
                            if "op" in instruction and instruction["op"] == "const":
                                loop_invariant_code.append(instruction)
                                loop_invariant_vars.append(instruction["dest"])
                                continue
                            if "args" in instruction and "op" in instruction:
                                if instruction["op"] not in deterministic_ops:
                                    continue
                                add_loop_invariant = False
                                if len(instruction["args"]) == 1:
                                    if instruction["args"][0] not in loop_var_def_map[header]:    # if the arg is not defined in the loop and the instruction is not already in the loop invariant code then add it, should not pass the next time bc instruction is already in
                                        add_loop_invariant = True
                                    else:
                                        if (instruction["args"][0] in loop_invariant_vars):
                                            add_loop_invariant = True
                                else:
                                    add_loop_invariant = True
                                    for arg in instruction["args"]:
                                        if arg in loop_var_def_map[header]:    # if the arg is not defined in the loop and the instruction is not already in the loop invariant code then add it, should not pass the next time bc instruction is already in
                                            add_loop_invariant = False
                                            break
                                        else:   # this means that the arg is defined in the loop
                                            if (arg not in loop_invariant_vars):
                                                add_loop_invariant = False
                                                break
                                if add_loop_invariant:
                                    if instruction not in loop_invariant_code:
                                        loop_invariant_code.append(instruction)
                                        loop_invariant_vars.append(instruction["dest"])
                                        for arg in instruction["args"]:
                                            if arg not in loop_invariant_vars:
                                                loop_invariant_vars.append(arg)
                                        found_loop_invariant = True

                # print("loop invariant code: ", loop_invariant_code)
                # print("loop invariant vars: ", loop_invariant_vars)
                # if we have a loop invariant code then we can do code motion on it
            # if it passes this check, then go through all the other loops and make sure the 
            # print("loop invariant code: ", loop_invariant_code)
            if len(all_final_loops) == 1:
                loop = all_final_loops[0]
                header = loop[0]
                header_obj = block_dict[header]
                parent_set = set([x.name for x in header_obj.parent_list]) #set(header_obj.parent_list)
                dom_set = set(dom_graph[header])
                common = parent_set & dom_set
                common = list(common)
                if len(common) == 1:         #if the header only has one parent
                    pre_header = common[0]
                    b_obj = block_dict[pre_header]
                    for inv in loop_invariant_code:
                        len_b_obj = len(b_obj.instruction_list)
                        b_obj.instruction_list.insert(len_b_obj-1, inv)       # need to insert at 1, because the label is at 0
                        for node in loop:
                            node_obj = block_dict[node]
                            if inv in node_obj.instruction_list:
                                # print("removed instruction: ", inv)
                                node_obj.instruction_list.remove(inv)
                            block_dict[node] = node_obj
                    block_dict[pre_header] = b_obj


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
    # print(json.dumps(from_ssa(prog), indent=2, sort_keys=True))
    json.dump(prog, sys.stdout, indent=2)