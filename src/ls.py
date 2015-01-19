#!/usr/bin/env python3
# -*- coding: utf-8 -*-


__author__ = 'Yi Zhao'


import os
import os.path
import sys


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        args.append(os.getcwd())

    for arg in args:
        if not os.path.exists(arg):
            print("No such file or directory")
            continue
        if os.path.isdir(arg):
            for f in os.listdir(arg):
                print(f)
        else:
            print(arg)


if __name__ == '__main__':
    main()

