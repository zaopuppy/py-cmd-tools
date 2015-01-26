#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ply.lex
import ply.yacc


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


def p_input_unit(p):
    """
    input_unit : simple_list
    """
    p[0] = p[1]

# def p_simple_list_terminator(p):
#     """
#     simple_list_terminator :	'\n'
#                            | yacc_EOF
#     """
#     pass


def p_simple_list(p):
    """
    simple_list : simple_list1
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
    p[0] = Pipe()
    if len(p) == 2:
        p[0].command_list.append(p[1])
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


lexer = ply.lex.lex(debug=False)


def p_error(p):
    if not p:
        # TODO: temporary solution
        lexer.input(input('> '))
        ply.yacc.errok()
        return
    print("syntax error: " + str(p))


parser = ply.yacc.yacc(debug=False)


def parse(**kwargs):
    return parser.parse(**kwargs)


if __name__ == "__main__":
    pass
    # import os
    # import sys
    # from ..shell import Shell
    # path = os.getenv("PATH").split(os.path.pathsep)
    # sh = Shell(basedir=os.path.abspath(os.path.dirname(sys.argv[0])), path=path)
    # if len(sys.argv) <= 1:
    #     print("py-pseudo-shell")
    #     print()
    #     sh.run()
    # else:
    #     # execute script
    #     raise Exception("Not implemented")

