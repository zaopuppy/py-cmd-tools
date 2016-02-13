# py-cmd-tools

## What is it

*py-cmd-tools* is aimed at implementing most of useful Unix/Linux command tools, so that we can use those powerful tools on Windows, which usually is done by installing `Cygwin` or `MinGW`.


To use those tools, it's recommended to use *py-pseudo-shell* instead of using windows command.


## Pseudo shell

*py-pseudo-shell* is bash-like shell environment. My plan is make it support most features of bash step by step.


Now only some simple features were implemented:


 * autocomplete
 * pipeline
 * simple shell expanding
 * basic bash builtin commands


## Available tools


 * which (built-in)
 * cd (built-in)
 * pwd
 * echo
 * ls
 * grep
 * codestat (new)
 * diff


## Usage


## Tasks

 * redirection
 * detect file type by reading the first line like bash, not by guessing.
 * if-stmt
 * while-stmt
 * test
 * file
 * test
 * shell expanding (like `*.log`, `applogcat[0-9]+.log`, etc)
 * testing code
 * file caching, for better performance.
 




TBD
