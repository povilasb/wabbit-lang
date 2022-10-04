"""Formats source code from AST."""

import typing as t
import logging

from ._ast import *


_logger = logging.getLogger()

_INDENT_SPACES: t.Final[int] = 4


def format(node: Node, indent_level: int = 0, add_semicolon: bool = True) -> str:
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
            type_suffix = f" {type_.name}" if type_ else ""
            maybe_semicolon = ";" if add_semicolon else ""
            src = f"{spec} {name.value}{type_suffix}{maybe_semicolon}"

        case IfElse(test=test, body=exec_body, else_body=else_body):
            lines = [
                f"if {format(test)} {{",
            ]
            lines += [format(node, indent_level=indent_level + 1) for node in exec_body]

            if else_body is not None:
                lines.append(_indent("} else {", indent_level))
                lines += [
                    format(node, indent_level=indent_level + 1)
                    for node in (else_body or [])
                ]

            lines.append(_indent("}", indent_level))
            src = "\n".join(lines)

        case While(test=test, body=exec_body):
            lines = [
                f"while {format(test)} {{",
            ]
            lines += [format(node, indent_level=indent_level + 1) for node in exec_body]
            lines.append("}")
            src = "\n".join(lines)

        case Break():
            src = "break;"

        case Continue():
            src = "continue;"

        case Block(nodes=nodes):
            lines = [format(n, indent_level) for n in nodes]
            src = "\n".join(lines)

        case FuncDef(
            name=Name(value=func_name),
            args=args,
            return_type=Type(name=return_type),
            body=body,
        ):
            formatted_args = ", ".join([format(arg) for arg in args])
            lines = [f"func {func_name}({formatted_args}) {return_type} {{"]
            lines += [format(node, indent_level=indent_level + 1) for node in body]
            lines.append("}")
            src = "\n".join(lines)

        case FuncArg(name=Name(value=arg_name), type_=Type(name=arg_type)):
            src = f"{arg_name} {arg_type}"

        case Return(value=ret_expr):
            src = f"return {format(ret_expr)};"

        case FuncCall(name=Name(value=func_name), args=args):
            formatted_args = ", ".join(format(arg) for arg in args)
            src = f"{func_name}({formatted_args})"

        case _:
            _logger.warning("Unsupported node type: %s", type(node))

    return _indent(src, indent_level)


def _indent(src: str, indent_level: int) -> str:
    return " " * indent_level * _INDENT_SPACES + src
