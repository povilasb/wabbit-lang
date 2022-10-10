"""
Usage:

poetry run python -m wabbit.parsit program.wb
"""

import typer

from ._parser import parse_file


def main(wabbit_file: str) -> None:
    ast = parse_file(wabbit_file)
    for n in ast.nodes:
        print(n.__class__.__name__, n)

    from ._format import format

    print(format(ast))


if __name__ == "__main__":
    typer.run(main)
