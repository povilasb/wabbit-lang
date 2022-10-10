mkdir -p build
poetry run python -m wabbit.compile $1 > build/tmp.ll
clang build/tmp.ll wabbit/runtime.c -o build/main.out
