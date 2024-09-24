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
        print("instr: ", instr)
        # some instr have operations, while others like label instr just have `label` defined
        if "label" in instr:
            print("current block is: ", curr_block)

            ret_block = block_list[instr["label"]]
            print("returned block is: ", ret_block)
            
            curr_block = ret_block
            print("new block is: ", curr_block)
                    
        if "op" in instr:
            if instr["op"] in terminator_list:
                # print("seen a terminator: ", instr)
                # terminator instr is counted, but next instr is not guaranteed
                curr_block.add_instr(instr)
                child_list_as_blocks = curr_block.add_child_blocks(instr["labels"])
                for block in child_list_as_blocks:
                    block_list[block.name] = block
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
        print("adding child blocks")
        print("label list: ", label_list)
        for label in label_list:
            self.children_list.append(Block(name=label, input_table=[], instruction_list=[], children_list=[], output_table= {}))
        
        print("self.children_list: ", self.children_list)
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

class Value():
    def __init__(self, op, args):
        self.op = op
        self.args = args
    def __repr__(self):
        final_str = self.op + "("
        for arg in self.args:
            final_str += str(arg)
            final_str += ","
        final_str = final_str[:-1] + ")"
        return final_str
    def equals(self, val):
        """
        Custom equality checker.
        """
        if self.op == "const":
            return False
        if self.op == val.op:
            # check if the length of arguments is the same, bc if they arent then vals can't be same
            # check the length of the set because you want to compare all the unique instances
            # ex. mul(4,4) vs mul(4,5). It checks if first 4 is in second, passes, then checks second 4 is in sec, passes 
            # making it into a set will make sure that these duplicates don't show up
            if len(set(val.args)) != len(set(self.args)):           
                return False
            # if len are same, then check that all args are in each other, doesn't matter where you start at this point

            return all([arg in val.args for arg in self.args])
        return False
    
def generate_value(instr, table):
    """
    Generates the value from the instruction.
    Input: Dict{}
    Output: str?
    """
    arith_ops = ["add", "sub", "mul", "div"]
    if instr["op"] == "const":
        return Value(op="const", args=[instr["value"]])
    if instr["op"] == "id":
        return Value(op="id", args=instr["args"])
    elif instr["op"] in arith_ops:
        consolidated_args = []
        for arg in instr["args"]:       # go through all arguments in new instr
            # print("arg: ", arg)
            for num in table:           # go through all existing to see if there are overlaps
                var_list = table[num][1]
                if arg in var_list:
                    consolidated_args.append(num)

        return Value(op=instr["op"], args=consolidated_args)
    else:
        return None
        

def valueInTable(val, tab):
    """
    Returns whether the val is in tab. Used to determine is a subexpression has been computed already.
    """
    print("tab: ", tab)
    for key in tab.keys():          # go through the table's keys, which are the instruction numbers
        print(f"key: {key} | value: {tab[key]}")

    return False    # if we make it through all of the keys then we return False

def pull_constant(val, table):
    """
    Pulls the value from the table
    """
    print(f"should be pulling {val} from {table}")

    for instr_num in table:
        dest_var = table[instr_num][1]       # the destination variable is stored in a list in the second index
        if val.args == dest_var:
            print("found it! returning: ", table[instr_num][0])
            return table[instr_num][0]
    return None

def convert_to_instr(instr_value, table):
    """
    Converts an instruction that is in deconstructed format into a bril appropriate output
    """
    dest = instr_value[1][0]    # 1 is the var name, 0 makes sure that we get only one var name, there may be multiple but we only need one, and for simplicity in the cases that we have only one, it is guaranteed in the 0th index spot
    val_obj = instr_value[0]    # the value object is stored in the 0th index of the tuple
    match val_obj.op:
        case "const":
            return {'dest': dest, 'op': val_obj.op, 'type': 'int', 'value': val_obj.args[0]}
        case _:
            final_simplified = []
            for arg_val in val_obj.args:
                final_simplified.append(table[arg_val][1][0])       # we don't want to add the unique number id, we want to add the variable name associated with the argument
            return {'args': final_simplified, 'dest': dest, 'op': val_obj.op, 'type': 'int'}
            
    
def table_to_prog(table):
    """
    Converts the table to program format by going through all the keys in our tables, which should, by definition, by unique instructions.
    """
    i = 1
    instruction_list = []
    while i in table.keys():
        instr_as_value = table[i]
        instruction_list.append(convert_to_instr(instr_as_value, table))
        i += 1

    return instruction_list
def const_prop(prog, starting_table):
    """
    Local value numbering pass through the program.
    DESIGN CHOICE: ONE PASS OR TWO PASS: If you go in one pass, you keep checking backwards to see what value it takes on.
    If you do in two pass, your first pass just dumbly goes through adding values and the second pass will be in charge of propagating the values
    """
    # TODO: handle case where variables are used before declaration
    # table will store values with key = Num, val = (Value, Var)
    table = starting_table
    for fn in prog["functions"]:
        i = 1
        for instr in fn["instrs"]:
            value = generate_value(instr, table)
            if value:           # if we have generated a value, then we should add it to the table
                if value.op == "id":
                    pulled_constant = pull_constant(value, table)# if the value has an id to it, check if it's in the dictionary alr
                    if pulled_constant is not None:
                        table[i] = (pulled_constant, [instr["dest"]])
                else:
                    table[i] = (value,[instr["dest"]])
                i += 1
            # print("table after: ", table)

    return table_to_prog(table), table

def consolidate_input_tables(input_table_list):
    print("consolidating input lists: ", input_table_list)
    return {}
def const_prop_on_blocks(starting_block_name, block_dict):
    init_block = block_dict[starting_block_name]         # we always start with the main block
    if len(init_block.input_table) > 1:
        init_block.input_table = consolidate_input_tables(init_block.input_table)
    init_block.instruction_list, init_block.output_table = const_prop(init_block.instruction_list, init_block.input_table)
    final_list = []
    for child_block in init_block.children_list:
        child_block.input_table.append(init_block.output_table)
        final_list.append(const_prop_on_blocks(child_block.name, block_dict))
    init_block.children_list = final_list
    return init_block
############################################
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)
    # print("init program: ", prog)
    
    # block_dict = create_blocks(prog)
    # return_prog = const_prop_on_blocks("main", block_dict)
    # print("")
    return_prog = const_prop(prog, {})
    print(return_prog)
    # for key in return_prog:
        # print(return_prog[key].instruction_list)
    # json.dump(return_prog, sys.stdout, indent=2)