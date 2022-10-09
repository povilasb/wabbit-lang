"""Formats source code from AST."""

import typing as t
import logging

from ._ast import *


_logger = logging.getLogger()


# TODO(povilas): take indentation into consideration for functions and if blocks
def format(node: Node, add_semicolon: bool = True, indent_level: int = 0) -> str:
    src = ""
    match node:
        case PrintStatement(value=inner_node):
            src = f"print {format(inner_node)};"

        case Integer(value=val) | Float(value=val):
            src = f"{val}"

        case Boolean(value=val):
            src = "true" if val else "false"

        case Name(value=name):
            src = name

        case BinOp(operation=op, left=left, right=right) | LogicalOp(
            operation=op, left=left, right=right
        ):
            src = f"{format(left)} {op} {format(right)}"

        case UnaryOp(operation=op, operand=operand):
            src = f"{op}{format(operand)}"

        case ParenExpr(value=val):
            src = f"({format(val)})"

        case Assignment(left=left, right=right):
            src = f"{format(left, add_semicolon=False)} = {format(right)};"

        case VarDecl(specifier=spec, name=name, type_=type_):
            type_suffix = f" {type_}" if type_ else ""
            maybe_semicolon = ";" if add_semicolon else ""
            src = f"{spec} {name}{type_suffix}{maybe_semicolon}"

        case IfElse(test=test, body=exec_body):
            lines = [
                f"if {format(test)} {{",
            ]
            lines += [
                format(node, indent_level=indent_level + 1)
                for node in (exec_body or [])
            ]
            lines.append("}")
            src = "\n".join(lines)

        case _:
            _logger.warning("Unsupported node type: %s", type(node))

    return " " * indent_level * 4 + src


class _Lines:
    """Helps to deal with indentation

    ```py
    with lines.indent():
        lines.append("indented")
    """

    indent_spaces: t.ClassVar[int] = 4

    def __init__(self) -> None:
        self._inner: list[str] = []
        self._indent_level: int = 0

    def __enter__(self) -> "_Lines":
        self._indent_level += 1
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self._indent_level -= 1

    def append(self, text: str) -> None:
        self._inner.append(" " * self._indent_level * self.indent_spaces + text)

    def indent(self) -> "_Lines":
        return self

    def __str__(self) -> str:
        """Format lines with indentation."""
        return "\n".join(self._inner)
