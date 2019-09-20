#!usr/bin/env python

class PString:

    def __init__(self, s = "", form = "string"):
        self.pstring = s[1:-1]
        self.plines = []
        if form == "string":
            self.tab = "\\t"
            self.nl = "\\n"
        else:
            self.tab = '\t'
            self.nl = '\n'

    def parsestring(self):
        lines = self.pstring.split(self.nl)
        funcbegin = False
        for line in lines:
            pline = self.parseline(line)
            if pline["type"] == "def":
                funcbegin = True
            if funcbegin and pline["type"] != "empty" and pline["type"] != "error":
                self.plines.append(pline)
        return self.plines

    def parseline(self, line):
        level, i = 0, 0
        while i + 1 < len(line) and line[i:i+2] == self.tab:
            level += 1
            i += 2
        typ = "empty"
        if i < len(line) and line[i] == ' ':
            print("Error: detected a space for indentation.")
            print(line)
            typ = "error"
        elif i + 3 < len(line) and line[i:i+4] == "def " and line[-1] == ':':
            typ = "def"
        elif i + 2 < len(line) and line[i:i+3] == "if ":
            typ = "if"
        elif i + 6 < len(line) and line[i:i+7] == "return ":
            typ = "return"
        elif i < len(line) and (line[i].isalpha() or line[i] == '_'):
            typ = "expr"
        return {"level": level, "type": typ, "content": line[i:]}
