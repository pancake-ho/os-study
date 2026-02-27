#ifndef __common_h__
#define __common_h__

#include <sys/time.h>
#include <sys/stat.h>
#include <assert.h>

double GetTime() {
    // 현재 시간을 초 단위로 리턴하는 함수
    struct timeval t; // 시간을 담을 구조체 변수
    int rc = gettimeofday(&t, NULL); // 현재 시간을 t에 채우고, 반환값을 rc에 저장
    assert(rc == 0);
    return (double) t.tv_sec + (double) t.tv_usec / 1e6;
}

void Spin(int howlong) {
    // "howlong" 초 동안 기다리는 함수 (의도적으로 CPU 소모를 보여주기 위함)
    double t = GetTime();
    while ((GetTime() - t) < (double) howlong);
}

#endif 