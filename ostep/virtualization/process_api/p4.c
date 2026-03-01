#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <assert.h>
#include <sys/wait.h>
#include <sys/stat.h>

int main(int argc, char *argv[]) {
    // "./p4.output" 파일에는 "wc p4.c"의 출력이 들어감
    // 또한 보통 wc 파일은 기본적으로 "라인 수/단어 수/바이트 수/파일 이름"의 정보가 들어감
    int rc = fork();
    if (rc < 0) {
        // fork failed; exit
        fprintf(stderr, "fork failed\n");
        exit(1);
    }
    else if (rc == 0) {
        // child: redirect standard output to a file
        close(STDOUT_FILENO); // 표준출력(stdout)을 닫아버림, STDOUT_FILENO는 보통 1번 파일 디스크립터

        // 없으면 새로 만들고, 쓰기 전용이고, 이미 있으면 내용 싹 지우고 시작해라 | 또한 사용자에게 읽기/쓰기/실행 권한 부여
        // 방금 stdout(fd=1)을 닫았기 때문에, OS는 보통 "가장 낮은 빈 fd"를 재사용하고
        // 이 open()이 fd=1을 다시 차지하는 경우가 많음 -> 결과적으로 이제부터 "stdout으로 출력되는 것"이 파일 p4.output으로 들어감
        open("./p4.output", O_CREAT|O_WRONLY|O_TRUNC, S_IRWXU);

        // now exec "wc"...
        char *myargs[3];
        myargs[0] = strdup("wc");
        myargs[1] = strdup("p4.c");
        myargs[2] = NULL;
        execvp(myargs[0], myargs); // wc의 출력이 터미널이 아니라 "./p4.output"에 저장됨
    }
    else {
        int wc = wait(NULL);
        assert(wc >= 0);
    }
    return 0;
}