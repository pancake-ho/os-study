#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
    // parent가 wait() 안하면 child 종료 후 좀비 프로세스가 잠깐 생길 수 있음 (wait은 자식 종료를 회수하는 기능을 수행함)
    printf("hello world (pid:%d)\n", (int) getpid());
    int rc = fork();

    if (rc < 0) {
        // fork failed; exit
        fprintf(stderr, "fork failed\n");
        exit(1);
    }
    else if (rc == 0) {
        // child (new process)
        printf("hello, I am child (pid:%d)\n", (int) getpid());
        sleep(1); // 출력 순서 관찰을 용이하게 하기 위함
    }
    else {
        // parents goes down this path (original process)
        // 부모가 자식 프로세스가 종료할 때까지 대기
        int wc = wait(NULL); // 반환값 wc는 종료된 자식의 PID (이걸 호출한 순간 parent는 멈춰서 child가 끝날 때까지 다음 줄로 못 내려감)
        printf("hello, I am parent of %d (wc:%d) (pid:%d)\n", rc, wc, (int) getpid());
    }
    return 0;
}