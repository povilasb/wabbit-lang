"""
Usage:

poetry run python -m wabbit.runit program.wb
"""

import typer

from ._parser import parse_file
from ._compiler import Compiler


def main(wabbit_file: str) -> None:
    ast = parse_file(wabbit_file)
    compiler = Compiler()
    compiler.visit(ast)
    print(compiler.to_llvm())


if __name__ == "__main__":
    typer.run(main)
