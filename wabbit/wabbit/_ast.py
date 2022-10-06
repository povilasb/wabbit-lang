"""A wabbit data model - AST declarations.

Ideally I would like this to be CST (Concrete Syntax Tree) to preserve whitespaces
and comments for re-formatting.

Using `pydantic` to

1. reduce boilerplate defining the data classes,
1. easy AST serialization into JSON.
"""

import typing as t

from pydantic import BaseModel


class Node(BaseModel):
    """Base AST node."""

    location: int | None = None
    """Each node should have a location in original source code so that we could pin
    point the errors to.

    Optional for now so it would be easier to construct in tests.
    """


class Statement(Node):
    """Used to label the node is a statement rather than an expression."""


class Expression(Node):
    """Used to label the node is an expression rather than a statement."""


class ExprAsStatement(Statement):
    """
    Expressions can sometimes be used in the position of statement. For example:

        x + y;
        a = b = 123;

    This class provides a "Statement" wrapper around an expression that's meant
    to capture this particular usage.
    """

    expr: Expression


class PrintStatement(Statement):
    """e.g. `print 123;"""

    value: Expression


class Integer(Expression):
    """e.g. `123`"""

    value: str


class Float(Expression):
    """e.g. `1.0`"""

    value: str


class Boolean(Expression):
    value: bool


class Type(Node):
    name: t.Literal["int"] | t.Literal["float"] | t.Literal["bool"] | t.Literal["char"]


class Name(Expression):
    """Either function or variable name."""

    value: str


# TODO(povilas): do I want to restrict possible node types in the AST declaration?
# e.g. Integer | Float
# Or is this more of a job to a type checker?
class BinOp(Expression):
    """Binary operation."""

    operation: t.Literal["+"] | t.Literal["-"] | t.Literal["*"] | t.Literal["/"]
    left: Node
    right: Node

    @classmethod
    def add(cls, l: Node, r: Node) -> "BinOp":
        return cls(left=l, right=r, operation="+")

    @classmethod
    def sub(cls, l: Node, r: Node) -> "BinOp":
        return cls(left=l, right=r, operation="-")

    @classmethod
    def mul(cls, l: Node, r: Node) -> "BinOp":
        return cls(left=l, right=r, operation="*")

    @classmethod
    def div(cls, l: Node, r: Node) -> "BinOp":
        return cls(left=l, right=r, operation="/")


class UnaryOp(Expression):
    operation: t.Literal["-"] | t.Literal["!"]
    # TODO(povilas): Expression?
    operand: Node


class LogicalOp(Expression):
    operation: t.Literal["=="] | t.Literal[">"] | t.Literal["<"] | t.Literal[
        "&&"
    ] | t.Literal["||"]
    left: Expression
    right: Expression


class ParenExpr(Expression):
    """Parenthesis around expression.

    e.g. `(1)`
    """

    value: Node


class VarDecl(Statement):
    """Variable declaration.

    Either type or initial value must be specified.

    `var n int = 1;`
    """

    name: Name
    type_: Type | None = None
    """Type is optional, e.g. when it is inferred:

    ```
    var radius = 4.0;
    ```
    """
    value: Expression | None = None


class ConstDecl(Statement):
    """`const n int = 1;`"""

    name: Name
    value: Expression
    type_: Type | None = None
    """Type is optional as it is inferred from the initial `value`."""


class Assignment(Expression):
    left: Name
    right: Expression


class Statements(Node):
    """A container for multiple statements/expressions."""

    # TODO(povilas): pydantic does some unexpected type guessing and say
    # Assignment(Expression) becomes a Statement.
    # nodes: list[Statement | Expression]
    nodes: list[Node]


class IfElse(Statement):
    test: Expression
    body: Statements = Statements(nodes=[])
    else_body: Statements | None = None


class While(Statement):
    test: Expression
    body: Statements = Statements(nodes=[])


class Break(Statement):
    """Just a placeholder for the `break;` statement."""

    pass


class Continue(Statement):
    """Just a placeholder for the `continue;` statement."""

    pass


class FuncArg(Node):
    """Encodes single function argument:

        `x int`

    e.g. in `func add(x int, y int) int`
    """

    name: Name
    type_: Type


class FuncDef(Node):
    name: Name
    args: list[FuncArg]
    return_type: Type
    body: Statements = Statements(nodes=[])


class Return(Statement):
    """Function return statement."""

    value: Expression


class FuncCall(Expression):
    name: Name
    args: list[Expression]


# TODO(povilas): optionally retain comments: for reformatting and automated refactoring
class BlockComment(Node):
    value: str


class LineComment(Node):
    value: str


class Visitor:
    """Extend this to traverse the AST and apply custom actions on each node."""

    def visit(self, node: Node) -> t.Any:
        methname = "visit_" + type(node).__name__
        meth = getattr(self, methname, None)
        assert meth, f"Visitor method does not exist: {methname}"
        return meth(node)

    def visit_Integer(self, node: Integer) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Float(self, node: Float) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Boolean(self, node: Boolean) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Type(self, node: Type) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Name(self, node: Name) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_BinOp(self, node: BinOp) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_UnaryOp(self, node: UnaryOp) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_LogicalOp(self, node: LogicalOp) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_ParenExpr(self, node: ParenExpr) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_VarDecl(self, node: VarDecl) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_ConstDecl(self, node: ConstDecl) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Assignment(self, node: Assignment) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_ExprAsStatement(self, node: ExprAsStatement) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_IfElse(self, node: IfElse) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_While(self, node: While) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Break(self, node: Break) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Continue(self, node: Continue) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Statements(self, node: Statements) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_FuncArg(self, node: FuncArg) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_FuncDef(self, node: FuncDef) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_Return(self, node: Return) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_FuncCall(self, node: FuncCall) -> t.Any:
        raise RuntimeError("Not implemented")

    def visit_PrintStatement(self, node: PrintStatement) -> t.Any:
        raise RuntimeError("Not implemented")
