#!usr/bin/env python

class PString:

    def __init__(self, s = ""):
        self.pstring = s[1:-1]
        self.plines = []

    def parsestring(self):
        lines = self.pstring.split("\\n")
        for line in lines:
            pline = self.parseline(line)
            if pline["type"] != "empty" and pline["type"] != "error":
                self.plines.append(pline)
        return self.plines

    def parseline(self, line):
        level, i = 0, 0
        while i + 1 < len(line) and line[i:i+2] == '\\t':
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
