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
        self.in_var_mem = {}       # key is variable, value is memory locations that are present at the start of the block
        # in_var_mem is going to be used for the analysis later 
        self.out_var_mem = {}      # key is variable, value is memory locations that are present at the end of the block
        # out_var_mem is going to be used for to get to fixed point 

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
            if B in dominator_map[A] and A != B:   # B can't be in the dominance of A if it is dominated by A
                continue

            for b_pred_obj in B_block_obj.parent_list:          # B is in the dom front of A if B has a predecessor that A dominates
                if b_pred_obj.name in dominator_map[A]:
                    df[A].append(B)

    # df = {}
    # for b_name in b_dict:
    #     df[b_name] = []
    
    # for b_name in b_dict:
    #     block_obj = b_dict[b_name]
    #     parent_list_list = list(block_obj.parent_list) 
    #     if len(parent_list_list) > 1:
    #         for parent_name in parent_list_list:
    #             df[parent_name.name].append(b_name)
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
    # print("-------------------")
    # print("block: ", block_name)
    # print("My block started with this stack: ", stack) 
    # print("dom map: ", dom_map)
    new_stack = stack.copy()
    block_obj = b_dict[block_name]
    
    # print("block name: ", block_name)
    for instr in block_obj.instruction_list:
        # args
        # this instruction's arguments are changed based off whatever the most recent thing on the stack is
        # we do the arguments first and we are confident that this will work because you can't use a variable before initializing it, and when you initalize, the stack will get populated
        # print("stack: ", stack)
        # print("orig_instr: ", instr)
        if "args" in instr:                             # this means that we are using the variable, so pull from the stack
            final_args_list = []
            if not("op" in instr and "phi" == instr["op"]):
                for arg in instr["args"]:
                    if arg in new_stack:
                        final_args_list.append(new_stack[arg][-1])
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
            # print("checking to make sure that the value didn't change: ", original_stack)
    # for child_block_name in dom_map[block_name]:
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
    # print("frontier map: ", dom_front_map)
    # print("var list: ", var_list)
    # print("var def map: ", var_def_map)

    for var in var_list:
        # print("--------------")
        # print("var: ", var)
        worklist = var_def_map[var].copy()     # our defined block list could change as the program goes on so thats why it is in a while loop         #inspired from chatgpt - worklist 
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
                block_obj = block_dict[block]
                # num_parents = len(block_obj.parent_list)

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
    
    # prune phi
    # for block_name in block_dict:
    #     final_instr_list = []
    #     block_obj = block_dict[block_name]
    #     for instr in block_obj.instruction_list:
    #         if "op" in instr and "dest" in instr and "args" in instr and "labels" in instr:
    #             if instr["op"] == "phi":
    #                 if len(instr["args"]) < 2:
    #                     # print("pruned instr")
    #                     continue
    #         final_instr_list.append(instr)
        
    #     block_obj.instruction_list = final_instr_list
    #     block_dict[block_name] = block_obj

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

