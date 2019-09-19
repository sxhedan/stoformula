#! /usr/bin/env python

import z3

class Expr:

    def __init__(self, lines = []):
        self.plines = lines
        self.vars = {}

    def formula(self):
        if len(self.plines) == 0 or self.plines[0]["type"] != "def":
            print("Empty or invalid input.")
            print(self.plines)
            return 0
        if not self.parsehead():
            print("Invalid def:")
            print(self.plines[0]["content"])
            return 0
        level = self.plines[0]["level"]
        i = 1
        while i < len(self.plines):
            line = self.plines[i]
            if line["type"] == "return":
                return self.calstring(line["content"][6:]) #TODO
            if line["type"] == "if":
                print("if statement to be implemented.")    # TODO
                pass
            else:
                self.parseexpr(line["content"])
            i += 1
        print("Error: can't locate return.")
        return 0

    def parseexpr(self, line):
        if '=' not in line:
            return
        i = 0
        # left hand side
        # x, y = y, x   FIXME
        v0, i = self.getvname(line, i)
        if not v0:
            return
        # right hand side
        while i < len(line) and line[i] == ' ':
            i += 1
        if line[i] == '=':
            if i + 1 == len(line) or line[i+1] == '=':
                return
            rhs = line[i+1:]
        else:
            ieq = line.find('=', i)
            rhs = v0 + line[i:ieq] + '(' + line[ieq+1:] + ')'
        self.vars[v0] = self.calstring(rhs)
        return

    def calstring(self, s):
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
            elem, typ, i = self.getelement(s, i)
            if typ == "operator":
                while len(stack) >= 3 and self.isvalidexpr(stack[-3:]) and prt[elem] <= prt[stack[-2][0]]:
                    n2 = stack.pop()[0]
                    op = stack.pop()[0]
                    n1 = stack.pop()[0]
                    self.pushnum(stack, self.cal2n(n1, op, n2))
                stack.append([elem, typ])
            elif typ == "variable" or typ == "number":
                if typ == "variable":
                    elem = self.vars[elem]
                self.pushnum(stack, elem)
            elif elem == ')':
                if not self.calbracket(stack):
                    return 0
            else:
                stack.append([elem, typ])
        # Now stack should not have any brackets.
        # Calculate from top to bottom
        while len(stack) >= 3:
            if not self.isvalidexpr(stack[-3:]):
                print("Error in calstring(), stack:")
                print(stack)
                return 0
            n2 = stack.pop()[0]
            op = stack.pop()[0]
            n1 = stack.pop()[0]
            self.pushnum(stack, self.cal2n(n1, op, n2))
        if len(stack) != 1:
            print("Error in calstring(), stack:")
            print(stack)
            return 0
        return z3.simplify(stack[0][0])

    def calbracket(self, st):
        ibegin = len(st) - 1
        while ibegin >= 0 and st[ibegin][1] != "bracket":
            ibegin -= 1
        if ibegin < 0:
            print("Error in calbracket(), stack:")
            print(st)
            return 0
        while len(st) - ibegin >= 4:
            if not self.isvalidexpr(st[-3:]):
                print("Error in calbracket(), stack:")
                print(st)
                return 0
            n2 = st.pop()[0]
            op = st.pop()[0]
            n1 = st.pop()[0]
            self.pushnum(st, self.cal2n(n1, op, n2))
        if (len(st)) - ibegin != 2:
            print("Error in calbracket(), stack:")
            print(st)
            return 0
        tmp = st.pop()
        st.pop()
        self.pushnum(st, tmp[0])
        return 1

    def pushnum(self, st, num):
        # check sign
        # If len(st) == 1, st[0][0] is a sign if it is '+' or '-'.
        # If len(st) >= 2, st[-1][0] is a sign if it is '+' or '-' and st[-2][1] is not "number".
        # Cases like "+--++-+-" are considered when we push operators, so it will not happen.
        if len(st) == 1 and (st[0][0] == '+' or st[0][0] == '-'):
            if st[0][0] == '-':
                num = -num
            st.pop()
        elif len(st) >= 2 and (st[-1][0] == '+' or st[-1][0] == '-') and st[-2][1] != "number":
            if st[-1][0] == '-':
                num = -num
            st.pop()
        st.append([num, "number"])

    def isvalidexpr(self, st):
        return st[-1][1] == "number" and st[-2][1] == "operator" and st[-3][1] == "number"

    def getelement(self, s, i):
        # get a variable or a number or an operator
        # return [element, type, index]
        ibegin = i
        while ibegin < len(s) and s[ibegin] == ' ':
            ibegin += 1
        if ibegin == len(s):
            return [None, None, None]
        if s[ibegin].isalpha() or s[ibegin] == '_':
            # variable
            vname, i = self.getvname(s, ibegin)
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

    def parsehead(self):
        line = self.plines[0]["content"]
        i = 4
        while i < len(line) and line[i] != '(':
            i += 1
        if i == len(line):
            return 0
        while i < len(line):
            vname, i = self.getvname(line, i)
            if vname:
                self.vars[vname] = z3.Int(vname)
        return 1

    def getvname(self, line, i):
        # get a variable
        ibegin = i
        while ibegin < len(line) and line[ibegin] != '_' and not line[ibegin].isalpha():
            if line[ibegin] == '\\':
                ibegin += 2
            else:
                ibegin += 1
        if ibegin == len(line):
            return ["", ibegin]
        iend = ibegin
        while iend < len(line) and (line[iend].isalnum() or line[iend] == '_'):
            iend += 1
        return [line[ibegin:iend], iend]

    def cal2n(self, n1, op, n2):
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
