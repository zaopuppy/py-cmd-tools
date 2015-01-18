#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'zaopuppy'


import sys
import re
import getopt

import os.path


try:
    import readline
except ImportError as e:
    readline = None
    print("warn: cant find readline")


if sys.version_info.major != 3:
    print("python 3.x needed")
    quit(-1)


def usage():
    print("""
    <grep> <pattern> files
    """)


def get_line(file_list, max_len=4096):
    # print("get_line")
    if len(file_list) <= 0:
        # don't use input(), or we can't get input from pipe in win32 platform(works fine under Mac OS, though)
        for line in iter(lambda: sys.stdin.readline(max_len), ''):
            # print("input: " + line)
            yield line
    else:
        for f in filter(lambda _: os.path.isfile(_), file_list):
            with open(f, "rb") as fp:
                # _io.BufferedReader
                for line in iter(lambda: fp.readline(max_len), b''):
                    # TODO: separate binary file and text file
                    yield line.decode()


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

    prog = re.compile(pattern, flag)

    for line in get_line(file_list):
        if prog.search(line):
            # win32 needs this `end=''`, but linux/mac doesn't
            print(line, end='')


if __name__ == "__main__":
    main()

