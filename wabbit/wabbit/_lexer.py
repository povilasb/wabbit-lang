"""Lexical Wabbit language analysis."""

from ._errors import WabbitSyntaxError


class Token:
    def __init__(self, type_: str, value: str, pos: int) -> None:
        self.type = type_
        self.value = value
        self.pos = pos

    def __eq__(self, o: "Token") -> bool:
        return self.type == o.type and self.value == o.value and self.pos == o.pos

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.type}, {self.value}, {self.pos})"


_SYMBOL_TOKENS = {
    "+": "ADD",
    "-": "SUB",
    "*": "MULTIPLY",
    "/": "DIVIDE",
    "<": "LESS",
    ">": "MORE",
    "=": "EQUAL",
    "<=": "LESS_EQ",
    ">=": "MORE_EQ",
    "==": "DOUBLE_EQ",
    "!=": "NOT_EQ",
    "!": "LOGICAL_NOT",
    "&&": "LOGICAL_AND",
    "||": "LOGICAL_OR",
    "(": "OPEN_PARENS",
    ")": "CLOSE_PARENS",
    "{": "OPEN_CURLY_BRACE",
    "}": "CLOSE_CURLY_BRACE",
    ";": "SEMICOLON",
    ",": "COMMA",
}

# TODO(povilas): add int, float, bool, char
_KEYWORDS = {
    "print",
    "var",
    "const",
    "if",
    "else",
    "while",
    "break",
    "continue",
    "func",
    "return",
    "true",
    "false",
}


def tokenize(text: str) -> list[Token]:
    pos = 0
    tokens: list[Token] = []

    while pos < len(text):
        # NOTE: order matters - match comments first, float before int, etc.
        if m := match_block_comment(text, pos):
            pass
        elif m := match_line_comment(text, pos):
            pass

        elif m := match_name(text, pos):
            if m in _KEYWORDS:
                tokens.append(Token(m.upper(), m, pos))
            else:
                tokens.append(Token("NAME", m, pos))

        elif m := match_float(text, pos):
            tokens.append(Token("FLOAT", m, pos))
        elif m := match_digits(text, pos):
            tokens.append(Token("INTEGER", m, pos))

        elif m := match_symbol(text, pos):
            tokens.append(Token(_SYMBOL_TOKENS[m], m, pos))

        elif m := match_whitespace(text, pos):
            pass
        else:
            raise WabbitSyntaxError(
                f"Could not match a token at position {pos}: '{text[pos:pos+10]}...'"
            )

        pos += len(m)

    return tokens


def match_digits(text: str, start: int = 0) -> str:
    n = start
    while n < len(text) and text[n].isdigit():
        n += 1
    return text[start:n]


assert match_digits("12345") == "12345"
assert match_digits("abc") == ""  # Doesn't start with digit
assert match_digits("acb123") == ""
assert match_digits("123 abc") == "123"
assert match_digits("123abc456") == "123"  # Stops with first non-digit


def match_name(text: str, start: int = 0) -> str:
    n = start
    while n < len(text) and (text[n].isalpha() or text[n] == "_"):
        n += 1

    if n == start:
        return ""

    suffix = match_digits(text[n:]) if n > 0 else ""
    return text[start:n] + suffix


assert match_name("print") == "print"
assert match_name("123") == ""
assert match_name("abc_123") == "abc_123"
assert match_name("abc 123") == "abc"


def match_symbol(text: str, start: int = 0) -> str:
    symbols1 = {"+", "-", "*", "/", "<", ">", "=", "(", ")", "{", "}", ";", "!", ","}
    symbols2 = {"<=", ">=", "==", "&&", "||", "!="}

    if start + 2 <= len(text) and text[start : start + 2] in symbols2:
        return text[start : start + 2]

    if start < len(text) and text[start] in symbols1:
        return text[start]

    return ""


assert match_symbol("+") == "+"
assert match_symbol("<=") == "<="
assert match_symbol("<+") == "<"  # <+ is not a valid Wabbit symbol. But < is.
assert match_symbol("abc") == ""
assert match_symbol("print true && true", 11) == "&&"


def match_block_comment(text: str, start: int = 0) -> str:
    if len(text) < start + 4:
        return ""

    if text[start : start + 2] != "/*":
        return ""

    n = start + 2
    while n < len(text) and text[n] != "*":
        n += 1
    n += 1  # skip '*'

    if text[n] == "/":
        return text[start : n + 1]

    return ""


assert match_block_comment("/**/") == "/**/"
assert match_block_comment("/* Comment */") == "/* Comment */"
assert match_block_comment("/* Line1\nLine2\n */") == "/* Line1\nLine2\n */"
assert match_block_comment("123 /* Line1\nLine2\n */", 4) == "/* Line1\nLine2\n */"


def match_line_comment(text: str, start: int = 0) -> str:
    if len(text) < start + 2:
        return ""

    if not text[start : start + 2] == "//":
        return ""

    n = start + 2
    while n < len(text) and text[n] != "\n":
        n += 1

    if text[n] == "\n":
        return text[start : n + 1]

    return ""


assert match_line_comment("// Comment\n") == "// Comment\n"


def match_float(text: str, start: int = 0) -> str:
    if digits := match_digits(text, start):
        dot_pos = start + len(digits)
        if dot_pos >= len(text) or not text[dot_pos] == ".":
            return ""

        if more_digits := match_digits(text, dot_pos + 1):
            return text[start : dot_pos + len(more_digits) + 1]

        return text[start : dot_pos + 1]

    elif text[start] == "." and (digits := match_digits(text, start + 1)):
        return text[start : len(digits) + 1]

    return ""


assert match_float("3.14159") == "3.14159"
assert match_float("abc 1.2", 4) == "1.2"
assert match_float("123") == ""  # Floats must have "."
assert match_float(".123") == ".123"
assert match_float("1.") == "1."
assert match_float(".") == ""


def match_whitespace(text: str, start: int = 0) -> str:
    n = start
    while n < len(text) and text[n].isspace():
        n += 1
    return text[start:n]


assert match_whitespace("abc") == ""
assert match_whitespace(" abc") == " "
assert match_whitespace("   abc") == "   "

assert tokenize("print 123 + 1.2;") == [
    Token("PRINT", "print", 0),
    Token("INTEGER", "123", 6),
    Token("ADD", "+", 10),
    Token("FLOAT", "1.2", 12),
    Token("SEMICOLON", ";", 15),
]
