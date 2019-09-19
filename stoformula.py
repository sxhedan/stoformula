#!/usr/bin/env python

import sys
import z3

def stoformula(s):
    print("Converting string %s to a formula..." % s)
    s = s[1:-1]
    lines = s.split("\\n")
    funcstart = False
    var = {}
    for line in lines:
        if not line:
            continue
        elif "return" in line:
            ans = calstring(line[line.find("return")+6:], var)
            return ans
        elif funcstart:
            parseline(line, var)
        elif line.startswith("def "):   # maybe '\t' before def?    TODO
            # only one "def" allow? TODO
            funcstart = True
            parsehead(line, var)
    return 0

def getvname(s, i):
    # get a variable
    ibegin = i
    while ibegin < len(s) and s[ibegin] != '_' and not s[ibegin].isalpha():
        if s[ibegin] == '\\':
            ibegin += 2
        else:
            ibegin += 1
    if ibegin == len(s):
        print("Failed to get the name of variable.")
        return ["", ibegin]
    iend = ibegin
    while iend < len(s) and (s[iend].isalnum() or s[iend] == '_'):
        iend += 1
    return [s[ibegin:iend], iend]

def parsehead(line, v):
    i = 4
    while i < len(line) and line[i] != '(':
        i += 1
    vname, i = getvname(line, i)
    v[vname] = z3.Int(vname)
    vname, i = getvname(line, i)
    v[vname] = z3.Int(vname)
    return

def parseline(line, v):
    if '=' not in line:
        return
    i = 0
    # left head side
    v0, i = getvname(line, i)
    # right head side
    while i < len(line) and line[i] == ' ':
        i += 1
    if line[i] == '=':
        if i + 1 == len(line) or line[i+1] == '=':
            return
        rhs = line[i+1:]
    else:
        ieq = line.find('=', i, -1)
        rhs = v0 + line[i:ieq] + '(' + line[ieq+1:] + ')'
    v[v0] = calstring(rhs, v)
    return

def getelement(s, i):
    # get a variable or a number or an operator
    # return [element, type, index]
    ibegin = i
    while ibegin < len(s) and s[ibegin] == ' ':
        ibegin += 1
    if ibegin == len(s):
        return [None, None, None]
    if s[ibegin].isalpha() or s[ibegin] == '_':
        # variable
        vname, i = getvname(s, ibegin)
        return [vname, "variable", i]
    elif s[ibegin].isdigit():
        # number
        iend = ibegin
        while iend < len(s) and s[iend].isdigit():
            iend += 1
        return [int(s[ibegin:iend]), "number", iend]
    elif s[ibegin] == '(' or s[ibegin] == ')':
        # '(' or ')'
        return [s[ibegin], "bracket", ibegin+1]
    else:
        # operator
        if s[ibegin] == '+' or s[ibegin] == '-':
            # + or -
            sign = 1
            iend = ibegin
            while iend < len(s) and (s[iend] == '+' or s[iend] == '-'):
                if s[iend] == '-':
                    sign *= -1
                iend += 1
            if sign == 1:
                return ['+', "operator", iend]
            else:
                return ['-', "operator", iend]
        elif s[ibegin] == '*':
            # * or **
            if ibegin + 1 < len(s) and s[ibegin+1] == '*':
                return ["**", "operator", ibegin+2]
            else:
                return ['*', "operator", ibegin+1]
        elif s[ibegin] == '/':
            # / or //
            if ibegin + 1 < len(s) and s[ibegin+1] == '/':
                return ['/', "operator", ibegin+2]
            else:
                return ['/', "operator", ibegin+1]
        elif s[ibegin] == '%':
            # %
            return ['%', "operator", ibegin+1]
        else:
            print("Operator %s is not implemented yet." % s[ibegin])
    return [None, None, None]

