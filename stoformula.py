#!/usr/bin/env python3

import sys
import z3
from pstring import PString
from expr import Expr

def main(argv):
    print("===============================================================")
    print("Notes:")
    print("1) Only the first line in the input file will be read.")
    print("2) The line should start and end with \'\"\'.")
    print("3) '/' in Python and '/' in Python3 are different fot int.")
    print("===============================================================")
    """
    try:
        with open(argv[0], 'r') as f:
            print("Reading file %s..." % argv[0])
            pstring = f.readline()[:-1]
        # if not read from a file   TODO
        formula = stoformula(pstring)
        print("Formula of the function:")
        print(formula)
    except:
        print("Failed to convert the string to a formula.")
    """
    with open(argv[0], 'r') as f:
        print("Reading file %s..." % argv[0])
        instr = f.read()
    print("Converting string %s to a formula..." % instr)
    pstr = PString(instr, "file")
    plines = pstr.parsestring()
    expr = Expr(plines)
    formula = expr.formula()
    print("Formula for the string:")
    print(formula)
    return

if __name__ == "__main__":
    main(sys.argv[1:])

