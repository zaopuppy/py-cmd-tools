%{

%}

%%

inputunit:	simple_list simple_list_terminator
	|	'\n'
	|	error '\n'
	|	yacc_EOF
	;

word_list:	WORD
	|	word_list WORD
	;

redirection:	'>' WORD
	|	'<' WORD
	|	NUMBER '>' WORD
	|	NUMBER '<' WORD
	|	REDIR_WORD '>' WORD
	|	REDIR_WORD '<' WORD
	|	GREATER_GREATER WORD
	|	NUMBER GREATER_GREATER WORD
	|	REDIR_WORD GREATER_GREATER WORD
	|	GREATER_BAR WORD
	|	NUMBER GREATER_BAR WORD
	|	REDIR_WORD GREATER_BAR WORD
	|	LESS_GREATER WORD
	|	NUMBER LESS_GREATER WORD
	|	REDIR_WORD LESS_GREATER WORD
	|	LESS_LESS WORD
	|	NUMBER LESS_LESS WORD
	|	REDIR_WORD LESS_LESS WORD
	|	LESS_LESS_MINUS WORD
	|	NUMBER LESS_LESS_MINUS WORD
	|	REDIR_WORD  LESS_LESS_MINUS WORD
	|	LESS_LESS_LESS WORD
	|	NUMBER LESS_LESS_LESS WORD
	|	REDIR_WORD LESS_LESS_LESS WORD
	|	LESS_AND NUMBER
	|	NUMBER LESS_AND NUMBER
	|	REDIR_WORD LESS_AND NUMBER
	|	GREATER_AND NUMBER
	|	NUMBER GREATER_AND NUMBER
	|	REDIR_WORD GREATER_AND NUMBER
	|	LESS_AND WORD
	|	NUMBER LESS_AND WORD
	|	REDIR_WORD LESS_AND WORD
	|	GREATER_AND WORD
	|	NUMBER GREATER_AND WORD
	|	REDIR_WORD GREATER_AND WORD
	|	GREATER_AND '-'
	|	NUMBER GREATER_AND '-'
	|	REDIR_WORD GREATER_AND '-'
	|	LESS_AND '-'
	|	NUMBER LESS_AND '-'
	|	REDIR_WORD LESS_AND '-'
	|	AND_GREATER WORD
	|	AND_GREATER_GREATER WORD
	;

simple_command_element: WORD
	|	ASSIGNMENT_WORD
	|	redirection
	;

redirection_list: redirection
	|	redirection_list redirection
	;

simple_command:	simple_command_element
	|	simple_command simple_command_element
	;

command:	simple_command
	|	shell_command
	|	shell_command redirection_list
	|	function_def
	|	coproc
	;

shell_command:	for_command
	|	case_command
 	|	WHILE compound_list DO compound_list DONE
	|	UNTIL compound_list DO compound_list DONE
	|	select_command
	|	if_command
	|	subshell
	|	group_command
	|	arith_command
	|	cond_command
	|	arith_for_command
	;

for_command:	FOR WORD newline_list DO compound_list DONE
	|	FOR WORD newline_list '{' compound_list '}'
	|	FOR WORD ';' newline_list DO compound_list DONE
	|	FOR WORD ';' newline_list '{' compound_list '}'
	|	FOR WORD newline_list IN word_list list_terminator newline_list DO compound_list DONE
	|	FOR WORD newline_list IN word_list list_terminator newline_list '{' compound_list '}'
	|	FOR WORD newline_list IN list_terminator newline_list DO compound_list DONE
	|	FOR WORD newline_list IN list_terminator newline_list '{' compound_list '}'
	;

arith_for_command:	FOR ARITH_FOR_EXPRS list_terminator newline_list DO compound_list DONE
	|		FOR ARITH_FOR_EXPRS list_terminator newline_list '{' compound_list '}'
	|		FOR ARITH_FOR_EXPRS DO compound_list DONE
	|		FOR ARITH_FOR_EXPRS '{' compound_list '}'
	;

