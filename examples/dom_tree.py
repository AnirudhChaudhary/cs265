"""
Dominance Tree code
"""
import copy
import json
import sys
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

            print("block name: ", block_name)
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
    print("parent block doms: ", parent_block_doms)
    if parent_block_doms:
        pred_dom = set.intersection(*parent_block_doms)
    else:
        pred_dom = {}
    block_obj.dom = block_obj.dom.union(pred_dom)

    # may need to assert that the changed blocks are persisted
    b_dict[b_name] = block_obj
    return orig_len == len(block_obj.dom)

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

        print("block order: ", block_order)

        # print("instruction_list: ", instruction_list)
        block_dict = create_blocks(instruction_list, start_name=func["name"]).copy()

        for block in block_dict:
            print("name: ", block_dict[block].name)
            print("parents: ", block_dict[block].parent_list)
            print("parent set: ", set(block_dict[block].parent_list))
            print("children: ", block_dict[block].children_list)
            print("children set: ", set(block_dict[block].children_list))
        
        fixed_point_analysis(block_dict, block_order[-1])
        # dominance_transfer_analysis(block_dict, "B")

        for b in block_dict:
            print(f"b: {b} dom: {block_dict[b].dom}")