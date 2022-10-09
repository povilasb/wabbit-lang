from ._ast import *
from ._format import format

# TODO(povilas): make this into a test suite
statements = [
    PrintStatement(value=Integer(value="42")),
    PrintStatement(value=BinOp.add(Integer(value="2"), Integer(value="3"))),
    PrintStatement(
        value=BinOp.add(
            UnaryOp(operation="-", operand=Integer(value="2")), Integer(value="3")
        )
    ),
    PrintStatement(
        value=BinOp.add(
            Integer(value="2"),
            BinOp.mul(Integer(value="3"), Integer(value="-4")),
        )
    ),
    PrintStatement(
        value=BinOp.mul(
            ParenExpr(
                value=BinOp.add(
                    Integer(value="2"),
                    Integer(value="3"),
                )
            ),
            Integer(value="4"),
        )
    ),
    PrintStatement(
        value=BinOp.sub(
            Float(value="2.0"),
            BinOp.div(Float(value="3.0"), Float(value="4.0")),
        )
    ),
    Assignment(
        left=VarDecl(specifier="const", name="pi"), right=Float(value="3.14159")
    ),
    Assignment(
        left=VarDecl(specifier="const", name="tau"),
        right=BinOp.mul(Float(value="2.0"), Name(value="pi")),
    ),
    Assignment(left=VarDecl(specifier="var", name="radius"), right=Float(value="4.0")),
    VarDecl(specifier="var", name="perimeter", type_="float"),
    Assignment(
        left=Name(value="perimeter"),
        right=BinOp.mul(Name(value="tau"), Name(value="radius")),
    ),
    PrintStatement(value=Name(value="perimeter")),
    Assignment(
        left=VarDecl(specifier="var", name="v1", type_="int"), right=Integer(value="4")
    ),
    PrintStatement(value=UnaryOp(operation="-", operand=Name(value="x"))),
    PrintStatement(value=Boolean(value=True)),
    PrintStatement(
        value=LogicalOp(
            operation="==", left=Integer(value="1"), right=Integer(value="2")
        )
    ),
    PrintStatement(
        value=LogicalOp(
            operation="<", left=Integer(value="0"), right=Integer(value="1")
        )
    ),
    PrintStatement(
        value=LogicalOp(
            operation=">", left=Integer(value="1"), right=Integer(value="0")
        )
    ),
    PrintStatement(
        value=LogicalOp(
            operation="&&", left=Boolean(value=True), right=Boolean(value=True)
        )
    ),
    PrintStatement(
        value=LogicalOp(
            operation="||", left=Boolean(value=False), right=Boolean(value=True)
        )
    ),
    PrintStatement(value=UnaryOp(operation="!", operand=Boolean(value=False))),
    IfElse(
        test=LogicalOp(operation="<", left=Name(value="a"), right=Name(value="b")),
        body=[Assignment(left=Name(value="minval"), right=Name(value="a"))],
    ),
]


for s in statements:
    print(format(s))
    print()
