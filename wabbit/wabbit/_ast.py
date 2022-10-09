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


class PrintStatement(Node):
    """e.g. `print 123;"""

    value: Node


class Integer(Node):
    """e.g. `123`"""

    value: str


class Float(Node):
    """e.g. `1.0`"""

    value: str


class Boolean(Node):
    value: bool


# TODO(povilas): do I want to restrict possible node types in the AST declaration?
# e.g. Integer | Float
# Or is this more of a job to a type checker?
class BinOp(Node):
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


class UnaryOp(Node):
    operation: t.Literal["-"] | t.Literal["!"]
    operand: Node


class LogicalOp(Node):
    operation: t.Literal["=="] | t.Literal[">"] | t.Literal["<"] | t.Literal[
        "&&"
    ] | t.Literal["||"]
    left: Node
    right: Node


class ParenExpr(Node):
    """Parenthesis around expression.

    e.g. `(1)`
    """

    value: Node


class Name(Node):
    """Either function or variable name."""

    value: str


class VarDecl(Node):
    """Variable declaration."""

    specifier: t.Literal["const"] | t.Literal["var"]
    # TODO(povilas): wrap it with a node Name()
    name: str
    type_: str | None = None
    """Type is optional, e.g. when it is inferred:

    ```
    var radius = 4.0;
    ```
    """


class Assignment(Node):
    left: Node
    right: Node


class IfElse(Node):
    test: Node
    body: list[Node] | None = None
    else_body: list[Node] | None = None


# TODO(povilas): optionally retain comments: for reformatting and automated refactoring
class BlockComment(Node):
    value: str


class LineComment(Node):
    value: str
