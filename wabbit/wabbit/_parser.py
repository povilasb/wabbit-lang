import typing as t

from ._lexer import Token, tokenize
from ._ast import *
from ._errors import WabbitSyntaxError

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

    while not tokens.eof():
        if stmt := _parse_statement(tokens):
            ast.nodes.append(stmt)

    return ast


def _parse_statement(tokens: "_TokenStream") -> Statement:
    if tokens.peek("BREAK"):
        return _parse_break_statement(tokens)
    elif tokens.peek("CONTINUE"):
        return _parse_continue_statement(tokens)
    elif tokens.peek("PRINT"):
        return _parse_print_statement(tokens)
    elif tokens.peek("CONST"):
        return _parse_const_statement(tokens)
    elif tokens.peek("VAR"):
        return _parse_var_statement(tokens)
    elif tokens.peek("IF"):
        return _parse_if_statement(tokens)
    elif tokens.peek("WHILE"):
        return _parse_while_statement(tokens)
    else:
        return _parse_expression_as_statement(tokens)


def _parse_break_statement(tokens: "_TokenStream") -> Break:
    t = tokens.expect("BREAK")
    tokens.expect("SEMICOLON")
    return Break(location=t.pos)


def _parse_continue_statement(tokens: "_TokenStream") -> Continue:
    t = tokens.expect("CONTINUE")
    tokens.expect("SEMICOLON")
    return Continue(location=t.pos)


def _parse_print_statement(tokens: "_TokenStream") -> PrintStatement:
    t = tokens.expect("PRINT")
    expr = _parse_expression(tokens)
    tokens.expect("SEMICOLON")
    return PrintStatement(location=t.pos, value=expr)


def _parse_const_statement(tokens: "_TokenStream") -> ConstDecl:
    t1 = tokens.expect("CONST")
    name_node = _parse_name(tokens)
    type_node = _parse_type(tokens) if tokens.peek("NAME") else None

    tokens.expect("EQUAL")
    val = _parse_expression(tokens)
    tokens.expect("SEMICOLON")

    return ConstDecl(location=t1.pos, name=name_node, value=val, type_=type_node)


def _parse_var_statement(tokens: "_TokenStream") -> VarDecl:
    t1 = tokens.expect("VAR")
    name_node = _parse_name(tokens)
    type_node = _parse_type(tokens) if tokens.peek("NAME") else None

    if tokens.peek("EQUAL"):
        tokens.expect("EQUAL")
        val = _parse_expression(tokens)
    else:
        val = None

    tokens.expect("SEMICOLON")

    return VarDecl(location=t1.pos, name=name_node, value=val, type_=type_node)


def _parse_if_statement(tokens: "_TokenStream") -> IfElse:
    t1 = tokens.expect("IF")
    test = _parse_expression(tokens)
    body = _parse_statements_block(tokens)
    else_body = _parse_else_statement(tokens) if tokens.peek("ELSE") else None
    return IfElse(location=t1.pos, test=test, body=body, else_body=else_body)


def _parse_else_statement(tokens: "_TokenStream") -> Statements:
    tokens.expect("ELSE")
    return _parse_statements_block(tokens)


def _parse_while_statement(tokens: "_TokenStream") -> While:
    t1 = tokens.expect("WHILE")
    test = _parse_expression(tokens)
    body = _parse_statements_block(tokens)
    return While(location=t1.pos, test=test, body=body)


def _parse_statements_block(tokens: "_TokenStream") -> Statements:
    """Parse multiple statements surrounded by curly braces."""
    tokens.expect("OPEN_CURLY_BRACE")

    body = Statements(nodes=[])
    while not tokens.peek("CLOSE_CURLY_BRACE"):
        body.nodes.append(_parse_statement(tokens))
    tokens.expect("CLOSE_CURLY_BRACE")

    return body


def _parse_expression_as_statement(tokens: "_TokenStream") -> ExprAsStatement:
    expr = _parse_expression(tokens)
    tokens.expect("SEMICOLON")
    return ExprAsStatement(expr=expr)


def _parse_type(tokens: "_TokenStream") -> Type:
    t = tokens.expect("NAME")
    return Type(location=t.pos, name=t.value)


def _parse_expression(tokens: "_TokenStream") -> Expression:
    factor1 = _parse_factor(tokens)

    if tokens.peek_one_of("MULTIPLY", "DIVIDE"):
        return _parse_binop(tokens, factor1)

    return factor1


def _parse_binop(tokens: "_TokenStream", factor1: Expression) -> Expression:
    tok_op = tokens.expect_one_of("MULTIPLY", "DIVIDE")
    factor2 = _parse_factor(tokens)
    return BinOp(
        location=factor1.location, operation=tok_op.value, left=factor1, right=factor2
    )


def _parse_factor(tokens: "_TokenStream") -> Expression:
    if tokens.peek("INTEGER"):
        return _parse_integer(tokens)
    elif tokens.peek("FLOAT"):
        return _parse_float(tokens)
    elif tokens.peek("TRUE"):
        return _parse_true(tokens)
    elif tokens.peek("FALSE"):
        return _parse_false(tokens)
    elif tokens.peek("NAME"):
        return _parse_name(tokens)
    else:
        raise WabbitSyntaxError("Unexpected token for factor", tokens.current())


def _parse_name(tokens: "_TokenStream") -> Name:
    t = tokens.expect("NAME")
    return Name(location=t.pos, value=t.value)


def _parse_integer(tokens: "_TokenStream") -> Integer:
    t = tokens.expect("INTEGER")
    return Integer(location=t.pos, value=t.value)


def _parse_float(tokens: "_TokenStream") -> Float:
    t = tokens.expect("FLOAT")
    return Float(location=t.pos, value=t.value)


def _parse_true(tokens: "_TokenStream") -> Boolean:
    t = tokens.expect("TRUE")
    return Boolean(location=t.pos, value=True)


def _parse_false(tokens: "_TokenStream") -> Boolean:
    t = tokens.expect("FALSE")
    return Boolean(location=t.pos, value=False)


class _TokenStream:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._curr_token = 0

    def peek(self, toktype: TokenType) -> Token | None:
        if self.eof():
            return None

        if self.current().type == toktype:
            return self._tokens[self._curr_token]

    def peek_one_of(self, *tok_types: TokenType) -> Token | None:
        if self.eof():
            return None

        if self.current().type in tok_types:
            return self._tokens[self._curr_token]

    def expect(self, toktype: TokenType) -> Token:
        if self.current().type != toktype:
            raise WabbitSyntaxError(
                f"Expected token '{toktype}' but was '{self.current().type}'"
            )

        self._curr_token += 1
        return self._tokens[self._curr_token - 1]  # Return the matched token

    def expect_one_of(self, *tok_types: TokenType) -> Token:
        if not self.current().type in tok_types:
            raise WabbitSyntaxError(
                f"Expected token one of '{tok_types}' but was '{self.current().type}'"
            )

        self._curr_token += 1
        return self._tokens[self._curr_token - 1]  # Return the matched token

    def current(self) -> Token:
        return self._tokens[self._curr_token]

    def eof(self) -> bool:
        return self._curr_token >= len(self._tokens)
