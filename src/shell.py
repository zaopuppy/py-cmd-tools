#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple pseudo shell, designed as a environment for executing py-cmd-tools.

This program can execute both platform executable files and python scripts.

By Yi Zhao 1/15/2015

"""

__author__ = "Yi Zhao"


import io
import os
import os.path
import subprocess
import sys
import threading
import stat

import internal.parser

from functools import reduce

try:
    import readline
except ImportError:
    readline = None
    print("warn: cant find readline")


if sys.version_info.major != 3:
    print("python 3.x needed")
    quit(-1)


def unescape_dbl_quo_string(s):
    result = ""
    escaping = False
    for idx, c in enumerate(s):
        if not escaping:
            if c == '\\':
                escaping = True
            else:
                result += c
        else:
            escaping = False
            if c == '\\':
                result += '\\'
            elif c == 'a':
                # TODO: ascii bell
                result += '\a'
            elif c == 'b':
                result += '\b'
            elif c == 'f':
                result += '\f'
            elif c == 'n':
                result += '\n'
            elif c == 'r':
                result += '\r'
            elif c == 't':
                result += '\t'
            elif c == 'v':
                result += '\v'
            elif c == '"':
                result += '"'
            elif c == "'":
                result += "'"
            else:
                # bad escaping character, ignore escape character
                result += '\\'
                result += c
    return result


def unescape_quo_string(s):
    return unescape_dbl_quo_string(s)


def unescape_string(s):
    if s.startswith('"'):
        return unescape_dbl_quo_string(s[1:-1])
    elif s.startswith("'"):
        return unescape_quo_string(s[1:-1])
    else:
        return s


class BuiltIn:
    """
    Base class for all built-in commands. Setting up pipelines, supplying basic input/output functions for subclasses.
    """

    PIPE = -1

    def __init__(self, shell, args, stdin=None, stdout=None, stderr=None):
        self.shell = shell
        self.args = args
        self.returncode = 0

        # setup pipelines
        if stdin == BuiltIn.PIPE:
            pipe_in, pipe_out = os.pipe()
            # FIXME: should not use TextIOWrapper, or program like `zcat` will fail
            self.stdin_read = io.TextIOWrapper(io.open(pipe_in, "rb", -1))
            self.stdin = io.TextIOWrapper(io.open(pipe_out, "wb", -1))
        elif stdin is None:
            self.stdin_read, self.stdin = sys.stdin, None
        else:
            self.stdin_read, self.stdin = stdin, None

        if stdout == BuiltIn.PIPE:
            pipe_in, pipe_out = os.pipe()
            self.stdout = io.TextIOWrapper(io.open(pipe_in, "rb", -1))
            self.stdout_write = io.TextIOWrapper(io.open(pipe_out, "wb", -1))
        elif stdout is None:
            self.stdout, self.stdout_write = None, sys.stdout
        else:
            self.stdout, self.stdout_write = None, stdout

        if stderr == BuiltIn.PIPE:
            pipe_in, pipe_out = os.pipe()
            self.stderr = io.TextIOWrapper(io.open(pipe_in, "rb", -1))
            self.stderr_write = io.TextIOWrapper(io.open(pipe_out, "wb", -1))
        elif stderr is None:
            self.stderr, self.stderr_write = None, sys.stderr
        else:
            self.stderr, self.stderr_write = None, stderr

        self.thread = threading.Thread(target=self.thread_run, daemon=True)
        self.thread.start()

    def thread_run(self):
        self.execute()
        if self.stdin_read is not None and self.stdin_read is not sys.stdin:
            self.stdin_read.close()
        if self.stdout_write is not None and self.stdout_write is not sys.stdout:
            self.stdout_write.close()
        if self.stderr_write is not None and self.stderr_write is not sys.stderr:
            self.stderr_write.close()

    def execute(self):
        self.print("NotImplementedError")

    def communicate(self):
        self.thread.join()
        for f in filter(lambda _: _ is not None,
                        (self.stdin, self.stdout, self.stderr)):
            f.close()

    def print(self, msg, end='\n', flush=True):
        if not isinstance(msg, str):
            msg = str(msg)
        self.stdout_write.write(msg + end)
        if flush:
            self.stdout_write.flush()

    def error(self, msg, end='\n', flush=True):
        if not isinstance(msg, str):
            msg = str(msg)
        self.stderr_write.write(msg + end)
        if flush:
            self.stderr_write.flush()

    def input(self, prompt=''):
        self.stdout_write.write(prompt)
        self.stdout_write.flush()
        return self.stdin_read.readline(2048)


class Cd(BuiltIn):
    def execute(self):
        if len(self.args) <= 1:
            # do nothing
            return
        os.chdir(self.args[1])


class Exit(BuiltIn):
    def execute(self):
        self.shell.is_running = False


class Which(BuiltIn):
    def execute(self):
        path_list = self.shell.paths

        sts = 0

        for f in self.args[1:]:
            identity = ()
            for d in path_list:
                filename = os.path.join(d, f)
                # check `.py` file first
                try:
                    st = os.stat(filename + '.py')
                    filename += '.py'
                except OSError:
                    try:
                        st = os.stat(filename)
                    except OSError:
                        continue
                if not stat.S_ISREG(st[stat.ST_MODE]):
                    self.error(filename + ': not a disk file')
                else:
                    mode = stat.S_IMODE(st[stat.ST_MODE])
                    if mode & 0o111:
                        if not identity:
                            print(filename)
                            identity = st[:3]
                        else:
                            if st[:3] == identity:
                                s = 'same as: '
                            else:
                                s = 'also: '
                            self.error(s + filename)
                    else:
                        self.error(filename + ': not executable')
            if not identity:
                self.error(f + ': not found')
                sts = 1

        return sts


class Help(BuiltIn):
    """
    Print all command files in PATH. Optionally accept a regular expression
    parameter, which can be used for filtering output.
    """
    def execute(self):
        if len(self.args) > 1:
            match = self.args[1]
        else:
            match = None
        for k, v in self.shell.cmd_map.items():
            if match is not None:
                # FIXME: may cause performance issue if there are too many execute files in paths
                cmd_list = tuple(filter(lambda x: match in x, v))
                if len(cmd_list) > 0:
                    self.print('[' + k + ']')
                    for f in cmd_list:
                        print(f)
                    print()
            else:
                self.print('[' + k + ']')
                for i in v:
                    print(i)
                print()


class Test(BuiltIn):
    def execute(self):
        line = self.input('test> ')
        self.print("your input: " + line)


def setup_readline():
    """
    setup readline if readline is installed
    :return:
    """
    if not readline:
        return
    readline.parse_and_bind("tab: complete")
    readline.set_completer(file_name_completer)
    # ' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>/?'
    readline.set_completer_delims(" \t\n")


def file_name_completer(text, index):
    """
    a simple completer for testing only
    :param text:
    :param index:
    :return: the n'th candidate string
    """
    # print(text, index)
    dirname = os.path.dirname(text)
    if dirname != '' and not os.path.isdir(dirname):
        return None
    basename = os.path.basename(text)
    matches = []
    for f in os.listdir(dirname if dirname != '' else '.'):
        if f.lower().startswith(basename.lower()):
            p = os.path.join(dirname, f)
            if os.path.isdir(p):
                matches.append(os.path.join(p, ''))
            else:
                matches.append(p)
    if index > len(matches) - 1:
        return None
    return matches[index]


# TODO: support background('&', 'bg', 'jobs')
# TODO: support redirection
# TODO: support script
# TODO: auto complete
# TODO: alias
# TODO: input/output recording
class Shell:
    """
    """
    LINE_BUF_SIZE = 2048

    if sys.platform == "win32":
        PYTHON_PATH = "D:\\Python34\\python.exe"
    else:
        PYTHON_PATH = "/usr/local/bin/python3"

    # def __init__(self, cwd=None, ps1="$ ", ps2=".. ", path=[]):
    def __init__(self, basedir, path=(), ps1='$ ', ps2=' > ', debug=False):
        # self.cwd = env.get("PWD")
        self.ps1 = ps1
        self.ps2 = ps2
        self.paths = [basedir] + list(path)
        if basedir is not None:
            self.basedir = basedir
        else:
            self.basedir = os.getcwd()

        self.debug = debug
        self.is_running = False
        # use RB-Tree instead of normal map, we need auto-complete
        # TODO: self.cmd_map = [] -> "path" -> [ "cmd.exe", "fde.dll" ]
        self.cmd_map = {}
        self.errno = 0
        # TODO: don't save commands in relative paths
        self.load_script_in_path(self.paths)
        self.builtin = {
            'cd': Cd,
            'exit': Exit,
            'help': Help,
            '.test': Test,
            'which': Which,
        }

        self.lexer = internal.parser.BashLexer(debug=self.debug)
        self.parser = internal.parser.BashParser(context=self, lexer=self.lexer.lexer, debug=self.debug)

        setup_readline()

    def load_script_in_path(self, paths):
        for p in paths:
            self.cmd_map[p] = []
            for f in os.listdir(p):
                self.cmd_map[p].append(f)

    def run(self):
        # interactive mode
        self.is_running = True
        while self.is_running:
            try:
                try:
                    line = input('[' + os.getcwd() + ']' + self.ps1)
                except Exception as e:
                    print(e)
                    break

                if not line:
                    continue

                line = line.strip()
                if len(line) == 0:
                    continue

                # parse input
                ast = self.parser.parse(
                    input=(line + '\n'),
                    debug=self.debug,
                    lexer=self.lexer.lexer,
                    tokenfunc=self.lexer.token_func)

                if not ast:
                    print("Bad syntax")
                    continue

                ast.accept(self.expand)
                self.errno = self.execute(ast)

            except KeyboardInterrupt:
                print("^C")
                continue
            # except Exception as e:
            #     print(e)
            #     continue

    def prompt_input(self):
        self.lexer.lexer.input(input(self.ps2))

    # There's no multi-methods/multi-dispatching in Python, so it needs
    # a little effort to make it available
    #
    # Creator's solution
    # http://www.artima.com/weblogs/viewpost.jsp?thread=101605
    def execute(self, tree):
        # I really need a good solution, but didn't find it yet.
        if isinstance(tree, internal.parser.Background):
            return self.execute_background(tree)
        elif isinstance(tree, internal.parser.And):
            return self.execute_and(tree)
        elif isinstance(tree, internal.parser.Or):
            return self.execute_or(tree)
        elif isinstance(tree, internal.parser.Pipe):
            return self.execute_pipe(tree)
        elif isinstance(tree, internal.parser.SequenceCommandList):
            return self.execute_sequence_command_list(tree)
        elif isinstance(tree, internal.parser.Command):
            return self.execute_command(tree)
        else:
            raise Exception("Unknown element: " + str(tree))

    def execute_sequence_command_list(self, tree):
        return tuple(map(self.execute, tree.command_list))[-1]

    def execute_command(self, tree):
        return self.execute_pipe_internal((tree,))

    # FIXME: not good, use sub-process instead of thread
    def execute_background(self, tree):
        thread = threading.Thread(target=self.execute, daemon=True, args=[tree.command])
        thread.start()
        return 0

    def execute_and(self, tree):
        rv = self.execute(tree.left)
        if rv != 0:
            return rv
        return self.execute(tree.right)

    def execute_or(self, tree):
        rv = self.execute(tree.left)
        if rv == 0:
            return rv
        return self.execute(tree.right)

    def execute_pipe(self, tree):
        return self.execute_pipe_internal(tree.command_list, tree.flags)

    def execute_pipe_internal(self, command_list, flags=0):
        try:
            process_list = []
            last_out = None
            next_in = subprocess.PIPE
            # if redirection exists, pipe fd won't be closed, that's a problem
            for idx, cmd in enumerate(command_list):
                if cmd.redirect_in is not None:
                    last_out = io.TextIOWrapper(io.open(cmd.redirect_in.file_name, "rb", -1))
                if cmd.redirect_out is not None:
                    next_in = io.TextIOWrapper(io.open(cmd.redirect_out.file_name, "wb", -1))
                elif idx >= len(command_list) - 1:
                    # the last command of pipeline
                    next_in = None
                arg_list = self.normalize_arguments(cmd.arg_list)
                p = self.create_subprocess(arg_list, stdin=last_out, stdout=next_in)
                process_list.append(p)
                if cmd.redirect_out is not None:
                    last_out = subprocess.DEVNULL
                else:
                    last_out = p.stdout
                next_in = subprocess.PIPE

            process_list[-1].communicate()
        finally:
            if flags & internal.parser.FLAG_TIME_PIPE_LINE:
                # TODO
                print()
                print("real    0m0.062s")
                print("user    0m0.000s")
                print("sys     0m0.046s")
                print("(Oh... `time` is not supported...:P)")

        if flags & internal.parser.FLAG_INVERT_RETURN:
            if process_list[-1].returncode:
                return 0
            else:
                return 1
        else:
            return process_list[-1].returncode

    def find_cmd_in_paths(self, cmd):
        if os.path.isabs(cmd):
            try:
                os.stat(cmd)
                return cmd
            except FileNotFoundError:
                return None

        for path, cmd_list in self.cmd_map.items():
            if cmd in cmd_list:
                return os.path.join(path, cmd)
            elif cmd + ".py" in cmd_list:
                return os.path.join(path, cmd + ".py")
            elif cmd + ".exe" in cmd_list:
                return os.path.join(path, cmd + ".exe")
            else:
                pass
        return None

    def is_builtin(self, cmd):
        return cmd in self.builtin.keys()

    def create_subprocess(self, args, stdin=None, stdout=None, stderr=None):
        cmd = args[0]
        if self.is_builtin(cmd):
            cmd_type = self.builtin.get(cmd)
            process = cmd_type(self, args, stdin=stdin, stdout=stdout, stderr=stderr)
        else:
            full_path = self.find_cmd_in_paths(cmd)
            if not full_path:
                raise Exception("[{}]: No such command or file".format(cmd))
            if full_path.endswith(".py"):
                process = subprocess.Popen(
                    [self.PYTHON_PATH, full_path] + args[1:], stdin=stdin, stdout=stdout, stderr=stderr)
            else:
                process = subprocess.Popen(
                    [full_path, ] + args[1:], stdin=stdin, stdout=stdout, stderr=stderr)

        return process

    def expand(self, ast):
        if isinstance(ast, internal.parser.Command):
            ast.arg_list = reduce(lambda _, __: _ + __,
                                  map(lambda s: self.expand_string(s),
                                      ast.arg_list),
                                  [])

    def expand_string(self, s):
        """
        a very simple and (also) very buggy implementation... :(
        """
        # TODO: complete this method

        if not self.errno:
            self.errno = 0
        s = s.replace('$?', str(self.errno))
        if s == '*':
            return os.listdir(os.getcwd())
        else:
            return [s]

    def normalize_arguments(self, arg_list):
        return reduce(
            lambda _, __: _ + __,
            map(
                lambda _: [unescape_string(_)] if _.startswith('"') or _.startswith("'") else self.expand_string(_),
                arg_list)
        )


def main():
    path = os.getenv("PATH").split(os.path.pathsep)
    sh = Shell(basedir=os.path.abspath(os.path.dirname(sys.argv[0])), path=path, debug=True)
    if len(sys.argv) <= 1:
        print("py-pseudo-shell")
        print()
        sh.run()
    else:
        # execute script
        raise Exception("Not implemented")


if __name__ == "__main__":
    main()
