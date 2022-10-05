import typer

from ._lexer import tokenize


def main(wabbit_file: str) -> None:
    with open(wabbit_file) as f:
        source_code = f.read()

    tokens = tokenize(source_code)
    for t in tokens:
        print(t)


if __name__ == "__main__":
    typer.run(main)
