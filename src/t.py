#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from internal.parser import ExecuteVisitor
import internal.parser as parser
from shell import Shell


if __name__ == "__main__":
    import os
    import sys
    path = os.getenv("PATH").split(os.path.pathsep)
    sh = Shell(basedir=os.path.abspath(os.path.dirname(sys.argv[0])), path=path)

    visitor = ExecuteVisitor()
    while True:
        line = input('> ')
        if not line or len(line.strip()) == 0:
            continue
        print("input: [" + line + "]")
        ret = parser.parse(line)
        print('ret: {}'.format(visitor.visit(sh, ret)))



