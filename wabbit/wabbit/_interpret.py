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
        # TODO(povilas): move functions to global context

    def visit_Integer(self, node: Integer) -> "_IntegerVar":
        return _IntegerVar(int(node.value))

    def visit_Float(self, node: Float) -> "_FloatVar":
        return _FloatVar(float(node.value))

    def visit_Boolean(self, node: Boolean) -> "_BooleanVar":
        return _BooleanVar(node.value)

    def visit_Character(self, node: Character) -> "_CharVar":
        return _CharVar(node.value)

    def visit_Name(self, node: Name) -> "_DataType":
        ctx = self._curr_ctx()
        if node.value in ctx.variables:
            return ctx.variables[node.value]
        if node.value in ctx.constants:
            return ctx.constants[node.value]

        raise WabbitRuntimeError(f"Undefined variable '{node.value}'")

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        res: _DataType = self.visit(node.value)
        # TODO(povilas): assert type _DataType
        print(res.value, end="")

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

    def visit_UnaryOp(self, node: UnaryOp) -> "_DataType":
        match node.operation:
            case "-":
                val = self.visit(node.operand)
                return val.unary_minus()

            case "+":
                val = self.visit(node.operand)
                return val.unary_plus()

            case "!":
                val = self.visit(node.operand)
                return val.logical_not()

            case _:
                raise WabbitRuntimeError(f"Unknown unary operator '{node.operation}'")

    def visit_LogicalOp(self, node: LogicalOp) -> "_DataType":
        left = self.visit(node.left)
        right = self.visit(node.right)
        match node.operation:
            case "==":
                return left.cmp_eq(right)
            case "!=":
                return left.cmp_not_eq(right)
            case ">":
                return left.cmp_more(right)
            case ">=":
                return left.cmp_more_eq(right)
            case "<":
                return left.cmp_less(right)
            case "<=":
                return left.cmp_less_eq(right)
            case "&&":
                return left.logical_and(right)
            case "||":
                return left.logical_or(right)
            case _:
                raise RuntimeError("not possible")

    def visit_ParenExpr(self, node: ParenExpr) -> t.Any:
        return self.visit(node.value)

    def visit_Statements(self, node: Statements) -> t.Any:
        res = None
        for s in node.nodes:
            res = self.visit(s)

        # This is only to cater a `return` statement.
        return res

    def visit_ExprAsStatement(self, node: ExprAsStatement) -> None:
        self.visit(node.expr)

    def visit_VarDecl(self, node: VarDecl) -> None:
        var_name = node.name.value
        variables = self._curr_ctx().variables
        if var_name in variables or var_name in self._curr_ctx().constants:
            raise WabbitRuntimeError("Variable '{var_name}' was already declared.")

        if node.value:
            val = self.visit(node.value)
        else:
            val = _default_var_type(node)

        variables[var_name] = val

    def visit_ConstDecl(self, node: ConstDecl) -> None:
        constants = self._curr_ctx().constants
        var_name = node.name.value
        if var_name in constants or var_name in self._curr_ctx().variables:
            raise WabbitRuntimeError("Constant '{var_name}' was already declared.")

        constants[var_name] = self.visit(node.value)

    def visit_FuncArg(self, farg_node: FuncArg) -> "_VarDef":
        return _VarDef(type_=_var_type(farg_node.type_), name=farg_node.name.value)

    def visit_FuncDef(self, func_def: FuncDef) -> None:
        args = [self.visit_FuncArg(a) for a in func_def.args]
        ret_type = _var_type(func_def.return_type)
        func_name = func_def.name.value
        f = _Function(name=func_name, args=args, ret_type=ret_type, body=func_def.body)
        self._curr_ctx().functions[func_name] = f

    def visit_FuncCall(self, callf: FuncCall) -> t.Any:
        func = self._curr_ctx().functions[callf.name.value]

        func_ctx = _ExecCtx()
        func_ctx.functions = self._curr_ctx().functions
        for argi, arg in enumerate(callf.args):
            arg_value = self.visit(arg)
            func_ctx.variables[func.args[argi].name] = arg_value

        self._exec_ctx.append(func_ctx)

        # Each function should have a return statement last.
        res = self.visit(func.body)
        self._exec_ctx.pop()
        return res

    def visit_Return(self, node: Return) -> _DataTypes:
        res = self.visit(node.value)
        return res

    def visit_Assignment(self, node: Assignment) -> "_DataType":
        assert isinstance(node.left, Name)
        var_name = node.left.value

        value = self.visit(node.right)
        self._curr_ctx().variables[var_name] = value

        return value

    def visit_IfElse(self, node: IfElse) -> None:
        test_res = self.visit(node.test)
        if type(test_res) is not _BooleanVar:
            raise WabbitRuntimeError(
                f"If condition mus evaluate to boolean. Rather it was '{test_res}'"
            )

        if test_res.value:
            self.visit(node.body)
        elif else_body := node.else_body:
            self.visit(else_body)

    def visit_While(self, node: While) -> None:
        while True:
            test_res = self.visit(node.test)
            if type(test_res) is not _BooleanVar:
                raise WabbitRuntimeError(
                    f"If condition mus evaluate to boolean. Rather it was '{type(test_res)}'"
                )

            if test_res.value:
                self.visit(node.body)
            else:
                break

    def _curr_ctx(self) -> "_ExecCtx":
        assert (
            len(self._exec_ctx) > 0
        ), "At all times there should be at least 1 execution context."
        return self._exec_ctx[-1]