def meet(parent_list, block_dict):
    """
    Go through the parent list and meet on the parents to get the new block dictionary
    """
    met_vars = {}
    for parent in parent_list:
        block_obj = block_dict[parent.name]
        out_var_mem_dict = block_obj.out_var_mem
        print(f"parent: {parent.name} | dict: {out_var_mem_dict}")
        for var in out_var_mem_dict:      # out var mem is a {}
            if var not in met_vars:
                met_vars[var] = set()
            
            met_vars[var] = met_vars[var].union(out_var_mem_dict[var])

    print("type met vars: ", type(met_vars))
    return met_vars
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)

    for func in prog["functions"]:
        instruction_list = func["instrs"]

        block_order = []
        # state
        allocated_var_map = {}

        entry_block_instr = {"label": "b1"}
        instruction_list.insert(0, entry_block_instr)

        block_dict = create_blocks(instruction_list, start_name=func["name"]).copy()
        curr_mem_loc = 0
        for instr in instruction_list:
            # helps tells us the ordering of the blocks at the end
            if "label" in instr:
                block_order.append(instr["label"])
            
            # helps us find out all of the allocations
            # if "dest" in instr and "op" in instr and instr["op"] == "alloc":
            #     if instr["dest"] not in allocated_var_map:
            #         allocated_var_map[instr["dest"]] = set()
            #     allocated_var_map[instr["dest"]].add(curr_mem_loc)
            #     curr_mem_loc += 1

        print("initial var_type_map: ", allocated_var_map)

        block_order = [func["name"]] + block_order
        print("block order: ", block_order)

        curr_label = func["name"]

        fixed_point = False
        first_pass = True
        curr_mem_loc = 0 
        allocated_var_map = {}
        while not fixed_point:
            fixed_point = True
            curr_mem_loc = 0
            for block in block_dict:
                block_obj = block_dict[block]

                # do a meet on the parents, which is going to be this block's starting "state"
                print("looking at block: ", block)
                # print([block_obj.parent_list[i].out_var_mem for i in range(len(block_obj.parent_list))])
                starting_state = meet(block_obj.parent_list, block_dict)
                print("starting state after meet: ", starting_state)
                block_obj.in_var_mem = starting_state.copy()
                original_out = copy.deepcopy(block_obj.out_var_mem)
                for instr in block_obj.instruction_list:
                    if "dest" in instr:
                        if instr["dest"] not in starting_state:
                            starting_state[instr["dest"]] = set()

                        if "op" in instr and instr["op"] == "alloc":
                            if instr["dest"] in allocated_var_map:
                                allocated_memory = allocated_var_map[instr["dest"]]     # gives us all of the current allocations for the variable
                            
                            else:
                                allocated_var_map[instr["dest"]] = set()
                                allocated_memory = allocated_var_map[instr["dest"]]

                            if curr_mem_loc in allocated_memory:
                                starting_state[instr["dest"]] = copy.deepcopy(allocated_memory)
                                continue
                            
                            else:
                                starting_state[instr["dest"]].add(curr_mem_loc)
                                allocated_var_map[instr["dest"]].add(curr_mem_loc)
                                    
                                curr_mem_loc += 1
                                # print(starting_state[instr["dest"]])

                        if "op" in instr and instr["op"] == "id":
                            dest = instr["dest"]        # it should have a destination because it's an id operator
                            instr_arg = instr["args"][0]
                            print("instr arg: ", instr_arg)
                            if instr_arg in starting_state:                     # based on the dataflow analysis, it's possible that the argument has been been merged from the parents
                                existing_mem_loc = starting_state[instr_arg]     # we want all of the memory locations of the previous argument in the instruction
                                for var in existing_mem_loc:
                                    starting_state[dest].add(var)     # perhaps a reference issue here?
                        
                        if "op" in instr and instr["op"] == "ptradd":
                            dest = instr["dest"]        # it should have a destination because it's an id operator
                            (ptr_arg, offset) = instr["args"]
                            existing_mem_loc = starting_state[ptr_arg]
                            # start_len = starting_state[dest]
                            start_len = len(starting_state[dest])
                            starting_state[dest] = starting_state[dest].union(existing_mem_loc)     # perhaps a reference issue here?
                            end_len = len(starting_state[dest])
                            # allocated_var_map[dest] = copy.deepcopy(starting_state[dest])   # this var matches a previous allocation, but is still allocated so it can be referenced


                            # fixed_point = fixed_point and (start_len == end_len)

                        # load
                        if "op" in instr and instr["op"] == "load":
                            dest = instr["dest"]
                            # print("in load")
                            # print(f"len starting state for var {dest} is {len(starting_state[dest])}")
                            # print("curr_mem_loc: ", curr_mem_loc)
                            # num_loc = 500
                            starting_state[dest] = set([i for i in range(10)])
                
                    # print(starting_state)
                block_obj.out_var_mem = copy.deepcopy(starting_state)
                
                block_dict[block] = block_obj
                print("out var mem: ", block_dict[block].out_var_mem)

                ## Check if the new out is the same as the old out

                # for each var in the starting state, we want to see if there is any difference versus what we had originally
                # print("checking if fixed point")
                # print("starting state before: ", starting_state)
                for var in starting_state:
                    if var not in original_out:
                        fixed_point = False
                    else:
                        # 
                        intersection = set.intersection(starting_state[var], original_out[var])

                        if len(intersection) != len(original_out[var]):
                            fixed_point = False
                # print("starting state after: ", starting_state)
            first_pass = False        
        
        print("final allocated map: ", allocated_var_map)

        for block in block_dict:
            print("block name: ", block)
            print("mem locations: ", block_dict[block].out_var_mem)
        ### the analysis will give the memory pointed locations for all the variables
        ### from here we go back through and we can change the occurences


        

                    
        instruction_list = []
        seen_blocks = []
        # remove duplicates
        while block_order:
            visited_block = block_order.pop(0)

            if visited_block not in seen_blocks:
                seen_blocks.append(visited_block)
                instruction_list = instruction_list + copy.deepcopy(block_dict[visited_block].instruction_list)
        func["instrs"] = instruction_list.copy()
        


    # json.dump(prog, sys.stdout, indent=2)