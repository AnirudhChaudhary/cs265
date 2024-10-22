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
        block_obj.imm_dom_by = imm_dom_by
        # print("~~~~~~~~~~~~~~~~")
        # print(f"block: {block_name} dominated by: {imm_dom_by}" )
        block_dict[block_name] = block_obj

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

def invert_dom_graph(b_dict):
    """
    For each block, finds all the blocks that it dominates.
    """
    dominating_map = {}
    for b_name in b_dict:
        for b_name_two in b_dict:
            # if b_name in b_dict[b_name_two].imm_dom_by:
            if b_name in b_dict[b_name_two].dom:
                if b_name not in dominating_map:
                    dominating_map[b_name] = []
                dominating_map[b_name].append(b_name_two)
    
    return dominating_map



def find_path_to(desired, seen, b_dict, curr):
    # print("desired: ", desired)
    # print("seen: ", seen)
    # print("curr: ", curr)
    # print("-------------")

    child_list = list(b_dict[curr].children_list)
    if curr in seen:
        return []
    elif curr == desired:
        return [[curr]]

    if len(child_list) == 0:
        return []

    seen.append(curr)
    found_paths = []
    for child in child_list:
        child_path = find_path_to(desired, seen, b_dict, child.name)
        if child_path:
            found_paths.extend(child_path)

    # print("I am: ", curr)
    # print("I found, from my children : ", found_paths)

    all_paths = []
    for path in found_paths:
        all_paths.append([curr] + path)

    # print("all paths including me: ", all_paths)

    return all_paths

def insert_phi_bc_loops():
    # go through the back edges because those
    for loop_header in back_edge_map:
        frontier_block = loop_header
        block_obj = b_dict[frontier_block]

        for pred in block_obj.parent_list:
            if pred.name not in df:
                df[pred.name] = []
            df[pred.name].append(loop_header)

def remove_back_edges(b_dict, top_level):
    worklist = [top_level]
    seen = []
    while worklist:
        curr_block = worklist.pop(0)
        b_obj = b_dict[curr_block]

        new_child_list = []
        for child in b_obj.children_list:
            if child not in seen:
                new_child_list.append(child)

def create_dom_front(dominator_map, b_dict, top_level):
    """
    Finds and populates dominance frontier for all blocks in the block dictionary.

    Input: b_dict: dict of {block_name:block_obj}
    Output: df: map of block name to blocks on the frontier
    """
    

    # df = {}
    # for block in b_dict:
    #     df[block] = [b.name for b in b_dict[block].parent_list if len(b_dict[block].parent_list) > 1]
    
    ###### 
    # First we need to remove nasty back edges that make the entire calculation messed up
    # The backedges will be used for loops later on anyways
    strict_dominator_map = {}
    back_edge_map = {}
    worklist = [top_level]
    while worklist:
        curr_block_name = worklist.pop(0) 
        curr_block_obj = b_dict[curr_block_name]
        strict_dominator_map[curr_block_name] = []
        for child in curr_block_obj.children_list:
            if curr_block_name in dominator_map[child.name]:        # if the current block is dominated by a child, then it is a back edge
                if child.name not in back_edge_map:     # if there are multiple back edges back to a header
                    back_edge_map[child.name] = set()
                    back_edge_map[child.name].add(curr_block_name)
                else:
                    # print("ive seen this before: ", child.name)
                    back_edge_map[child.name].add(curr_block_name)
            else:
                strict_dominator_map[curr_block_name].append(child.name)    # otherwise this is a regular edge in our graph
            
            if child.name not in strict_dominator_map:
                worklist.append(child.name)
    
    # print("strict dominator map: ", strict_dominator_map)
    parent_map = {}
    for parent in strict_dominator_map:
        for new_parent in strict_dominator_map[parent]:
            if new_parent not in parent_map:
                parent_map[new_parent] = []
            
            parent_map[new_parent].append(parent)
    
    # print("parent_map: ", parent_map)
    # print("dominator map: ", dominator_map)
    # Go through the regular dominator map and find the dominance frontier
    df = {}
    for b in b_dict:
        df[b] = []
        for prospect in b_dict:
            # a prospect cannot be dominated by the parent
            if prospect in dominator_map[b]:    
                continue
            
            if prospect in parent_map:
                for pred in parent_map[prospect]:
                    if pred in dominator_map[b]:
                        df[b].append(prospect)
            # for pred in b_dict[prospect].parent_list:
            #     if pred.name in dominator_map[b]:
            #         df[b].append(pred.name)
    
    # print("df: ", df)
    # print("strict dominator map: ", strict_dominator_map)
    # print("back edge map: ", back_edge_map)

    return df, back_edge_map