class _ExecCtx(BaseModel):
    variables: dict[str, "_DataType"] = {}
    # TODO(povilas): rm and do const checking before interpreting
    constants: dict[str, "_DataType"] = {}
    functions: dict[str, "_Function"] = {}


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

    def unary_plus(self) -> _DataTypes:
        raise _UnsupportedOperation(self.type_, "+x")

    def cmp_eq(self, other: "_DataType") -> _DataTypes:
        return _BooleanVar(self.value == self._assert_same_type(other).value)

    def cmp_not_eq(self, other: "_DataType") -> _DataTypes:
        return _BooleanVar(self.value != self._assert_same_type(other).value)

    def cmp_less(self, other: "_DataType") -> _DataTypes:
        return _BooleanVar(self.value < self._assert_same_type(other).value)

    def cmp_less_eq(self, other: "_DataType") -> _DataTypes:
        return _BooleanVar(self.value <= self._assert_same_type(other).value)

    def cmp_more(self, other: "_DataType") -> _DataTypes:
        return _BooleanVar(self.value > self._assert_same_type(other).value)

    def cmp_more_eq(self, other: "_DataType") -> _DataTypes:
        return _BooleanVar(self.value >= self._assert_same_type(other).value)

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

    def unary_plus(self) -> "_IntegerVar":
        return self


class _FloatVar(_DataType):
    type_ = float

    @classmethod
    def default(cls) -> "_FloatVar":
        return cls(0.0)

    def unary_minus(self) -> "_FloatVar":
        return type(self)(-self.value)

    def unary_plus(self) -> "_FloatVar":
        return self


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


class _CharVar(_DataType):
    type_ = str

    @classmethod
    def default(cls) -> "_CharVar":
        return cls("\0")


class _VarDef(BaseModel):
    # TODO(povilas): I'm using the in | float | bool ... types here
    # But all I really need is some placeholders like TInt that I could later map
    # To the interpreted environment type like 'int'.
    type_: type[_DataTypes]
    name: str


class _Function(BaseModel):
    """Wabbit functions are not first class citizens and thus do not derive from
    _DataType."""

    name: str
    args: list[_VarDef]
    ret_type: type[_DataTypes]
    body: Statements


def _default_var_type(node: VarDecl) -> _DataType:
    match node.type_:
        case Type(name="int"):
            return _IntegerVar.default()
        case Type(name="float"):
            return _FloatVar.default()
        case Type(name="bool"):
            return _BooleanVar.default()
        case Type(name="char"):
            return _CharVar.default()
        case _:
            assert False, f"Unknown variable type: {node.type_}"


def _var_type(node: Type) -> type[_DataTypes]:
    match node:
        case Type(name="int"):
            return int
        case Type(name="float"):
            return float
        case Type(name="bool"):
            return bool
        case Type(name="char"):
            return str
        case _:
            assert False, f"Unknown variable type: {node}"
