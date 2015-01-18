
start: cmd (OPER_PIPE cmd)* bg_flag?;

cmd: string+ redirect_flag?;

@redirect_flag: (redirect_in | redirect_out)+;

redirect_in: OPER_REDIRECT_IN string;

redirect_out: OPER_REDIRECT_OUT string;

bg_flag: OPER_BG;

string: STRING | RAW_STRING;

%fragment STRING_INTERNAL: '.*?(?<!\\)(\\\\)*?';
%fragment QUOTE: '\'';
%fragment DBL_QUOTE: '"';

STRING : '(' DBL_QUOTE STRING_INTERNAL DBL_QUOTE '|' QUOTE STRING_INTERNAL QUOTE ')';
RAW_STRING: '[:\\/~\.\+\-\?\$\*\[\]_0-9a-zA-Z]+';

COMMENT: '\#[^\n]*'(%ignore);
SPACES: '[ \t\r]+' (%ignore);
OPER_PIPE: '\|';
OPER_BG: '&';
OPER_OR: '\|\|';
OPER_AND: '&&';
OPER_REDIRECT_IN: '<';
OPER_REDIRECT_OUT: '>&?';


