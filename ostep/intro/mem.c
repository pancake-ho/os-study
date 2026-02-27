#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include "common.h"

int main(int argc, char *argv[]) {
    // 같은 프로그램을 두 번 실행하면 둘 다 같은 주소를 출력할 수 있지만 값은 따로 증가함
    if (argc != 2) {
        fprintf(stderr, "usage: mem <value>\n");
        exit(1);
    }
    int *p; // int 가리키는 포인터 변수 p 선언 (stack에 위치)
    p = malloc(sizeof(int)); // heap에서 int 1개 크기만큼 메모리 할당하고 그 주소(포인터)를 p에 저장
    assert(p != NULL);
    printf("(%d) addr pointed to by p: %p\n", (int) getpid(), p); // 현재 프로세스의 PID와 p가 가리키는 주소값 출력
    *p = atoi(argv[1]); // argv 문자열을 정수로 바꿔 p가 가리키는 메모리 위치에 저장
    
    while (1) {
        Spin(1);
        *p = *p + 1; // 포인터 자체 p가 변하는 게 아니라, 그 주소에 저장되어 있는 값 변화
        printf("(%d) value of p: %d\n", getpid(), *p);
    }
    return 0;
}