def calstring(s, v):
    """
    Operators currently allowed:
    **
    * / % //
    + - 
    To be considered:
    bitwise operators
    comparisons
    """
    prt = {"**": -1, '*': -2, '/': -2, '%': -2, '+': -3, '-': -3}
    stack = []
    ans, i = 0, 0
    while i < len(s):
        elem, typ, i = getelement(s, i)
        if typ == "operator":
            while len(stack) >= 3 and isvalidexpr(stack[-3:]) and prt[elem] <= prt[stack[-2][0]]:
                n2 = stack.pop()[0]
                op = stack.pop()[0]
                n1 = stack.pop()[0]
                #stack.append([cal2n(n1, op, n2), "number"])
                pushnum(stack, cal2n(n1, op, n2))
            stack.append([elem, typ])
        elif typ == "variable" or typ == "number":
            if typ == "variable":
                elem = v[elem]
            # if there's a sign at the top of stack TODO
            #stack.append([elem, "number"])
            pushnum(stack, elem)
        elif elem == ')':
            if not calbracket(stack):
                return 0
        else:
            stack.append([elem, typ])
    # Now stack should not have any brackets.
    # Calculate from top to bottom
    while len(stack) >= 3:
        if not isvalidexpr(stack[-3:]):
            print("Error in calstring(), stack:")
            print(stack)
            return 0
        n2 = stack.pop()[0]
        op = stack.pop()[0]
        n1 = stack.pop()[0]
        #stack.append([cal2n(n1, op, n2), "number"])
        pushnum(stack, cal2n(n1, op, n2))
    if len(stack) != 1:
        print("Error in calstring(), stack:")
        print(stack)
        return 0
    return z3.simplify(stack[0][0])

def isvalidexpr(st):
    return st[-1][1] == "number" and st[-2][1] == "operator" and st[-3][1] == "number"

def pushnum(st, num):
    # check sign
    # If len(st) == 1, st[0][0] is a sign if it is '+' or '-'.
    # If len(st) >= 2, st[-1][0] is a sign if it is '+' or '-' and st[-2][1] is not "number".
    # Cases like "+--++-+-" are considered when we push operators, so it will not happen.
    if len(st) == 1 and (st[0][0] == '+' or st[0][0] == '-'):
        if st[0][0] == '-':
            num = -num
        st.pop()
    if len(st) >= 2 and (st[-1][0] == '+' or st[-1][0] == '-') and st[-2][1] != "number":
        if st[-1][0] == '-':
            num = -num
        st.pop()
    st.append([num, "number"])

def calbracket(st):
    ibegin = len(st) - 1
    while ibegin >= 0 and st[ibegin][1] != "bracket":
        ibegin -= 1
    if ibegin < 0:
        print("Error in calbracket(), stack:")
        print(st)
        return 0
    while len(st) - ibegin >= 4:
        if not isvalidexpr(st[-3:]):
            print("Error in calbracket(), stack:")
            print(st)
            return 0
        n2 = st.pop()[0]
        op = st.pop()[0]
        n1 = st.pop()[0]
        #st.append([cal2n(n1, op, n2), "number"])
        pushnum(st, cal2n(n1, op, n2))
    if (len(st)) - ibegin != 2:
        print("Error in calbracket(), stack:")
        print(st)
        return 0
    tmp = st.pop()
    st.pop()
    #st.append(tmp)
    pushnum(st, tmp[0])
    return 1

def cal2n(n1, op, n2):
    if op == '+':
        return n1 + n2
    elif op == '-':
        return n1 - n2
    elif op == '*':
        return n1 * n2
    elif op == '/':
        return n1 / n2
    elif op == '%':
        return n1 % n2
    elif op == '**':
        return n1**n2
    else:
        print("Operator %s is not implemented yet." % op)
    return 0

def main(argv):
    print("==========================================================")
    print("Notes:")
    print("1) Only the first line in the input file will be read.")
    print("2) The line should start and end with \'\"\'.")
    print("3) '/' in Python and '/' in Python3 are different.")
    print("==========================================================")
    try:
        with open(argv[0], 'r') as f:
            print("Reading file %s..." % argv[0])
            pstring = f.readline()[:-1]
        # if not read from a file   TODO
        formula = stoformula(pstring)
        print("Formula in the code:")
        print(formula)
    except:
        print("Failed to convert the string to a formula.")
    return

if __name__ == "__main__":
    main(sys.argv[1:])

