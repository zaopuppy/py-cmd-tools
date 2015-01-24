#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import subprocess


import ply.lex
import ply.yacc


# There's no multi-methods/multi-dispatching in Python, so it needs
# a little effort to make it available
#
# Creator's solution
# http://www.artima.com/weblogs/viewpost.jsp?thread=101605
class ExecuteVisitor:
    def __init__(self):
        pass

    def visit(self, context, tree):
        # I really need a good solution, but didn't find it yet.
        if isinstance(tree, Background):
            return self.exec_background(context, tree)
        elif isinstance(tree, And):
            return self.exec_and(context, tree)
        elif isinstance(tree, Or):
            return self.exec_or(context, tree)
        elif isinstance(tree, Pipe):
            return self.exec_pipe(context, tree)
        elif isinstance(tree, Command):
            return self.exec_command(context, tree)
        # elif isinstance(tree, RedirectionIn):
        #     return self.exec_redirect_in(context, tree)
        # elif isinstance(tree, RedirectionOut):
        #     return self.exec_redirect_out(context, tree)
        else:
            raise Exception("Unknown element")

    def exec_background(self, context, tree):
        # thread = threading.Thread(target=self.execute_commands_in_thread, daemon=True, args=[exe_tree.cmd_list])
        # thread.start()
        self.visit(context, tree)
        return 0

    def exec_and(self, context, tree):
        rv = self.visit(context, tree.left)
        if rv != 0:
            return rv
        return self.visit(context, tree.right)

    def exec_or(self, context, tree):
        rv = self.visit(context, tree.left)
        if rv == 0:
            return rv
        return self.visit(context, tree.right)

    def exec_pipe(self, context, tree):
        # for cmd in tree.command_list:
        #     self.visit(context, cmd)
        # return 0
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
        return process_list[-1].returncode

    def exec_command(self, context, tree):
        return 0

    # def exec_redirect_in(self, context, tree):
    #     pass
    #
    # def exec_redirect_out(self, context, tree):
    #     pass


class BaseElement:
    def __init__(self):
        pass


class Background(BaseElement):
    def __init__(self, command):
        BaseElement.__init__(self)
        self.command = command


class And(BaseElement):
    def __init__(self, left, right):
        BaseElement.__init__(self)
        self.left = left
        self.right = right


class Or(BaseElement):
    def __init__(self, left, right):
        BaseElement.__init__(self)
        self.left = left
        self.right = right


class Pipe(BaseElement):
    def __init__(self):
        BaseElement.__init__(self)
        self.command_list = []


class Command(BaseElement):
    def __init__(self):
        BaseElement.__init__(self)
        self.arg_list = []
        self.redirect_in = None
        self.redirect_out = None


class RedirectionIn(BaseElement):
    def __init__(self, file_name):
        BaseElement.__init__(self)
        self.file_name = file_name


class RedirectionOut(BaseElement):
    def __init__(self, file_name):
        BaseElement.__init__(self)
        self.file_name = file_name


tokens = (
    'SPACES',
    'STRING',
    'COMMENT',
    'OR',
    'AND',
    'OR_OR',
    'AND_AND',
    'LT',
    'GT',
    'SEMICOLON',
    'NL',
)

t_ignore_SPACES = r'[ \t\r]+'
internal_string = r'.*?(?<!\\)(\\\\)*?'
raw_string = r'[:\\/~\.\+\-\?\$\*\[\]_0-9a-zA-Z]+'
t_STRING = r'("' + internal_string + r'"|\'' + internal_string + r'\'|' + raw_string + r')'
t_ignore_COMMENT = r'\#[^\n]*'
t_OR = r'\|'
t_AND = r'&'
t_OR_OR = r'\|\|'
t_AND_AND = r'&&'
t_LT = r'<'
t_GT = r'>&?'
t_SEMICOLON = r';'
t_NL = r'\n'


def t_error(t):
    print("lex error: " + str(t))


# precedence = (
# )


def p_start(p):
    """
    start : simple_list1
          | simple_list1 AND
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Background(p[1])


def p_simple_list1_and(p):
    """
    simple_list1 : simple_list1 AND_AND newline_list simple_list1
    """
    p[0] = And(p[1], p[4])


def p_simple_list1_or(p):
    """
    simple_list1 : simple_list1 OR_OR newline_list simple_list1
    """
    p[0] == Or(p[1], p[4])


def p_simple_list1(p):
    """
    simple_list1 : pipeline_command
    """
    p[0] = p[1]


def p_pipeline_command(p):
    """
    pipeline_command : pipeline
    """
    p[0] = p[1]


def p_pipeline(p):
    """
    pipeline : pipeline OR newline_list pipeline
             | command
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Pipe()
        for o in (p[1], p[4]):
            if isinstance(o, Pipe):
                p[0].command_list.extend(o.command_list)
            elif isinstance(o, Command):
                p[0].command_list.append(o)
            else:
                raise Exception("bad command or pipeline")


def p_command(p):
    """
    command : simple_command
    """
    p[0] = p[1]


def p_simple_command(p):
    """
    simple_command : simple_command_element
                   | simple_command simple_command_element
    """
    p[0] = Command()
    if len(p) == 2:
        p[0].arg_list.append(p[1])
    else:
        for o in (p[1], p[2]):
            if isinstance(o, Command):
                p[0].arg_list.extend(o.arg_list)
            elif isinstance(o, RedirectionIn):
                p[0].redirect_in = o
            elif isinstance(o, RedirectionOut):
                p[0].redirect_out = o
            elif isinstance(o, str):
                p[0].arg_list.append(o)
            else:
                raise Exception("bad command")


def p_simple_command_element(p):
    """
    simple_command_element : STRING
                           | redirection
    """
    p[0] = p[1]


def p_redirection_out(p):
    """
    redirection : GT STRING
    """
    p[0] = RedirectionOut(p[2])


def p_redirection_in(p):
    """
    redirection : LT STRING
    """
    p[0] = RedirectionIn(p[2])


def p_newline_list(p):
    """
    newline_list :
                 | newline_list NL
    """
    pass


def p_error(p):
    print("syntax error: " + str(p))

if __name__ == "__main__":
    lexer = ply.lex.lex(debug=True)
    # while True:
    #     lexer.input(input('> '))
    #     for token in iter(lexer.token, None):
    #         print(token)
    parser = ply.yacc.yacc(debug=True)
    visitor = ExecuteVisitor()
    while True:
        ret = parser.parse(input('> '))
        visitor.visit(None, ret)


