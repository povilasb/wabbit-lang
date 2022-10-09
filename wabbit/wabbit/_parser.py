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
    elif tokens.peek("FUNC"):
        return _parse_func_def(tokens)
    elif tokens.peek("RETURN"):
        return _parse_return_statement(tokens)
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


def _parse_return_statement(tokens: "_TokenStream") -> Return:
    t1 = tokens.expect("RETURN")
    ret_val = _parse_expression(tokens)
    tokens.expect("SEMICOLON")
    return Return(location=t1.pos, value=ret_val)


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
    return _parse_assignment_or_expr(tokens)


def _parse_assignment_or_expr(tokens: "_TokenStream") -> Expression:
    left = _parse_or_or_expr(tokens)
    if tokens.peek("EQUAL"):
        tokens.expect("EQUAL")
        right = _parse_or_or_expr(tokens)
        return Assignment(location=left.location, left=left, right=right)

    return left


def _parse_or_or_expr(tokens: "_TokenStream") -> Expression:
    left = _parse_and_or_expr(tokens)
    while tok_op := tokens.peek_one_of("LOGICAL_OR"):
        tokens.expect_one_of("LOGICAL_OR")
        right = _parse_and_or_expr(tokens)
        left = LogicalOp(
            location=left.location, operation=tok_op.value, left=left, right=right
        )
    return left


def _parse_and_or_expr(tokens: "_TokenStream") -> Expression:
    """This is very similar to _parse_logical_cmp_or_expr() but makes sure the
    precedence of `&&` operators over others:

        a < b && c > d
        (a < b) && (c > d)
    """
    left = _parse_logical_cmp_or_expr(tokens)
    while tok_op := tokens.peek_one_of("LOGICAL_AND"):
        tokens.expect_one_of("LOGICAL_AND")
        right = _parse_logical_cmp_or_expr(tokens)
        left = LogicalOp(
            location=left.location, operation=tok_op.value, left=left, right=right
        )
    return left


def _parse_logical_cmp_or_expr(tokens: "_TokenStream") -> Expression:
    cmp_tokens = ("LESS", "MORE", "LESS_EQ", "MORE_EQ", "DOUBLE_EQ", "NOT_EQ")
    left = _parse_addsub_or_expr(tokens)
    while tok_op := tokens.peek_one_of(*cmp_tokens):
        tokens.expect_one_of(*cmp_tokens)
        right = _parse_addsub_or_expr(tokens)
        left = LogicalOp(
            location=left.location, operation=tok_op.value, left=left, right=right
        )
    return left


def _parse_addsub_or_expr(tokens: "_TokenStream") -> Expression:
    left = _parse_muldiv_or_expr(tokens)
    while tok_op := tokens.peek_one_of("ADD", "SUB"):
        tokens.expect_one_of("ADD", "SUB")
        right = _parse_muldiv_or_expr(tokens)
        left = BinOp(
            location=left.location, operation=tok_op.value, left=left, right=right
        )
    return left


def _parse_muldiv_or_expr(tokens: "_TokenStream") -> Expression:
    left = _parse_factor(tokens)

    while tok_op := tokens.peek_one_of("MULTIPLY", "DIVIDE"):
        tokens.expect_one_of("MULTIPLY", "DIVIDE")
        right = _parse_factor(tokens)
        left = BinOp(
            location=left.location, operation=tok_op.value, left=left, right=right
        )

    return left


def _parse_factor(tokens: "_TokenStream") -> Expression:
    if tokens.peek("INTEGER"):
        return _parse_integer(tokens)
    elif tokens.peek("FLOAT"):
        return _parse_float(tokens)
    elif tokens.peek("TRUE"):
        return _parse_true(tokens)
    elif tokens.peek("FALSE"):
        return _parse_false(tokens)
    elif tokens.peek("CHAR"):
        return _parse_character(tokens)
    elif tokens.peek_all("NAME", "OPEN_PARENS"):
        return _parse_func_call(tokens)
    elif tokens.peek("NAME"):
        return _parse_name(tokens)
    elif tokens.peek_one_of("SUB", "ADD", "LOGICAL_NOT"):
        return _parse_unaryop(tokens)
    elif tokens.peek("OPEN_PARENS"):
        tokens.expect("OPEN_PARENS")
        factor = _parse_expression(tokens)
        tokens.expect("CLOSE_PARENS")
        return factor
    else:
        tokens.print_debug_info()
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


def _parse_character(tokens: "_TokenStream") -> Character:
    t = tokens.expect("CHAR")
    value = t.value[1:-1]  # 'a' -> a
    if value == "\\n":
        value = "\n"
    return Character(location=t.pos, value=value)


def _parse_func_def(tokens: "_TokenStream") -> FuncDef:
    t1 = tokens.expect("FUNC")
    func_name = _parse_name(tokens)

    tokens.expect("OPEN_PARENS")
    func_args = []
    while not tokens.peek("CLOSE_PARENS"):
        func_args.append(_parse_func_arg(tokens))
        if tokens.peek("COMMA"):
            tokens.expect("COMMA")
    tokens.expect("CLOSE_PARENS")

    ret_type = _parse_type(tokens)
    body = _parse_statements_block(tokens)

    return FuncDef(
        location=t1.pos, name=func_name, args=func_args, return_type=ret_type, body=body
    )


def _parse_func_arg(tokens: "_TokenStream") -> FuncArg:
    name = _parse_name(tokens)
    type_ = _parse_type(tokens)
    return FuncArg(location=name.location, name=name, type_=type_)


def _parse_func_call(tokens: "_TokenStream") -> FuncCall:
    func_name = _parse_name(tokens)
    tokens.expect("OPEN_PARENS")

    args = []
    while not tokens.peek("CLOSE_PARENS"):
        args.append(_parse_expression(tokens))
        if tokens.peek("COMMA"):
            tokens.expect("COMMA")

    tokens.expect("CLOSE_PARENS")

    return FuncCall(location=func_name.location, name=func_name, args=args)


def _parse_unaryop(tokens: "_TokenStream") -> UnaryOp:
    t1 = tokens.expect_one_of("SUB", "ADD", "LOGICAL_NOT")
    val = _parse_factor(tokens)
    match t1.type:
        case "SUB":
            op = "-"
        case "ADD":
            op = "+"
        case "LOGICAL_NOT":
            op = "!"
        case _:
            assert False, f"Unexpected token for unary operator {t1.value}"

    return UnaryOp(location=t1.pos, operation=op, operand=val)


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

    def peek_all(self, *tok_types: TokenType) -> Token | None:
        if self.eof():
            return None

        if self._curr_token + len(tok_types) >= len(self._tokens):
            return None

        end = self._curr_token + len(tok_types)
        all_match = all(
            [
                tok_exp_type[0].type == tok_exp_type[1]
                for tok_exp_type in zip(self._tokens[self._curr_token : end], tok_types)
            ]
        )
        if all_match:
            return self._tokens[self._curr_token]

    def expect(self, toktype: TokenType) -> Token:
        if self.current().type != toktype:
            self.print_debug_info()
            raise WabbitSyntaxError(
                f"Expected token '{toktype}' but was '{self.current()}'"
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

    def print_debug_info(self) -> None:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("Last 5 tokens finished parsing:")
        start = max(self._curr_token - 5, 0)
        print(self._tokens[start : self._curr_token])
        print("-------------------------------")
        print("Next 5 tokens to parse:")
        end = min(self._curr_token + 5, len(self._tokens))
        print(self._tokens[self._curr_token : end])
        print("-------------------------------")
