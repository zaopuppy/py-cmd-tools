#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'zaopuppy'


import sys
import re
import getopt

import os.path


try:
    import readline
except ImportError:
    readline = None
    print("warn: cant find readline")


if sys.version_info.major != 3:
    print("python 3.x needed")
    quit(-1)


def usage():
    print("""
    <grep> <pattern> files
    """)


def main():
    optlist, args = getopt.getopt(sys.argv[1:], "i", "ignore-case=")

    if len(args) <= 0:
        usage()
        return 1

    flag = 0
    for o, a, in optlist:
        if o == "-i":
            flag |= re.IGNORECASE

    pattern = args[0]
    file_list = args[1:]
    max_len = 4096

    prog = re.compile(pattern, flag)

    if len(file_list) <= 0:
        # don't use input(), or we can't get input from pipe in win32 platform(works fine under Mac OS, though)
        for line in iter(lambda: sys.stdin.readline(max_len), ''):
            if prog.search(line):
                print(line, end='')
    else:
        for f in file_list:
            if not os.path.isfile(f):
                print("{}: not a file".format(f))
                continue
            try:
                with open(f, "rb") as fp:
                    # _io.BufferedReader
                    for no, line in enumerate(iter(lambda: fp.readline(max_len), b'')):
                        # TODO: separate binary file and text file
                        line = line.decode()
                        if prog.search(line):
                            # win32 needs this `end=''`, but linux/mac doesn't
                            print("{}:{}: {}".format(f, no, line), end='')
            except Exception as e:
                print(e)


if __name__ == "__main__":
    main()

