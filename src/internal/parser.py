#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ply.lex
import ply.yacc
from ply.lex import TOKEN

FLAG_INVERT_RETURN = 1
FLAG_TIME_PIPE_LINE = (1 << 1)
FLAG_TIME_POSIX = (1 << 2)


class BaseElement:
    def __init__(self):
        pass

    def accept(self, visitor):
        raise NotImplementedError("BaseElement.visit")


class Background(BaseElement):
    def __init__(self, command):
        super().__init__()
        self.command = command

    def accept(self, visitor):
        visitor(self)
        visitor(self.command)


class And(BaseElement):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def accept(self, visitor):
        visitor(self)
        visitor(self.left)
        visitor(self.right)


class Or(BaseElement):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def accept(self, visitor):
        visitor(self)
        visitor(self.left)
        visitor(self.right)


class Pipe(BaseElement):
    def __init__(self):
        super().__init__()
        self.flags = 0
        self.command_list = []

    def accept(self, visitor):
        visitor(self)
        for cmd in self.command_list:
            visitor(cmd)


class SimpleCommandList(BaseElement):
    def __init__(self):
        super().__init__()
        self.command_list = []

    def accept(self, visitor):
        visitor(self)
        for cmd in self.command_list:
            visitor(cmd)


class Command(BaseElement):
    def __init__(self):
        super().__init__()
        self.env_list = []
        self.arg_list = []
        self.redirect_in = None
        self.redirect_out = None

    def accept(self, visitor):
        visitor(self)


class RedirectionIn(BaseElement):
    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name

    def accept(self, visitor):
        visitor(self)


class RedirectionOut(BaseElement):
    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name

    def accept(self, visitor):
        visitor(self)


# class For(BaseElement):
#     def __init__(self, var, value_list, command):
#         super().__init__()
#         self.env_list = []
#         self.var = var
#         self.value_list = value_list
#         self.command = command
#
#     def accept(self, visitor):
#         visitor(self)
#         # TODO: do we really need to let visitor visit our `value_list`?
#         visitor(self.value_list)
#         visitor(self.command)


class Assign(BaseElement):
    def __init__(self, var, value):
        super().__init__()
        self.var = var
        self.value = value

    def accept(self, visitor):
        visitor(self)


# /* Reserved words.  These are only recognized as the first word of a
#    command. */
# STRING_INT_ALIST word_token_alist[] = {
#   { "if", IF },
#   { "then", THEN },
#   { "else", ELSE },
#   { "elif", ELIF },
#   { "fi", FI },
#   { "case", CASE },
#   { "esac", ESAC },
#   { "for", FOR },
# #if defined (SELECT_COMMAND)
#   { "select", SELECT },
# #endif
#   { "while", WHILE },
#   { "until", UNTIL },
#   { "do", DO },
#   { "done", DONE },
#   { "in", IN },
#   { "function", FUNCTION },
# #if defined (COMMAND_TIMING)
#   { "time", TIME },
# #endif
#   { "{", '{' },
#   { "}", '}' },
#   { "!", BANG },
# #if defined (COND_COMMAND)
#   { "[[", COND_START },
#   { "]]", COND_END },
# #endif
# #if defined (COPROCESS_SUPPORT)
#   { "coproc", COPROC },
# #endif
#   { (char *)NULL, 0}
# };

# Handle special cases of token recognition:
#         IN is recognized if the last token was WORD and the token
#         before that was FOR or CASE or SELECT.
#
#         DO is recognized if the last token was WORD and the token
#         before that was FOR or SELECT.
#
#         ESAC is recognized if the last token caused `esacs_needed_count'
#         to be set
#
#         `{' is recognized if the last token as WORD and the token
#         before that was FUNCTION, or if we just parsed an arithmetic
#         `for' command.
#
#         `}' is recognized if there is an unclosed `{' present.
#
#         `-p' is returned as TIMEOPT if the last read token was TIME.
#         `--' is returned as TIMEIGN if the last read token was TIMEOPT.
#
#         ']]' is returned as COND_END if the parser is currently parsing
#         a conditional expression ((parser_state & PST_CONDEXPR) != 0)
#
#         `time' is returned as TIME if and only if it is immediately
#         preceded by one of `;', `\n', `||', `&&', or `&'.
#

