/**
 * Wabbit runtime functions.
 */

#include <stdio.h>

void __wabbit_print_int(int x)
{
    printf("%i\n", x);
}

void __wabbit_print_float(double x)
{
    printf("%f\n", x);
}

void __wabbit_print_bool(int v)
{
    if (v > 0)
    {
        printf("true\n");
    }
    else
    {
        printf("false\n");
    }
}

void __wabbit_print_char(int c)
{
    printf("%c", c);
}
