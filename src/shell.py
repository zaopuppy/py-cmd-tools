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

from functools import reduce

import plyplus
from plyplus.strees import STree


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


def extract_string(s):
    if s.head != "string":
        return None
    return unescape_string(s.tail[0])


def extract_redirect_in(redirect):
    if redirect.head != "redirect_in":
        return None
    return extract_string(redirect.tail[0])


def extract_redirect_out(redirect):
    if redirect.head != "redirect_out":
        return None
    return extract_string(redirect.tail[0])


def extract_cmd_args(cmd):
    if cmd.head != "cmd":
        return []

    args = [extract_string(y) for y in filter(lambda x: x.head == "string", cmd.tail)]

    redirect_in_list = tuple(filter(lambda x: x.head == "redirect_in", cmd.tail))
    if len(redirect_in_list) == 0:
        redirect_in = None
    elif len(redirect_in_list) == 1:
        redirect_in = extract_redirect_in(redirect_in_list[0])
    else:
        raise Exception("obscure redirection(in)")

    redirect_out_list = tuple(filter(lambda x: x.head == "redirect_out", cmd.tail))
    if len(redirect_out_list) == 0:
        redirect_out = None
    elif len(redirect_out_list) == 1:
        redirect_out = extract_redirect_out(redirect_out_list[0])
    else:
        raise Exception("obscure redirection(out)")

    return Command(args, redirect_in=redirect_in, redirect_out=redirect_out)


def extract_cmd_list(ast):
    if ast.head != "start":
        return []
    return list(map(extract_cmd_args, filter(lambda x: x.head == "cmd", ast.tail)))


class Command:
    def __init__(self, args, redirect_in=None, redirect_out=None):
        self.args = args
        self.redirect_in = redirect_in
        self.redirect_out = redirect_out


class ExecuteTree:
    def __init__(self, ast):
        self.cmd_list = extract_cmd_list(ast)
        self.background = ast.tail[-1].head == "bg_flag"


class BuiltIn:
    """
    Base class for all built-in commands. Setting up pipelines, supplying basic input/output functions for subclasses.
    """

    PIPE = -1

    def __init__(self, shell, args, stdin=None, stdout=None, stderr=None):
        self.shell = shell
        self.args = args

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
        # self.shell.cwd = os.getcwd()


class Exit(BuiltIn):
    def execute(self):
        self.shell.is_running = False


class Which(BuiltIn):
    def execute(self):
        pathlist = self.shell.paths

        sts = 0

        for prog in self.args[1:]:
            ident = ()
            for dir in pathlist:
                filename = os.path.join(dir, prog)
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
                        if not ident:
                            print(filename)
                            ident = st[:3]
                        else:
                            if st[:3] == ident:
                                s = 'same as: '
                            else:
                                s = 'also: '
                            self.error(s + filename)
                    else:
                        self.error(filename + ': not executable')
            if not ident:
                self.error(prog + ': not found')
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
        if f.startswith(basename):
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
    def __init__(self, **env):
        if "PWD" not in env:
            env["PWD"] = os.getcwd()
        if "PS1" not in env:
            env["PS1"] = "$ "
        if "PS2" not in env:
            env["PS2"] = ".. "

        self.env = env

        # self.cwd = env.get("PWD")
        self.ps1 = env.get("PS1")
        self.ps2 = env.get("PS2")
        self.paths = env.get("PATH", [])

        self.is_running = False
        # use RB-Tree instead of normal map, we need auto-complete
        # TODO: self.cmd_map = [] -> "path" -> [ "cmd.exe", "fde.dll" ]
        self.cmd_map = {}
        self.errno = 0
        self.parser = plyplus.Grammar(open("bash.g"))
        # TODO: don't save commands in relative paths
        self.load_script_in_path(self.paths)
        self.builtin = {
            'cd': Cd,
            'exit': Exit,
            'help': Help,
            'test': Test,
            'which': Which,
        }

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
                except Exception:
                    print()
                    break

                if not line:
                    continue

                if len(line.strip()) == 0:
                    continue

                # parse input
                ast = self.parser.parse(line)

                # create execute tree and execute it
                self.execute(ExecuteTree(self.expand(ast)[0]))

            except plyplus.TokenizeError as tokenizeError:
                print(tokenizeError)
                continue
            except KeyboardInterrupt:
                print("^C")
                continue
            except Exception as e:
                print(e)
                continue

    def execute(self, exe_tree):
        if exe_tree.background:
            # FIXME: not good, use sub-process instead of thread
            thread = threading.Thread(target=self.execute_commands_in_thread, daemon=True, args=[exe_tree.cmd_list])
            thread.start()
        else:
            self.execute_commands(exe_tree.cmd_list)

    def execute_commands_in_thread(self, *args):
        """
        wrapper for execution in thread
        :param args: arguments for `execute_commands`
        :return: None
        """
        self.execute_commands(*args)
        print("[[done]]")

    def execute_commands(self, cmd_list):
        """
        create sub-processes, pipe them together, then execute them in parallel
        :param cmd_list: command list
        :return: None
        """
        process_list = []
        last_out = None
        next_in = subprocess.PIPE
        # if redirection exists, pipe fd won't be closed, that's a problem
        for idx, cmd in enumerate(cmd_list):
            if cmd.redirect_in is not None:
                last_out = io.TextIOWrapper(io.open(cmd.redirect_in, "rb", -1))
            if cmd.redirect_out is not None:
                next_in = io.TextIOWrapper(io.open(cmd.redirect_out, "wb", -1))
            elif idx >= len(cmd_list) - 1:
                # the last command of pipeline
                next_in = None
            p = self.create_subprocess(cmd.args, stdin=last_out, stdout=next_in)
            process_list.append(p)
            if cmd.redirect_out is not None:
                last_out = subprocess.DEVNULL
            else:
                last_out = p.stdout
            next_in = subprocess.PIPE

        process_list[-1].communicate()

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
        """
        expand shell input string
        :param ast:
        :return:
        """
        if not isinstance(ast, STree):
            return [ast]
        if ast.head == "string":
            if ast.tail[0][0] not in "\"'":
                return list(map(
                    lambda _: STree("string", [_]),
                    self.expand_string(ast.tail[0])))
            else:
                return [ast]
        else:
            ast.tail = reduce(
                lambda x, y: x + y,
                map(self.expand, ast.tail)
            )
            return [ast]

    def expand_string(self, s):
        """
        a very simple and (also) very buggy implementation... :(
        :param s:
        :return:
        """
        # TODO: complete this method
        if not self.errno:
            self.errno = 0
        s = s.replace('$?', str(self.errno))
        if s == '*':
            return os.listdir(os.getcwd())
        else:
            return [s]


def main():
    path = [os.path.abspath(os.path.dirname(sys.argv[0]))] + os.getenv("PATH").split(os.path.pathsep)
    sh = Shell(PATH=path)
    if len(sys.argv) <= 1:
        print("py-pseudo-shell")
        print()
        sh.run()
    else:
        # execute script
        raise Exception("Not implemented")


if __name__ == "__main__":
    main()