reserved = {
    'if': 'IF',
    'then': 'THEN',
    'elif': 'ELIF',
    'fi': 'FI',
    'case': 'CASE',
    'esac': 'ESAC',
    'for': 'FOR',
    'select': 'SELECT',
    'while': 'WHILE',
    'until': 'UNTIL',
    'do': 'DO',
    'done': 'DONE',
    'function': 'FUNCTION',
    'coproc': 'COPROC',

    '[[': 'COND_START',
    ']]': 'COND_END',
    # ??: 'COND_ERROR',

    'in': 'IN',
    'time': 'TIME',
    '-p': 'TIMEOPT',
    '--': 'TIMEIGN',
}

tokens = [
    'ASSIGNMENT_WORD',

    'TIMEOPT',
    'TIMEIGN',
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
    'LBRACE',
    'RBRACE',
    'LPARENT',
    'RPARENT',
    'BAR_AND',
    'SEMI_SEMI',
] + list(reserved.values())


class BashLexer:
    """
    Lexer for Bash
    """
    tokens = tokens
    internal_string = r'.*?(?<!\\)(\\\\)*?'
    direct_string = r'[:\\/~\.\+\-\?\$\*\[\]=_0-9a-zA-Z]+'
    any_string = r'("' + internal_string + r'"|\'' + internal_string + r'\'|' + direct_string + r')'

    reserved_pre = ('NL', 'SEMICOLON', 'LPARENT', 'RPARENT',
                    'OR', 'AND', 'LBRACE', 'RBRACE', 'AND_AND',
                    'BANG', 'BAR_AND', 'DO', 'DONE', 'ELIF',
                    'ELSE', 'ESAC', 'FI', 'IF', 'OR_OR', 'SEMI_SEMI',
                    'TIME', 'TIMEOPT', 'TIMEIGN', 'UNTIL', 'WHILE')

    t_ignore_SPACES = r'[ \t\r]+'
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
    t_TIMEOPT = r'-p'
    t_TIMEIGN = r'--'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_LPARENT = r'\('
    t_RPARENT = r'\)'
    t_BAR_AND = r'\|&'
    t_SEMI_SEMI = r';;'

    @TOKEN(any_string)
    def t_STRING(self, t):
        # reserved tokens
        if not self.last_token or self.last_token.type in self.reserved_pre:
            if t.value[0] not in "'\"" and '=' in t.value:
                idx = t.value.find('=')
                if idx != 0 and idx < len(t.value) - 1:
                    t.type = 'ASSIGNMENT_WORD'
            else:
                t.type = reserved.get(t.value, 'STRING')

        # special case tokens
        if self.token_before_that is not None and self.token_before_that.type in ('FOR', 'CASE', 'SELECT'):
            if t.value == 'in':
                t.type = 'IN'
        elif self.token_before_that is not None and self.token_before_that.type in ('FOR', 'SELECT'):
            if t.value == 'do':
                t.type = 'DO'

        return t

    def t_error(self, t):
        print("lex error: " + str(t))

    def __init__(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
        self.last_token = None
        self.token_before_that = None

    def token_func(self):
        self.last_token, self.token_before_that = self.lexer.token(), self.last_token
        return self.last_token


# precedence = (
# )

class BashParser:
    """
    Bash parser
    """
    tokens = tokens

    def p_input_unit(self, p):
        """
        input_unit : simple_list simple_list_terminator
                   | NL
        """
        if len(p) == 3:
            p[0] = p[1]

    def p_input_unit_error(self, p):
        """
        input_unit : error NL
        """
        print("Syntax error in input_unit_error, bad expression")

    def p_simple_list_terminator(self, p):
        """
        simple_list_terminator :
                               | NL
        """
        pass

    def p_list_terminator(self, p):
        """
        list_terminator :
                               | NL
                               | SEMICOLON
        """
        pass

    def p_simple_list(self, p):
        """
        simple_list : simple_list1
                    | simple_list1 SEMICOLON
        """
        p[0] = p[1]

    def p_simple_list_and(self, p):
        """
        simple_list : simple_list1 AND
        """
        p[0] = Background(p[1])

    def p_simple_list1_and_and(self, p):
        """
        simple_list1 : simple_list1 AND_AND newline_list simple_list1
        """
        p[0] = And(p[1], p[4])

    def p_simple_list1_or_or(self, p):
        """
        simple_list1 : simple_list1 OR_OR newline_list simple_list1
        """
        p[0] = Or(p[1], p[4])

    # TODO
    def p_simple_list1_and(self, p):
        """
        simple_list1 : simple_list1 AND simple_list1
        """
        raise NotImplementedError("`cmd & cmd` is not supported yet")

    def p_simple_list1_semi(self, p):
        """
        simple_list1 : simple_list1 SEMICOLON simple_list1
        """
        p[0] = SimpleCommandList()
        for o in (p[1], p[3]):
            if isinstance(o, SimpleCommandList):
                p[0].command_list.expand(o.command_list)
            else:
                p[0].command_list.append(o)

    def p_simple_list1(self, p):
        """
        simple_list1 : pipeline_command
        """
        p[0] = p[1]

    def p_pipeline_command(self, p):
        """
        pipeline_command : pipeline
        """
        p[0] = p[1]

    def p_pipeline_command_bang(self, p):
        """
        pipeline_command : BANG pipeline_command
        """
        p[0] = p[2]
        p[0].flags ^= FLAG_INVERT_RETURN

    def p_pipeline_command_timespec(self, p):
        """
        pipeline_command : timespec pipeline_command
        """
        p[0] = p[2]
        p[0].flags |= p[1]

    # TODO
    def p_pipeline_command_bang_terminator(self, p):
        """
        pipeline_command : BANG list_terminator
        """
        raise NotImplementedError("`!;` is not support")

    # TODO
    def p_pipeline_command_timespec_terminator(self, p):
        """
        pipeline_command : timespec list_terminator
        """
        raise NotImplementedError("`time;` is not support")

    def p_timespec(self, p):
        """
        timespec : TIME
                 | TIME TIMEOPT
                 | TIME TIMEOPT TIMEIGN
        """
        p[0] = 0
        if len(p) == 2:
            p[0] |= FLAG_TIME_PIPE_LINE
        else:
            p[0] |= FLAG_TIME_PIPE_LINE
            p[0] |= FLAG_TIME_POSIX

    def p_pipeline(self, p):
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

    def p_command(self, p):
        """
        command : simple_command
                | shell_command
        """
        p[0] = p[1]

    def p_shell_command(self, p):
        """
        shell_command : for_command
        """
        p[0] = p[1]

    # for_command : FOR WORD newline_list DO compound_list DONE
    # | FOR WORD newline_list '{' compound_list '}'
    # | FOR WORD ';' newline_list DO compound_list DONE
    # | FOR WORD ';' newline_list '{' compound_list '}'
    # |
    # | FOR WORD newline_list IN word_list list_terminator newline_list '{' compound_list '}'
    # | FOR WORD newline_list IN list_terminator newline_list DO compound_list DONE
    # | FOR WORD newline_list IN list_terminator newline_list '{' compound_list '}'
    def p_for_command(self, p):
        """
        for_command : FOR STRING newline_list IN word_list list_terminator newline_list DO compound_list DONE
        """
        # p[0] = For(p[2], p[5], p[9])
        p[0] = Command()
        # p[0].env_list = []
        p[0].arg_list = ['for', p[2], p[5], p[8]]
        p[0].redirect_in = None
        p[0].redirect_out = None

    def p_list(self, p):
        """
        list : newline_list list0
        """
        p[0] = p[2]

    def p_list0(self, p):
        """
        list0 : list1 NL newline_list
              | list1 SEMICOLON newline_list
        """
        p[0] = p[1]

    def p_list0_and(self, p):
        """
        list0 : list1 AND newline_list
        """
        p[0] = Background(p[1])

    def p_list1(self, p):
        """
        list1 : list1 SEMICOLON newline_list list1
              | list1 NL newline_list list1
              | pipeline_command
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            # TODO: abstract this kind of procedure as `command_connect`
            p[0] = SimpleCommandList()
            for o in (p[1], p[4]):
                if isinstance(o, SimpleCommandList):
                    p[0].command_list.extend(o.command_list)
                else:
                    p[0].command_list.append(o)

    def p_list1_and(self, p):
        """
        list1 : list1 AND newline_list list1
        """
        p[0] = SimpleCommandList()
        p[0].command_list.append(Background(p[1]))
        if isinstance(p[4], SimpleCommandList):
            p[0].command_list.extend(p[4])
        else:
            p[0].command_list.append(p[4])

    def p_list1_and_and(self, p):
        """
        list1 : list1 AND_AND newline_list list1
        """
        p[0] = And(p[1], p[4])

    def p_list1_or_or(self, p):
        """
        list1 : list1 OR_OR newline_list list1
        """
        p[0] = Or(p[1], p[4])

    def p_compound_list(self, p):
        """
        compound_list : list
                      | newline_list list1
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]

    # def p_command_shell_command_redirection_list(p):
    #     """
    #     command : shell_command redirection_list
    #     """
    #     pass

    # def p_command_function_define(p):
    #     """
    #     command : function_def
    #     """
    #     pass

    # def p_command_coproc(p):
    #     """
    #     command : coproc
    #     """
    #     pass

    # def p_shell_command_for(p):
    #     """
    #     shell_command : for_command
    #     """
    #     p[0] = p[1]

    def p_simple_command(self, p):
        """
        simple_command : simple_command_element
                       | simple_command simple_command_element
        """
        p[0] = Command()
        if len(p) == 2:
            if isinstance(p[1], Command) or isinstance(p[1], str):
                p[0].arg_list.append(p[1])
            elif isinstance(p[1], Assign):
                p[0].env_list.append(p[1])
            else:
                raise Exception("Unknown command element type")
        else:
            for o in (p[1], p[2]):
                if isinstance(o, Command):
                    p[0].arg_list.extend(o.arg_list)
                    p[0].env_list.extend(o.env_list)
                elif isinstance(o, RedirectionIn):
                    p[0].redirect_in = o
                elif isinstance(o, RedirectionOut):
                    p[0].redirect_out = o
                elif isinstance(o, str):
                    p[0].arg_list.append(o)
                elif isinstance(o, Assign):
                    p[0].env_list.append(o)
                else:
                    raise Exception("bad command")

    def p_simple_command_element(self, p):
        """
        simple_command_element : STRING
                               | redirection
        """
        p[0] = p[1]

    # TODO: support `v=abc ls`
    def p_simple_command_element_assignment(self, p):
        """
        simple_command_element : ASSIGNMENT_WORD
        """
        idx = p[1].find('=')
        p[0] = Assign(p[1][:idx], p[1][idx+1:])

    def p_redirection_out(self, p):
        """
        redirection : GT STRING
        """
        p[0] = RedirectionOut(p[2])

    def p_redirection_in(self, p):
        """
        redirection : LT STRING
        """
        p[0] = RedirectionIn(p[2])

    def p_newline_list(self, p):
        """
        newline_list :
                     | newline_list NL
        """
        pass

    def p_word_list(self, p):
        """
        word_list : STRING
                  | word_list STRING
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_error(self, p):
        if not p:
            # TODO: temporary solution
            self.context.prompt_input()
            ply.yacc.errok()
            return
        print("syntax error: " + str(p))

    def __init__(self, context, lexer, debug=False):
        self.context = context
        self.lexer = lexer
        self.parser = ply.yacc.yacc(module=self, debug=debug)

    def parse(self, **kwargs):
        return self.parser.parse(**kwargs)


if __name__ == "__main__":
    pass

