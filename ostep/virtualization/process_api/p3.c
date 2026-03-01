#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
    // fork() 만 하면 "복제된 동일한 프로그램"이 두 개가 됨
    // 그런데, 실제 os에서는 자식에게 다른 프로그램을 실행시키고 싶을 때가 대부분
    // -> 부모는 관리/감독, 자식은 exec로 원하는 프로그램 실행!
    // execvp() 의 핵심은 "성공하면 돌아오지 않는다", 또한 argv는 NULL로 끝나야 함
    // wait() 의 핵심은 "동기화 및 자식 정리"
    printf("hello world (pid:%d)\n", (int) getpid());
    int rc = fork();

    if (rc < 0) {
        // fork failed; wait
        fprintf(stderr, "fork failed\n");
        exit(1);
    }
    else if (rc == 0) {
        // child (new process)
        printf("hello, I am child (pid:%d)\n", (int) getpid());
        char *myargs[3]; // 문자열 포인터 3개짜리 배열 (이 배열이 그대로 새 프로그램 wc의 argv가 됨)
        myargs[0] = strdup("wc"); // program: "wc" (word count) - 관례적으로 "실행 파일 이름"이고, "wc" 문자열을 힙 메모리에 복사해서 포인터를 돌려주는 역할
        myargs[1] = strdup("p3.c"); // argument: file to count - wc에 줄 인자로 줄 파일명
        myargs[2] = NULL; // marks end of array - NULL로 끝난다고 가정 (중요)
        execvp(myargs[0], myargs); // runs word count - 자식의 프로그램 교체 / 성공하면 자식 프로세스는 더 이상 p3.c를 실행하지 않고 wc를 로드해서 실행 (자식의 메모리가 wc로 덮어씌워짐)
        printf("this shouldn't print out"); // 이건 원칙적으로 출력되면 안됨!
    }
    else {
        // parents goes down this path (original process)
        int wc = wait(NULL); // 자식이 끝날 때까지 부모가 기다림, 자식의 종료 정보를 수거해서 좀비 프로세스를 방지하는 과정
        printf("hello, I am parent of %d (wc:%d) (pid:%d)\n", rc, wc, (int) getpid());
    }
    return 0;
}