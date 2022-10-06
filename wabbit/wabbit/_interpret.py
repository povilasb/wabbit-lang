"""A simple (but slow) Wabbit language interpreter."""

import typing as t

from ._ast import *
from ._errors import WabbitRuntimeError, WabbitTypeError


def interpret(ast: Node) -> None:
    """Interpret the given Wabbit program AST."""
    _Interpreter().visit(ast)


_DataTypes: t.TypeAlias = int | float | bool | str


class _UnsupportedOperation(WabbitRuntimeError):
    def __init__(self, data_type: type[_DataTypes], operation: "str") -> None:
        msg = f"Unsupported operation '{operation}' with '{data_type}'"
        super().__init__(msg)


class _Interpreter(Visitor):
    """
    Expressions return a value, Statements do not.
    """

    def __init__(self) -> None:
        # A stack of execution contexts: from global to local ones when going into a
        # function or if/while block.
        self._exec_ctx = [_ExecCtx()]

    def visit_Integer(self, node: Integer) -> "_IntegerVar":
        return _IntegerVar(int(node.value))

    def visit_Float(self, node: Float) -> "_FloatVar":
        return _FloatVar(float(node.value))

    def visit_Boolean(self, node: Boolean) -> "_BooleanVar":
        return _BooleanVar(node.value)

    def visit_Name(self, node: Name) -> "_DataType":
        ctx = self._curr_ctx()
        if node.value in ctx.variables:
            return ctx.variables[node.value]
        if node.value in ctx.constants:
            return ctx.constants[node.value]

        raise WabbitRuntimeError(f"Undefined variable '{node.value}'")

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        res = self.visit(node.value)
        # TODO(povilas): assert type _DataType
        print(res.value)

    def visit_BinOp(self, node: BinOp) -> t.Any:
        val1 = self.visit(node.left)
        val2 = self.visit(node.right)

        match node.operation:
            case "+":
                return val1.add(val2)
            case "-":
                return val1.sub(val2)
            case "*":
                return val1.mul(val2)
            case "/":
                return val1.div(val2)

    def visit_UnaryOp(self, node: UnaryOp) -> t.Any:
        match node.operation:
            case "-":
                val = self.visit(node.operand)
                return val.unary_minus()

            case "!":
                val = self.visit(node.operand)
                return val.logical_not()

            case _:
                raise WabbitRuntimeError(f"Unknown unary operator '{node.operation}'")

    def visit_LogicalOp(self, node: LogicalOp) -> bool:
        left = self.visit(node.left)
        right = self.visit(node.right)
        match node.operation:
            case "==":
                return left == right
            case ">":
                return left > right
            case "<":
                return left < right
            case "&&":
                return left and right
            case "||":
                return left or right

    def visit_ParenExpr(self, node: ParenExpr) -> t.Any:
        return self.visit(node.value)

    def visit_Statements(self, node: Statements) -> None:
        for s in node.nodes:
            self.visit(s)

    def visit_ExprAsStatement(self, node: ExprAsStatement) -> None:
        self.visit(node.expr)

    def visit_VarDecl(self, node: VarDecl) -> t.Any:
        variables = self._curr_ctx().variables
        var_name = node.name.value
        if var_name in variables:
            raise WabbitRuntimeError("Variable '{var_name}' was already declared.")

        variables[var_name] = _default_var_type(node)

    def visit_ConstDecl(self, node: ConstDecl) -> t.Any:
        variables = self._curr_ctx().variables
        var_name = node.name.value
        if var_name in variables:
            raise WabbitRuntimeError("Constant '{var_name}' was already declared.")

        variables[var_name] = self.visit(node.value)

    def visit_Assignment(self, node: Assignment) -> t.Any:
        assert isinstance(node.left, Name)
        var_name = node.left.value

        value = self.visit(node.right)
        # TODO(povilas): test if var_name exists
        # TODO(povilas): test if var_name is not a constat
        self._curr_ctx().variables[var_name] = value

    def visit_IfElse(self, node: IfElse) -> None:
        test_res = self.visit(node.test)
        if type(test_res) is not bool:
            raise WabbitRuntimeError(
                f"If condition mus evaluate to boolean. Rather it was '{type(test_res)}'"
            )

        if test_res:
            self.visit(node.body)
        elif else_body := node.else_body:
            self.visit(else_body)

    def visit_While(self, node: While) -> None:
        while True:
            test_res = self.visit(node.test)
            if type(test_res) is not bool:
                raise WabbitRuntimeError(
                    f"If condition mus evaluate to boolean. Rather it was '{type(test_res)}'"
                )

            if test_res:
                self.visit(node.body)
            else:
                break

    # TODO(povilas): function def and call

    def _curr_ctx(self) -> "_ExecCtx":
        assert (
            len(self._exec_ctx) > 0
        ), "At all times there should be at least 1 execution context."
        return self._exec_ctx[-1]


