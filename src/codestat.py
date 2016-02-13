#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import os.path

from functools import reduce


if sys.version_info.major != 3:
    raise Exception("Wrong python major version")


class FileInfo():
    def __init__(self):
        pass


class TextStatisticHandler():
    def __init__(self):
        self.last_byte = None
        self.line_no = 0

    def handle(self, buf):
        self.last_byte = buf[-1]
        self.line_no = reduce(lambda x, _: x + 1,
                              filter(lambda x: x == ord('\r'), buf),
                              self.line_no)

    def end(self):
        if self.last_byte is None:
            return
        if self.last_byte not in b'\r\n':
            self.line_no += 1

    def get(self):
        info = FileInfo()
        info.line_no = self.line_no
        return info

    def dump(self):
        return self.line_no


class XmlStatisticHandler():
    def __init__(self):
        self.last_byte = None
        self.line_no = 0

    def handle(self, buf):
        self.last_byte = buf[-1]

    def end(self):
        if self.last_byte is None:
            return

    def get(self):
        info = FileInfo()
        info.line_no = self.line_no
        return info

    def dump(self):
        return self.line_no


class PythonStatisticHandler():
    def __init__(self):
        self.line_no = 0
        self.begin_of_line = True
        self.ignore_to_end = False

    def handle(self, buf):
        for b in buf:
            if b == ord('#'):
                if self.begin_of_line:
                    self.ignore_to_end = True
                    self.begin_of_line = False
            elif b == ord('\n'):
                if not self.ignore_to_end and not self.begin_of_line:
                    self.line_no += 1
                self.ignore_to_end = False
                self.begin_of_line = True
            elif b in b' \r\t':
                # begin_of_line = False
                pass
            else:
                self.begin_of_line = False

    def end(self):
        if not self.begin_of_line and not self.ignore_to_end:
            self.line_no += 1

    def get(self):
        info = FileInfo()
        info.line_no = self.line_no
        return info

    def dump(self):
        return self.line_no


class CppStatisticHandler():
    COMMENT_NONE = 0
    # "//"
    COMMENT_LINE = 1
    # "/" --+--> "//"
    # |
    #       +--> "/*"
    COMMENT_PRE = 2
    # "/* "
    COMMENT_BLOCK = 3
    # "*" --> "*/"
    COMMENT_POST_BLOCK = 4

    def __init__(self):
        self.line_no = 0
        self.comment_type = self.COMMENT_NONE
        # for skipping blank line
        self.has_code = False

    def handle(self, buf):
        for b in buf:
            # print("type: {}, b: {}".format(self.comment_type, chr(b)))
            if self.comment_type == self.COMMENT_NONE:
                if b == ord('/'):
                    self.comment_type = self.COMMENT_PRE
                elif b in b' \r\t':
                    # ignore
                    pass
                elif b == ord('\n'):
                    if self.has_code:
                        self.line_no += 1
                    self.has_code = False
                else:
                    self.has_code = True
            elif self.comment_type == self.COMMENT_LINE:
                if b == ord('\n'):
                    self.comment_type = self.COMMENT_NONE
                    self.has_code = False
            elif self.comment_type == self.COMMENT_PRE:
                if b == ord('/'):
                    self.comment_type = self.COMMENT_LINE
                elif b == ord('*'):
                    self.comment_type = self.COMMENT_BLOCK
                else:
                    if b == ord('\n'):
                        self.line_no += 1
                        self.has_code = False
                    else:
                        self.has_code = True
                    self.comment_type = self.COMMENT_NONE
            elif self.comment_type == self.COMMENT_BLOCK:
                if b == ord('*'):
                    self.comment_type = self.COMMENT_POST_BLOCK
                elif b == ord('\n'):
                    if self.has_code:
                        self.line_no += 1
                    self.has_code = False
            elif self.comment_type == self.COMMENT_POST_BLOCK:
                if b == ord('/'):
                    self.comment_type = self.COMMENT_NONE
                elif b == ord('\n'):
                    self.has_code = False
            else:
                raise Exception("Unknown comment type, something was wrong, tell me: zhaoyi.zero@gmail.com")

    def end(self):
        if self.has_code:
            self.line_no += 1

    def get(self):
        info = FileInfo()
        info.line_no = self.line_no
        return info

    def dump(self):
        return self.line_no


def statistic_text(f):
    handler = TextStatisticHandler()
    with open(f, "rb") as fp:
        for buf in iter(lambda: fp.read(1024), b''):
            handler.handle(buf)
        handler.end()
    print("{}: {}".format(f, handler.dump()))
    return handler.get()


def statistic_xml(f):
    handler = XmlStatisticHandler()
    with open(f, "rb") as fp:
        for buf in iter(lambda: fp.read(1024), b''):
            handler.handle(buf)
        handler.end()
        # handler.end()
    print("{}: {}".format(f, handler.dump()))
    return handler.get()


# doesn't support unicode file yet
def statistic_python(f):
    handler = PythonStatisticHandler()
    with open(f, "rb") as fp:
        for buf in iter(lambda: fp.read(1024), b''):
            handler.handle(buf)
        handler.end()
    print("{}: {}".format(f, handler.dump()))
    return handler.get()


def statistic_cpp(f):
    handler = CppStatisticHandler()
    with open(f, "rb") as fp:
        for buf in iter(lambda: fp.read(1024), b''):
            handler.handle(buf)
        handler.end()
    print("{}: {}".format(f, handler.dump()))
    return handler.get()


STATISTIC_HANDLERS = {
    ".py": statistic_python,
    ".cc": statistic_cpp,
    ".java": statistic_cpp,
    ".txt": statistic_text,
}


def get_type_by_file_name(file_name):
    """ all in lower cause """
    file_name = file_name.lower()
    idx = file_name.rfind(".")
    if idx >= 0:
        return file_name[idx:]
    else:
        return None


def statistic_dir(d):
    for dir_path, dir_names, file_names in os.walk(d):
        for f in file_names:
            yield statistic_file(os.path.join(dir_path, f))


def statistic_file(f):
    file_names = os.path.basename(f)
    file_type = get_type_by_file_name(file_names)
    handler = STATISTIC_HANDLERS.get(file_type, None)
    if handler is None:
        print(type(f))
        print("file [{}] (as type {}) doesn't support".format(f, file_type))
        return None
    info = handler(f)
    info.type = file_type
    return info


def statistic(f):
    stat_info = {}
    if os.path.isdir(f):
        for info in statistic_dir(f):
            if info is None:
                continue
            if info.type not in stat_info.keys():
                stat_info[info.type] = 0
            stat_info[info.type] += info.line_no
    else:
        info = statistic_file(f)
        if info is not None:
            stat_info[info.type] = info.line_no

    for item in stat_info.items():
        print("{}: {}".format(item[0], item[1]))


def main():
    args = sys.argv[1:]
    file_list = args
    # file_list = filter(lambda x: not x.startswith("--"), args)
    # opt_list = filter(lambda x: x.startswith("--"), args)
    for f in file_list:
        statistic(f)

if __name__ == "__main__":
    main()
