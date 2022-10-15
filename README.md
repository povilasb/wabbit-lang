# Wabbit

Wabbit - a super simple programming language from David Beazley's
[compiler course](https://dabeaz.com/compiler.html):

```wb
func factorial(n int) int {
    var f int = 1;
    while n > 0 {
        f = f * n;
        n = n - 1;
    }
    return f;
}

print factorial(5);
```

In this repo you can find:

* a Wabbit parser,
* interpreter
* and a compiler (via LLVM).

## Usage

```sh
poetry install
poetry run python -m wabbit.runit main.wb
poetry run python -m wabbit.compile main.wb

poetry run python -m wabbit.tokenit main.wb
poetry run python -m wabbit.parsit main.wb
```

## Grammar

The following grammar is a formal description of Wabbit syntax written
as a PEG (Parsing Expression Grammar). Tokens are specified in ALLCAPS
and are assumed to be returned by the tokenizer.

NOTE that it's very likely I have not implement all of this grammar (yet).

In this specification, the following syntax is used:

```
{ symbols }   --> Zero or more repetitions of symbols
[ symbols ]   --> Zero or one occurences of symbols (optional)
( symbols )   --> Grouping
sym1 / sym2   --> First match of sym1 or sym2.
```

A program consists of zero or more statements followed by the end-of-file (EOF).
Here is the grammar:

```
program : statements EOF

statements : { statement }

statement : print_statement
          / variable_definition
          / const_definition
          / func_definition
          / if_statement
          / while_statement
          / break_statement
          / continue_statement
          / return_statement
          / expr_statement

print_statement : PRINT expression SEMI

variable_definition : VAR NAME [ type ] ASSIGN expression SEMI
                    / VAR NAME type [ ASSIGN expression ] SEMI

const_definition : CONST NAME [ type ] ASSIGN expression SEMI

func_definition : FUNC NAME LPAREN [ parameters ] RPAREN type LBRACE statements RBRACE

parameters : parameter { COMMA parameter }

parameter  : NAME type

if_statement : IF expr LBRACE statements RBRACE [ ELSE LBRACE statements RBRACE ]

while_statement : WHILE expr LBRACE statements RBRACE

break_statement : BREAK SEMI

continue_statement : CONTINUE SEMI

return_statement : RETURN expression SEMI

expr_statement : expr SEMI

expr : logicalexpr { ASSIGN logicalexpr }

logicalexpr : orterm { LOR ortem }

orterm : andterm { LAND andterm }

andterm : sumterm { LT/LE/GT/GE/EQ/NE sumterm }

sumterm : multerm { PLUS/MINUS multerm }

multerm : factor { TIMES/DIVIDE factor }

factor : literal
       / LPAREN expression RPAREN
       / LBRACE statements RBRACE
       / PLUS factor
       / MINUS factor
       / LNOT factor
       / NAME LPAREN [ exprlist ] RPAREN
       / location

literal : INTEGER
        / FLOAT
        / CHAR
        / TRUE
        / FALSE

exprlist : expression { COMMA expression }

location : NAME

type      : NAME
```
