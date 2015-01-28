#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ply.lex
import ply.yacc


FLAG_INVERT_RETURN  = 0x00000001
FLAG_TIME_PIPE_LINE = 0x00000002


class BaseElement:
    def __init__(self):
        pass

    def accept(self, visitor):
        raise NotImplementedError("BaseElement.visit")


class Background(BaseElement):
    def __init__(self, command):
        BaseElement.__init__(self)
        self.command = command

    def accept(self, visitor):
        visitor(self)
        visitor(self.command)


class And(BaseElement):
    def __init__(self, left, right):
        BaseElement.__init__(self)
        self.left = left
        self.right = right

    def accept(self, visitor):
        visitor(self)
        visitor(self.left)
        visitor(self.right)


class Or(BaseElement):
    def __init__(self, left, right):
        BaseElement.__init__(self)
        self.left = left
        self.right = right

    def accept(self, visitor):
        visitor(self)
        visitor(self.left)
        visitor(self.right)


class Pipe(BaseElement):
    def __init__(self):
        BaseElement.__init__(self)
        self.flags = 0
        self.command_list = []

    def accept(self, visitor):
        visitor(self)


class SequenceCommandList(BaseElement):
    def __init__(self):
        BaseElement.__init__(self)
        self.command_list = []

    def accept(self, visitor):
        visitor(self)
        for cmd in self.command_list:
            visitor(cmd)


class Command(BaseElement):
    def __init__(self):
        BaseElement.__init__(self)
        self.arg_list = []
        self.redirect_in = None
        self.redirect_out = None

    def accept(self, visitor):
        visitor(self)
        visitor(self.redirect_in)
        visitor(self.redirect_out)


class RedirectionIn(BaseElement):
    def __init__(self, file_name):
        BaseElement.__init__(self)
        self.file_name = file_name

    def accept(self, visitor):
        visitor(self)


class RedirectionOut(BaseElement):
    def __init__(self, file_name):
        BaseElement.__init__(self)
        self.file_name = file_name

    def accept(self, visitor):
        visitor(self)


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
    'BANG',
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
t_BANG = r'!'


def t_error(t):
    print("lex error: " + str(t))


# precedence = (
# )


def p_input_unit(p):
    """
    input_unit : simple_list simple_list_terminator
               | NL
    """
    if len(p) == 3:
        p[0] = p[1]


def p_input_unit_error(p):
    """
    input_unit : error NL
    """
    print("Syntax error in input_unit_error, bad expression")


def p_simple_list_terminator(p):
    """
    simple_list_terminator :
                           | NL
                           | SEMICOLON
    """
    pass


def p_simple_list(p):
    """
    simple_list : simple_list1
                | simple_list1 SEMICOLON
    """
    p[0] = p[1]


def p_simple_list_and(p):
    """
    simple_list : simple_list1 AND
    """
    p[0] = Background(p[1])


def p_simple_list1_and_and(p):
    """
    simple_list1 : simple_list1 AND_AND newline_list simple_list1
    """
    p[0] = And(p[1], p[4])


def p_simple_list1_or_or(p):
    """
    simple_list1 : simple_list1 OR_OR newline_list simple_list1
    """
    p[0] == Or(p[1], p[4])


# TODO
def p_simple_list1_and(p):
    """
    simple_list1 : simple_list1 AND simple_list1
    """
    raise NotImplementedError("`cmd & cmd` is not supported yet")


def p_simple_list1_semi(p):
    """
    simple_list1 : simple_list1 SEMICOLON simple_list1
    """
    p[0] = SequenceCommandList()
    for o in (p[1], p[3]):
        if isinstance(o, SequenceCommandList):
            p[0].command_list.expand(o.command_list)
        else:
            p[0].command_list.append(o)


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


def p_pipeline_command_bang(p):
    """
    pipeline_command : BANG pipeline_command
    """
    p[0] = p[2]
    p[0].flags ^= FLAG_INVERT_RETURN


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
                p[0].flags |= o.flags
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


def get_syntax_text():
    """
    return the complete syntax text
    """
    # TODO
    return "Not implemented yet"


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

