"""A simple (but slow) Wabbit language interpreter."""

import typing as t

from ._ast import *


class WabbitError(Exception):
    pass


class WabbitTypeError(WabbitError):
    pass


class WabbitRuntimeError(WabbitError):
    pass


def interpret(ast: Node) -> None:
    """Interpret the given Wabbit program AST."""
    _Interpreter().visit(ast)


class _Interpreter(Visitor):
    def __init__(self) -> None:
        # A stack of execution contexts: from global to local ones when going into a
        # function or if/while block.
        self._exec_ctx = [_ExecCtx()]

    def visit_Integer(self, node: Integer) -> int:
        return int(node.value)

    def visit_Float(self, node: Float) -> float:
        return float(node.value)

    def visit_Boolean(self, node: Boolean) -> bool:
        return node.value

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        res = self.visit(node.value)
        print(res)

    def visit_BinOp(self, node: BinOp) -> t.Any:
        val1 = self.visit(node.left)
        val2 = self.visit(node.right)

        if type(val1) != type(val2):
            raise WabbitTypeError(
                "Binary operations are only possible with matching types.", val1, val2
            )

        match node.operation:
            case "+":
                return val1 + val2
            case "-":
                return val1 - val2
            case "*":
                return val1 * val2
            case "/":
                return val1 / val2

    def visit_UnaryOp(self, node: UnaryOp) -> t.Any:
        match node.operation:
            case "-":
                val = self.visit(node.operand)
                if type(val) not in (int, float):
                    raise WabbitTypeError(
                        f"Unary operator '{node.operation}' cannot be used with: "
                        f"{type(node.operand)}"
                    )
                return -val

            case "!":
                val = self.visit(node.operand)
                if type(val) != bool:
                    raise WabbitTypeError(
                        f"Binary not operator '{node.operation}' cannot be used with: "
                        f"{type(node.operand)}"
                    )
                return not val

            case _:
                raise WabbitRuntimeError(f"Unknown unary operator '{node.operation}'")

    def visit_ParenExpr(self, node: ParenExpr) -> t.Any:
        return self.visit(node.value)

    def visit_Statements(self, node: Statements) -> None:
        for s in node.nodes:
            self.visit(s)

    def visit_VarDecl(self, node: VarDecl) -> t.Any:
        variables = self._curr_ctx().variables
        var_name = node.name.value
        if var_name in variables:
            raise WabbitRuntimeError("Variable '{var_name}' was already declared.")

        variables[var_name] = _default_var_type(node)

    def visit_Assignment(self, node: Assignment) -> t.Any:
        assert isinstance(node.left, Name)
        var_name = node.left.value

        value = self.visit(node.right)
        self._curr_ctx().variables[var_name] = value

    def _curr_ctx(self) -> "_ExecCtx":
        assert (
            len(self._exec_ctx) > 0
        ), "At all times there should be at least 1 execution context."
        return self._exec_ctx[-1]


class _ExecCtx(BaseModel):
    variables: dict[str, int | float | bool | str] = {}


def _default_var_type(node: VarDecl) -> int | float | bool | str:
    match node.type_:
        case Type(name="int"):
            return 0
        case Type(name="float"):
            return 0.0
        case Type(name="bool"):
            return False
        case Type(name="char"):
            return " "
        case _:
            assert False, f"Unknown variable type: {node.type_}"
