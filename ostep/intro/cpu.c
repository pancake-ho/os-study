#include <stdio.h>
#include <stdlib.h>
#include "common.h"

int main(int argc, char *argv[])
// argc: 명령줄 인자 개수, argv: 인자 문자열 배열 (포인터)
{
    if (argc != 2) { 
        fprintf(stderr, "usage: cpu <string>\n"); // 인자가 틀리면 표준 에러 출력
        exit(1);
    }
    char *str = argv[1]; // 첫번째 인자 문자열을 str에 저장

    while (1) { // 무한 루프
        printf("%s\n", str);
        Spin(1);
    }
    return 0;
}