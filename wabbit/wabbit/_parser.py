import typing as t

from ._lexer import Token, tokenize
from ._ast import *

TokenType: t.TypeAlias = t.Literal["INTEGER"] | str


def parse_file(fname: str) -> Statements:
    with open(fname) as f:
        source = f.read()
        return parse_source(source)


def parse_source(text: str) -> Statements:
    tokens = tokenize(text)
    return _parse_program(_TokenStream(tokens))


def _parse_program(tokens: "_TokenStream") -> Statements:
    ast = Statements(nodes=[])
    ast.nodes.append(Integer(value="123"))
    return ast


class _TokenStream:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._curr_token = 0

    def peek(self, toktype: TokenType) -> Token | None:
        if self._tokens[self._curr_token].type == toktype:
            return self._tokens[self._curr_token]

    def expect(self, toktype: TokenType) -> Token:
        if self._tokens[self._curr_token].type != toktype:
            raise SyntaxError(f"Expected {toktype}")

        self._curr_token += 1
        return self._tokens[self._curr_token - 1]  # Return the matched token
