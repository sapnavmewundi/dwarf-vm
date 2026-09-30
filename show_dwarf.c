#include <stdio.h>

int main(int argc, char **argv) {
    int secret = 42;
    int array[5] = {1, 2, 3, 4, 5};
    int sum = secret;
    for (int i = 0; i < argc; i++) {
        sum += array[i % 5];
    }
    printf("Result: %d\n", sum);
    return 0;
}
