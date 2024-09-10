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
    
def generate_value(instr, table):
    """
    Generates the value from the instruction.
    Input: Dict{}
    Output: str?
    """
    print("table: ", table)
    arith_ops = ["add", "sub", "mul", "div"]
    if instr["op"] == "const":
        return Value(op="const", args=[instr["value"]])
    elif instr["op"] in arith_ops:
        consolidated_args = []
        for arg in instr["args"]:
            print("arg: ", arg)
            for num in table:
                var = table[num][1]
                if arg == var:
                    consolidated_args.append(num)

        return Value(op=instr["op"], args=consolidated_args)
    else:
        return None

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

                table[i] = (value, instr["dest"])
                i += 1
            
            
    
    return table

    
if __name__ == "__main__":
    # the program comes in from stdin
    prog = json.load(sys.stdin)


    return_prog = local_value_numbering(prog)
    print("returned table")
    print(return_prog)
        
    
    # json.dump(return_prog, sys.stdout, indent=2)
