#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ply.lex
import ply.yacc


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
    'time': 'TIME',
    'if': 'IF',
}

tokens = [
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
] + list(reserved.values())


class BashLexer:
    """
    Lexer for Bash
    """
    tokens = tokens
    internal_string = r'.*?(?<!\\)(\\\\)*?'
    raw_string = r'[:\\/~\.\+\-\?\$\*\[\]_0-9a-zA-Z]+'
    any_string = r'("' + internal_string + r'"|\'' + internal_string + r'\'|' + raw_string + r')'

    # @TOKEN(any_string)
    # def t_STRING(t):
    #     t.type = reserved.get(t.value, 'STRING')
    #     return t

    t_ignore_SPACES = r'[ \t\r]+'
    t_ignore_COMMENT = r'\#[^\n]*'
    t_STRING = any_string
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

    def t_error(self, t):
        print("lex error: " + str(t))

    def __init__(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
        self.last_token = None

    def token_func(self):
        self.last_token = self.lexer.token()
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
        p[0] = SequenceCommandList()
        for o in (p[1], p[3]):
            if isinstance(o, SequenceCommandList):
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

    #            | shell_command
    def p_command(self, p):
        """
        command : simple_command
        """
        p[0] = p[1]

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

    # def p_for_command(p):
    #     """
    #     for_command : FOR WORD newline_list DO compound_list DONE
    #     """
    #     pass

    # | FOR WORD newline_list '{' compound_list '}'
    # | FOR WORD ';' newline_list DO compound_list DONE
    # | FOR WORD ';' newline_list '{' compound_list '}'
    # | FOR WORD newline_list IN word_list list_terminator newline_list DO compound_list DONE
    # | FOR WORD newline_list IN word_list list_terminator newline_list '{' compound_list '}'
    # | FOR WORD newline_list IN list_terminator newline_list DO compound_list DONE
    # | FOR WORD newline_list IN list_terminator newline_list '{' compound_list '}'

    def p_simple_command(self, p):
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

    def p_simple_command_element(self, p):
        """
        simple_command_element : STRING
                               | redirection
        """
        p[0] = p[1]

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
        # ignore
        pass

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

