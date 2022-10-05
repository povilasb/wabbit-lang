import sys

from ._ast import *
from ._format import format


_TESTS = [
    (PrintStatement(value=Integer(value="42")), "print 42;"),
    (
        PrintStatement(value=BinOp.add(Integer(value="2"), Integer(value="3"))),
        "print 2 + 3;",
    ),
    (
        PrintStatement(
            value=BinOp.add(
                UnaryOp(operation="-", operand=Integer(value="2")),
                Integer(value="3"),
            )
        ),
        "print -2 + 3;",
    ),
    (
        PrintStatement(
            value=BinOp.add(
                Integer(value="2"),
                BinOp.mul(Integer(value="3"), Integer(value="-4")),
            )
        ),
        "print 2 + 3 * -4;",
    ),
    (
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
        "print (2 + 3) * 4;",
    ),
    (
        PrintStatement(
            value=BinOp.sub(
                Float(value="2.0"),
                BinOp.div(Float(value="3.0"), Float(value="4.0")),
            )
        ),
        "print 2.0 - 3.0 / 4.0;",
    ),
    (PrintStatement(value=Name(value="perimeter")), "print perimeter;"),
    (
        PrintStatement(value=UnaryOp(operation="-", operand=Name(value="x"))),
        "print -x;",
    ),
    (PrintStatement(value=Boolean(value=True)), "print true;"),
    (
        PrintStatement(
            value=LogicalOp(
                operation="==", left=Integer(value="1"), right=Integer(value="2")
            )
        ),
        "print 1 == 2;",
    ),
    (
        PrintStatement(
            value=LogicalOp(
                operation="<", left=Integer(value="0"), right=Integer(value="1")
            )
        ),
        "print 0 < 1;",
    ),
    (
        PrintStatement(
            value=LogicalOp(
                operation=">", left=Integer(value="1"), right=Integer(value="0")
            )
        ),
        "print 1 > 0;",
    ),
    (
        PrintStatement(
            value=LogicalOp(
                operation="&&", left=Boolean(value=True), right=Boolean(value=True)
            )
        ),
        "print true && true;",
    ),
    (
        PrintStatement(
            value=LogicalOp(
                operation="||", left=Boolean(value=False), right=Boolean(value=True)
            )
        ),
        "print false || true;",
    ),
    (
        PrintStatement(value=UnaryOp(operation="!", operand=Boolean(value=False))),
        "print !false;",
    ),
    (
        VarDecl(name=Name(value="perimeter"), type_=Type(name="float")),
        "var perimeter float;",
    ),
    (
        VarDecl(
            name=Name(value="v1"),
            type_=Type(name="int"),
            value=Integer(value="4"),
        ),
        "var v1 int = 4;",
    ),
    (
        ConstDecl(name=Name(value="pi"), value=Float(value="3.14159")),
        "const pi = 3.14159;",
    ),
    (
        ConstDecl(
            name=Name(value="tau"),
            value=BinOp.mul(Float(value="2.0"), Name(value="pi")),
        ),
        "const tau = 2.0 * pi;",
    ),
    (
        VarDecl(name=Name(value="radius"), value=Float(value="4.0")),
        "var radius = 4.0;",
    ),
    (
        Assignment(
            left=Name(value="perimeter"),
            right=BinOp.mul(Name(value="tau"), Name(value="radius")),
        ),
        "perimeter = tau * radius",
    ),
    (
        Assignment(
            left=Name(value="a"),
            right=Assignment(left=Name(value="b"), right=Integer(value="123")),
        ),
        "a = b = 123",
    ),
    (
        ExprAsStatement(
            expr=Assignment(left=Name(value="a"), right=Integer(value="123"))
        ),
        "a = 123;",
    ),
    (
        IfElse(
            test=LogicalOp(operation="<", left=Name(value="a"), right=Name(value="b")),
            body=Statements(
                nodes=[
                    ExprAsStatement(
                        expr=Assignment(
                            left=Name(value="minval"), right=Name(value="a")
                        )
                    )
                ]
            ),
            else_body=Statements(
                nodes=[
                    ExprAsStatement(
                        expr=Assignment(
                            left=Name(value="minval"), right=Name(value="b")
                        )
                    )
                ]
            ),
        ),
        """if a < b {
    minval = a;
} else {
    minval = b;
}""",
    ),
    (
        While(
            test=LogicalOp(
                operation="<", left=Name(value="x"), right=Integer(value="11")
            ),
            body=Statements(
                nodes=[
                    ExprAsStatement(
                        expr=Assignment(
                            left=Name(value="fact"),
                            right=BinOp.mul(Name(value="fact"), Name(value="x")),
                        )
                    ),
                    PrintStatement(value=Name(value="fact")),
                ]
            ),
        ),
        """while x < 11 {
    fact = fact * x;
    print fact;
}""",
    ),
    (
        While(
            test=Boolean(value=True),
            body=Statements(
                nodes=[
                    IfElse(
                        test=LogicalOp(
                            operation="==",
                            left=Name(value="n"),
                            right=Integer(value="0"),
                        ),
                        body=Statements(nodes=[Break()]),
                        else_body=Statements(
                            nodes=[
                                PrintStatement(value=Name(value="n")),
                                ExprAsStatement(
                                    expr=Assignment(
                                        left=Name(value="n"),
                                        right=BinOp.sub(
                                            Name(value="n"), Integer(value="1")
                                        ),
                                    )
                                ),
                                Continue(),
                            ]
                        ),
                    ),
                    ExprAsStatement(
                        expr=Assignment(
                            left=Name(value="n"),
                            right=BinOp.add(Name(value="n"), Integer(value="1")),
                        )
                    ),
                ]
            ),
        ),
        """while true {
    if n == 0 {
        break;
    } else {
        print n;
        n = n - 1;
        continue;
    }
    n = n + 1;
}""",
    ),
    (
        Statements(
            nodes=[
                FuncDef(
                    name=Name(value="add"),
                    args=[
                        FuncArg(name=Name(value="x"), type_=Type(name="int")),
                        FuncArg(name=Name(value="y"), type_=Type(name="int")),
                    ],
                    return_type=Type(name="int"),
                    body=Statements(
                        nodes=[
                            Return(value=BinOp.add(Name(value="x"), Name(value="y")))
                        ]
                    ),
                ),
                VarDecl(
                    name=Name(value="result"),
                    value=FuncCall(
                        name=Name(value="add"),
                        args=[Integer(value="2"), Integer(value="3")],
                    ),
                ),
            ]
        ),
        """func add(x int, y int) int {
    return x + y;
}
var result = add(2, 3);""",
    ),
]


def main() -> int:
    success = True
    for ast, expected_code in _TESTS:
        success &= _test_format(ast, expected_code, verbose=False)

    from ._interpret import interpret, _Interpreter

    n = Statements(
        nodes=[
            VarDecl(name=Name(value="n"), type_=Type(name="int")),
            Assignment(
                left=Name(value="n"),
                right=Integer(value="5"),
            ),
        ]
    )
    print(format(n))
    interpreter = _Interpreter()
    interpreter.visit(n)
    print(interpreter._exec_ctx)

    return 0 if success else 1


def _test_format(ast: Node, expected_code: str, verbose: bool = False) -> bool:
    success = True
    generated_code = format(ast)
    if generated_code != expected_code:
        # TODO(povilas): colors
        print("\n!!!!!! Test failed: !!!!!!")
        print("\n        Expected code")
        print("|--------------------------------|")
        print(expected_code)
        print("|--------------------------------|")
        print("\n        Generated code")
        print("|--------------------------------|")
        print(generated_code)
        print("|--------------------------------|")
        success = False

    elif verbose:
        print()
        print(generated_code)

    return success


if __name__ == "__main__":
    sys.exit(main())
