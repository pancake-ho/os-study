#include <stdio.h>
#include <stdlib.h>
#include "common.h"
#include "common_threads.h"

volatile int counter = 0; // 공유변수 선언 (모든 thread가 같은 counter를 봄) - volatile: 메모리에서 읽고 써라
int loops;

void *worker(void *arg) {
    // thread 시작 함수 (포인터 하나 받고, 포인터 하나 리턴)
    int i;
    for (i = 0; i < loops; i++) {
        counter++;
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    // thread 2개가 같은 변수를 동시에 ++ 하면 경쟁하여 결과가 틀릴 수도 있다
    if (argc != 2) {
        fprintf(stderr, "usage: threads <loops>\n"); // 사용법을 stderr로 출력
        exit(1);
    }
    loops = atoi(argv[1]); // 문자열 인자를 정수로 반환해서 loop에 저장
    pthread_t p1, p2; // thread "핸들/ID" 저장용 변수 2개
    printf("Initial value: %d\n", counter);
    Pthread_create(&p1, NULL, worker, NULL); // thread 1 생성 (ID, 기본 속성, 실행할 함수, Worker로 넘길 인자)
    Pthread_create(&p2, NULL, worker, NULL); // thread 2 생성
    Pthread_join(p1, NULL); // thread 1이 끝날 때까지 대기
    Pthread_join(p2, NULL); // thread 2가 끝날 때까지 대기
    printf("Final value: %d\n", counter); // 최종 counter 출력 - 정상 동작이면, Final = 2 * loops 가 출력되어야 함
    return 0;
}