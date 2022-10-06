"""
Usage:

poetry run python -m wabbit.runit program.wb
"""

import typer

from ._parser import parse_file
from ._interpret import interpret, _Interpreter

from ._ast import *


def main(wabbit_file: str) -> None:
    # ast = parse_file(wabbit_file)

    ast = Statements(
        nodes=[
            VarDecl(name=Name(value="a"), type_=Type(name="int")),
            Assignment(
                left=Name(value="a"),
                right=Integer(value="5"),
            ),
            ConstDecl(
                name=Name(value="b"), type_=Type(name="int"), value=Integer(value="1")
            ),
            # PrintStatement(value=BinOp.add(Name(value="a"), Name(value="b"))),
            # IfElse(
            #     test=LogicalOp(
            #         operation=">", left=Name(value="a"), right=Integer(value="0")
            #     ),
            #     body=Statements(nodes=[PrintStatement(value=Boolean(value=True))]),
            #     else_body=Statements(
            #         nodes=[PrintStatement(value=Boolean(value=False))]
            #     ),
            # ),
            While(
                test=LogicalOp(
                    operation=">", left=Name(value="a"), right=Integer(value="0")
                ),
                body=Statements(
                    nodes=[
                        PrintStatement(value=Name(value="a")),
                        Assignment(
                            left=Name(value="a"),
                            right=BinOp.sub(Name(value="a"), Integer(value="1")),
                        ),
                    ]
                ),
            ),
        ]
    )

    interpreter = _Interpreter()
    interpreter.visit(ast)
    print(interpreter._exec_ctx)


if __name__ == "__main__":
    typer.run(main)
