"""Formats source code from AST."""

import typing as t

from ._ast import *


_INDENT_SPACES: t.Final[int] = 4


def format(node: Node) -> str:
    return _FormatVisitor().visit(node)


class _FormatVisitor(Visitor):
    def __init__(self) -> None:
        self._indent_level = 0
        # Adds contextual info not to add a redundant semicolon: `var v1 int; = 4;`
        self._in_assignment = False

    # TODO(povilas): use beartype to ensure str is returned?
    def visit(self, node: Node) -> str:
        return super().visit(node)

    def visit_Integer(self, node: Integer) -> str:
        return str(node.value)

    def visit_Float(self, node: Float) -> str:
        return str(node.value)

    def visit_Boolean(self, node: Boolean) -> str:
        return "true" if node.value else "false"

    def visit_Name(self, node: Name) -> str:
        return node.value

    def visit_PrintStatement(self, node: PrintStatement) -> str:
        return f"print {self.visit(node.value)};"

    def visit_Break(self, node: Break) -> str:
        return "break;"

    def visit_Continue(self, node: Continue) -> str:
        return "continue;"

    def visit_BinOp(self, node: BinOp) -> str:
        return f"{self.visit(node.left)} {node.operation} {self.visit(node.right)}"

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        return f"{node.operation}{self.visit(node.operand)}"

    def visit_LogicalOp(self, node: LogicalOp) -> str:
        return f"{self.visit(node.left)} {node.operation} {self.visit(node.right)}"

    def visit_ParenExpr(self, node: ParenExpr) -> str:
        return f"({self.visit(node.value)})"

    def visit_Assignment(self, node: Assignment) -> str:
        self._in_assignment = True
        res = f"{self.visit(node.left)} = {self.visit(node.right)};"
        self._in_assignment = False
        return res

    def visit_VarDecl(self, node: VarDecl) -> str:
        type_suffix = f" {node.type_.name}" if node.type_ else ""
        maybe_semicolon = ";" if not self._in_assignment else ""
        return f"{node.specifier} {node.name.value}{type_suffix}{maybe_semicolon}"

    def visit_Statements(self, node: Statements) -> str:
        return "\n".join(_indent(self.visit(n), self._indent_level) for n in node.nodes)

    def visit_IfElse(self, node: IfElse) -> str:
        lines = [
            f"if {self.visit(node.test)} {{",
        ]
        self._indent_level += 1
        lines.append(self.visit(node.body))
        self._indent_level -= 1

        if node.else_body is not None:
            lines.append(_indent("} else {", self._indent_level))
            self._indent_level += 1
            lines.append(self.visit(node.else_body))
            self._indent_level -= 1

        lines.append(_indent("}", self._indent_level))
        return "\n".join(lines)

    def visit_While(self, node: While) -> str:
        lines = [
            f"while {self.visit(node.test)} {{",
        ]
        self._indent_level += 1
        lines.append(self.visit(node.body))
        self._indent_level -= 1
        lines.append("}")
        return "\n".join(lines)

    def visit_FuncDef(self, node: FuncDef) -> str:
        formatted_args = ", ".join([self.visit(arg) for arg in node.args])
        lines = [f"func {node.name.value}({formatted_args}) {node.return_type.name} {{"]

        self._indent_level += 1
        lines.append(self.visit(node.body))
        self._indent_level -= 1

        lines.append("}")
        return "\n".join(lines)

    def visit_FuncArg(self, node: FuncArg) -> str:
        return f"{node.name.value} {node.type_.name}"

    def visit_Return(self, node: Return) -> str:
        return f"return {self.visit(node.value)};"

    def visit_FuncCall(self, node: FuncCall) -> str:
        formatted_args = ", ".join(self.visit(arg) for arg in node.args)
        return f"{node.name.value}({formatted_args})"


def _indent(text: str, indent_level: int) -> str:
    return " " * indent_level * _INDENT_SPACES + text
