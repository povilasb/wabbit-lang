"""
Usage:

poetry run python -m wabbit.runit program.wb
"""

import typer

from ._parser import parse_file
from ._interpret import _Interpreter
from ._ast import *
from ._errors import WabbitError


def main(wabbit_file: str, debug: bool = False) -> None:
    ast = parse_file(wabbit_file)
    interpreter = _Interpreter()
    try:
        interpreter.visit(ast)
    except WabbitError as e:
        if debug:
            raise e
        else:
            print("Error:", e)

    if debug:
        print("\n")
        print("!!!! Interpreter state: !!!!")
        print(interpreter._exec_ctx[0])


if __name__ == "__main__":
    typer.run(main)
