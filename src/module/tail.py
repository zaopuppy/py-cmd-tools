#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys


def usage():
    print("tail <file_name>")


def main():
    if len(sys.argv) <= 1:
        usage()
        return


if __name__ == "__main__":
    main()

