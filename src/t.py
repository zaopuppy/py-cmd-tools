#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ply.lex
import ply.yacc


# There's no multi-methods/multi-dispatching in Python, so it needs
# a little effort to make it available
#
# [1] http://www.artima.com/weblogs/viewpost.jsp?thread=101605
class PrintVisitor:
    def __init__(self, exec_tree):
        self.exec_tree = exec_tree

    def exec(self, context):
        if isinstance()


class BaseElement:
    def __init__(self):
        pass

    def exec(self, context):
        print(type(self))


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


class RedirectionIn(BaseElement):
    def __init__(self, file_name):
        BaseElement.__init__(self)
        self.file_name = file_name


class RedirectionOut(BaseElement):
    def __init__(self, file_name):
        BaseElement.__init__(self)
        self.file_name = file_name


tokens = ('SPACES',
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
        if isinstance(p[1], Pipe):
            p[0].command_list.extend(p[1].command_list)
        else:
            p[0].command_list.append(p[1])
        if isinstance(p[4], Pipe):
            p[0].command_list.extend(p[4].command_list)
        else:
            p[0].command_list.append(p[4])


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
        if isinstance(p[1], Command):
            p[0].arg_list.extend(p[1].arg_list)
        else:
            p[0].arg_list.append(p[1])
        if isinstance(p[2], Command):
            p[0].arg_list.extend(p[2].arg_list)
        else:
            p[0].arg_list.append(p[2])


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
    lexer = ply.lex.lex()
    # while True:
    #     lexer.input(input('> '))
    #     for token in iter(lexer.token, None):
    #         print(token)
    parser = ply.yacc.yacc()
    while True:
        o = parser.parse(input('> '))
        print(o)


