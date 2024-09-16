import json
import sys
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
    elif instr["op"] in arith_ops:
        consolidated_args = []
        for arg in instr["args"]:       # go through all arguments in new instr
            # print("arg: ", arg)
            max_num = max(table.keys())
            for num in range(max_num, 0, -1):           # go through all existing to see if there are overlaps
                # print(num)
                var_list = table[num][1]
                if arg in var_list:
                    consolidated_args.append(num)
                    break


        # print("generating value with op: ", (instr["op"], consolidated_args))
        return Value(op=instr["op"], args=consolidated_args)
    else:
        return None
        # return Value(op=instr["op"], args=[instr["args"]])

def valueInTable(val, tab):
    """
    Returns whether the val is in tab. Used to determine is a subexpression has been computed already.
    """
    for key in tab.keys():
        table_value = tab[key][0]
        if table_value.equals(val):
            return key
    return False    # if we make it through all of the keys then we return False

def local_value_numbering(prog):
    """
    Local value numbering pass through the program.
    """
    # TODO: handle case where variables are used before declaration
    # table will store values with key = Num, val = (Value, Var)
    table = {}
    for fn in prog["functions"]:
        i = 1
        for instr in fn["instrs"]:
            value = generate_value(instr, table)
            if value:           # if we have generated a value, then we should add it to the table
                # need to compare with the existing operations and values 
                val_in_table = valueInTable(value, table)
                if val_in_table:
                    table[val_in_table][1].append(instr["dest"])    #table[i] gets the value, [1] gets the first element (variable) which should be a list
                else:
                    table[i] = (value, [instr["dest"]])
                    i += 1
            # print("table after: ", table)
    return table

# TODO: In reflection be aware of the fact that the current implementation only works for ints
# TODO: Ask about use before instantiation
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

def preprocessing(prog):
    instructions  = prog["functions"][0]["instrs"]
    for inst in instructions:
        if "dest" in inst and inst["dest"] == "cond":
            return True
        if "label" in inst:
            return True
        if "labels" in inst:
            return True
    
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)
    # print(prog)
    # in this version of lvn, we run away from conditionals and branching
    early_terminate = preprocessing(prog)
    if not early_terminate:
        
        final_instr = prog["functions"][0]["instrs"][-1]    # very adhoc way of dealing with the final instr, bc curr infra is not able to handle those bc they don't have destinations associated with them
        # TODO: Do a local dead code elimination pass before local value numbering
        return_table = local_value_numbering(prog)
        """
        table after:  {1: (const(4), ['a']), 2: (const(2), ['b']), 3: (const(2), ['c']), 4: (add(1,2), ['sum1', 'sum2']), 5: (add(1,3), ['sum3']), 6: (mul(4,4), ['prod']), 7: (mul(4,5), ['prod'])}
        """
        # print("---------- RETURNED TABLE -------------")
        # print(return_table)
        final_instr_list = table_to_prog(return_table)

        final_instr_list.append(final_instr)
        return_prog = {
            "functions": [
                {
                    "instrs": final_instr_list,
                    "name" : "main"
                }
            ],
            
        }
    else:
        return_prog = prog
        # print(return_prog)
        
    
    json.dump(return_prog, sys.stdout, indent=2)
