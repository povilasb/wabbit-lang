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
    operand: Node


class LogicalOp(Expression):
    operation: t.Literal["=="] | t.Literal[">"] | t.Literal["<"] | t.Literal[
        "&&"
    ] | t.Literal["||"]
    left: Node
    right: Node


class ParenExpr(Expression):
    """Parenthesis around expression.

    e.g. `(1)`
    """

    value: Node


class Name(Expression):
    """Either function or variable name."""

    value: str


class VarDecl(Statement):
    """Variable declaration."""

    specifier: t.Literal["const"] | t.Literal["var"]
    name: Name
    type_: Type | None = None
    """Type is optional, e.g. when it is inferred:

    ```
    var radius = 4.0;
    ```
    """


class Assignment(Expression):
    left: Node
    right: Node


class IfElse(Statement):
    test: Node
    body: list[Node] = []
    else_body: list[Node] | None = None


class While(Statement):
    test: LogicalOp | Boolean
    body: list[Node] = []


class Break(Statement):
    """Just a placeholder for the `break;` statement."""

    pass


class Continue(Statement):
    """Just a placeholder for the `continue;` statement."""

    pass


class Block(Node):
    """A container for multiple statements/expressions."""

    # TODO(povilas): pydantic does some unexpected type guessing and say
    # Assignment(Expression) becomes a Statement.
    # nodes: list[Statement | Expression]
    nodes: list[Node]


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
    body: list[Node] = []


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
