"""
Usage:

poetry run python -m wabbit.parsit program.wb
"""

import typer

from ._parser import parse_file


def main(wabbit_file: str) -> None:
    ast = parse_file(wabbit_file)
    print(ast)


if __name__ == "__main__":
    typer.run(main)