select_command:	SELECT WORD newline_list DO list DONE
	|	SELECT WORD newline_list '{' list '}'
	|	SELECT WORD ';' newline_list DO list DONE
	|	SELECT WORD ';' newline_list '{' list '}'
	|	SELECT WORD newline_list IN word_list list_terminator newline_list DO list DONE
	|	SELECT WORD newline_list IN word_list list_terminator newline_list '{' list '}'
	;

case_command:	CASE WORD newline_list IN newline_list ESAC
	|	CASE WORD newline_list IN case_clause_sequence newline_list ESAC
	|	CASE WORD newline_list IN case_clause ESAC
	;

function_def:	WORD '(' ')' newline_list function_body
	|	FUNCTION WORD '(' ')' newline_list function_body
	|	FUNCTION WORD newline_list function_body
	;

function_body:	shell_command
	|	shell_command redirection_list
	;

subshell:	'(' compound_list ')'
	;

coproc:		COPROC shell_command
	|	COPROC shell_command redirection_list
	|	COPROC WORD shell_command
	|	COPROC WORD shell_command redirection_list
	|	COPROC simple_command
	;

if_command:	IF compound_list THEN compound_list FI
	|	IF compound_list THEN compound_list ELSE compound_list FI
	|	IF compound_list THEN compound_list elif_clause FI
	;


group_command:	'{' compound_list '}'
	;

arith_command:	ARITH_CMD
	;

cond_command:	COND_START COND_CMD COND_END
	;

elif_clause:	ELIF compound_list THEN compound_list
	|	ELIF compound_list THEN compound_list ELSE compound_list
	|	ELIF compound_list THEN compound_list elif_clause
	;

case_clause:	pattern_list
	|	case_clause_sequence pattern_list
	;

pattern_list:	newline_list pattern ')' compound_list
	|	newline_list pattern ')' newline_list
	|	newline_list '(' pattern ')' compound_list
	|	newline_list '(' pattern ')' newline_list
	;

case_clause_sequence:  pattern_list SEMI_SEMI
	|	case_clause_sequence pattern_list SEMI_SEMI
	|	pattern_list SEMI_AND
	|	case_clause_sequence pattern_list SEMI_AND
	|	pattern_list SEMI_SEMI_AND
	|	case_clause_sequence pattern_list SEMI_SEMI_AND
	;

pattern:	WORD
	|	pattern '|' WORD
	;

/* A list allows leading or trailing newlines and
   newlines as operators (equivalent to semicolons).
   It must end with a newline or semicolon.
   Lists are used within commands such as if, for, while.  */

list:		newline_list list0
	;

compound_list:	list
	|	newline_list list1
	;

list0:  	list1 '\n' newline_list
	|	list1 '&' newline_list
	|	list1 ';' newline_list
	;

list1:		list1 AND_AND newline_list list1
	|	list1 OR_OR newline_list list1
	|	list1 '&' newline_list list1
	|	list1 ';' newline_list list1
	|	list1 '\n' newline_list list1
	|	pipeline_command
	;

simple_list_terminator:	'\n'
	|	yacc_EOF
	;

list_terminator:'\n'
	|	';'
	|	yacc_EOF
	;

newline_list:
	|	newline_list '\n'
	;

/* A simple_list is a list that contains no significant newlines
   and no leading or trailing newlines.  Newlines are allowed
   only following operators, where they are not significant.

   This is what an inputunit consists of.  */

simple_list:	simple_list1
	|	simple_list1 '&'
	|	simple_list1 ';'
	;

simple_list1:	simple_list1 AND_AND newline_list simple_list1
	|	simple_list1 OR_OR newline_list simple_list1
	|	simple_list1 '&' simple_list1
	|	simple_list1 ';' simple_list1
	|	pipeline_command
	;

pipeline_command: pipeline
	|	BANG pipeline_command
	|	timespec pipeline_command
	|	timespec list_terminator
	|	BANG list_terminator
	;

pipeline:	pipeline '|' newline_list pipeline
	|	pipeline BAR_AND newline_list pipeline
	|	command
	;

timespec:	TIME
	|	TIME TIMEOPT
	|	TIME TIMEOPT TIMEIGN
	;

%%

