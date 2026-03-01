#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    // PID: 프로세스를 지칭
    // 프로세스의 실행 순서는 다를 수 있다 (비결정성)
    printf("hello world (pid:%d)\n", (int) getpid());
    int rc = fork(); // 현재 프로세스를 복제해서 새 프로세스 생성

    if (rc < 0) {
        // fork failed; exit
        fprintf(stderr, "fork failed\n");
        exit(1);
    }
    else if (rc == 0) {
        // child (new process)
        // child의 PID는 새로 만들어진 child의 PID
        printf("hello, I am child (pid:%d)\n", (int) getpid());
    }
    else {
        // parent goes down this path (original process)
        printf("hello, I am parent of %d (pid:%d)\n", rc, (int) getpid());
    }
    return 0;
}