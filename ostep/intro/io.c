#include <stdio.h>
#include <unistd.h>
#include <assert.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>

int main(int argc, char *argv[]) {
    int fd = open("/tmp/file", O_WRONLY | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);
    // 파일을 열거나, 없으면 만들고, 내용을 0으로 잘라 (truncate) 쓰기 전용으로 열기
    assert(fd >= 0);
    char buffer[20];
    sprintf(buffer, "hello world\n"); // 문자열을 buffer에 써넣는 과정
    
    int rc = write(fd, buffer, strlen(buffer)); // buffer에서 strlen(buffer) 바이트만큼을 fc가 가리키는 파일에 써라
    assert(rc == (strlen(buffer))); // 전부 썼는 지 확인
    fsync(fd); // 커널의 버퍼 캐시에만 있던 변경 내용을 저장장치까지 강제 flush 하도록 요청
    close(fd);
    return 0;
}