class _ExecCtx(BaseModel):
    variables: dict[str, "_DataType"] = {}
    constants: dict[str, "_DataType"] = {}


class _DataType:
    """Handles Wabbit data type operations."""

    type_: t.ClassVar[type[_DataTypes]] = int

    def __init__(self, value: _DataTypes) -> None:
        self.value = value

    @classmethod
    def default(cls) -> "_DataType":
        raise _UnsupportedOperation(cls.type_, "default")

    def add(self, other: "_DataType") -> "_DataType":
        return type(self)(self.value + self._assert_same_type(other).value)

    def sub(self, other: "_DataType") -> _DataTypes:
        return type(self)(self.value - self._assert_same_type(other).value)

    def mul(self, other: "_DataType") -> _DataTypes:
        return type(self)(self.value * self._assert_same_type(other).value)

    def div(self, other: "_DataType") -> _DataTypes:
        return type(self)(self.value / self._assert_same_type(other).value)

    def unary_minus(self) -> _DataTypes:
        raise _UnsupportedOperation(self.type_, "-x")

    def cmp_eq(self, other: "_DataType") -> _DataTypes:
        return self.value == self._assert_same_type(other).value

    def cmp_not_eq(self, other: "_DataType") -> _DataTypes:
        return self.value != self._assert_same_type(other).value

    def cmp_less(self, other: "_DataType") -> _DataTypes:
        return self.value < self._assert_same_type(other).value

    def cmp_less_eq(self, other: "_DataType") -> _DataTypes:
        return self.value <= self._assert_same_type(other).value

    def cmp_more(self, other: "_DataType") -> _DataTypes:
        return self.value > self._assert_same_type(other).value

    def cmp_more_eq(self, other: "_DataType") -> _DataTypes:
        return self.value >= self._assert_same_type(other).value

    def logical_not(self) -> _DataTypes:
        raise _UnsupportedOperation(self.type_, "!")

    def logical_and(self, other: "_DataType") -> _DataTypes:
        raise _UnsupportedOperation(self.type_, "&&")

    def logical_or(self, other: "_DataType") -> _DataTypes:
        raise _UnsupportedOperation(self.type_, "||")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value})"

    def _assert_same_type(self, other: "_DataType") -> "_DataType":
        if self.type_ != other.type_:
            raise WabbitTypeError(
                f"Incompatible types '{self.type_.__name__}' and '{other.type_.__name__}"
            )
        return other


class _IntegerVar(_DataType):
    type_ = int

    @classmethod
    def default(cls) -> "_IntegerVar":
        return cls(0)

    def div(self, other: "_DataType") -> "_IntegerVar":
        return type(self)(int(self.value / self._assert_same_type(other).value))

    def unary_minus(self) -> "_IntegerVar":
        return type(self)(-self.value)


class _FloatVar(_DataType):
    type_ = float

    @classmethod
    def default(cls) -> "_FloatVar":
        return cls(0.0)

    def unary_minus(self) -> "_FloatVar":
        return type(self)(-self.value)


class _BooleanVar(_DataType):
    type_ = bool

    @classmethod
    def default(cls) -> "_BooleanVar":
        return cls(False)

    def logical_not(self) -> "_BooleanVar":
        return type(self)(not self.value)

    def logical_and(self, other: "_DataType") -> "_BooleanVar":
        return type(self)(self.value and self._assert_same_type(other).value)

    def logical_or(self, other: "_DataType") -> "_BooleanVar":
        return type(self)(self.value or self._assert_same_type(other).value)


def _default_var_type(node: VarDecl) -> _DataType:
    match node.type_:
        case Type(name="int"):
            return _IntegerVar.default()
        case Type(name="float"):
            return _FloatVar.default()
        case Type(name="bool"):
            return _BooleanVar.default()
        case Type(name="char"):
            assert False, f"Unknown variable type: {node.type_}"
        case _:
            assert False, f"Unknown variable type: {node.type_}"
