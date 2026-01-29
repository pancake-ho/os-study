#include <stdio.h>
#include <stdlib.h>
#include <ucontext.h>

// context 담을 변수 선언 (세이브 파일 슬롯 3개)
ucontext_t main_context, uctx_func1, uctx_func2;

// 각 함수 (프로세스)가 사용할 독자적인 스택 메모리 공간 (8KB)
// os 에서 프로세스마다 스택을 따로 할당하는 것과 동일
char stack1[8192];
char stack2[8192];

// 첫 번째 프로세스 역할
void func1() {
    printf("[Func1] 시작: 열심히 일하는 중...\n");
    printf("[Func1] 잠시 멈추고 Func2 에게 CPU 양보 (Switching!)\n");
    // 현재 상태를 uctx_func1 에 저장하고, uctx_func2 를 불러옴
    swapcontext(&uctx_func1, &uctx_func2);

    printf("[Func1] 다시 복귀! 하던 일 계속함.\n");
}

// 두 번째 프로세스 역할
void func2(){
    printf("[Func2] 안녕? 나는 Func1 이 양보해서 실행됨.\n");
    printf("[Func2] 할 일 다 했으니까 다시 Func1 에게 제어권 돌려줌.");
    // 현재 상태를 uctx_func2 에 저장하고, uctx_func1 로 복귀
    swapcontext(&uctx_func2, &uctx_func1);

    printf("[Func2] 이 줄은 실행되지 않습니다. (다시 호출되지 않으므로)\n");
}

int main(){
    // 현재 실행 중인 Main 의 문맥 가져오기 (초기화)
    getcontext(&uctx_func1);
    getcontext(&uctx_func2);

    // Func1 의 context (세이브파일) 설정
    uctx_func1.uc_stack.ss_sp = stack1; // 스택 위치
    uctx_func1.uc_stack.ss_size = sizeof(stack1); // 스택 크기
    uctx_func1.uc_link = &main_context; // 함수 끝나면 돌아갈 곳
    makecontext(&uctx_func1, func1, 0); // 세이브 파일 생성: "func1 부터 시작해!"

    // Func2의 context (세이브 파일) 설정
    uctx_func2.uc_stack.ss_sp = stack2;
    uctx_func2.uc_stack.ss_size = sizeof(stack2);
    uctx_func2.uc_link = &uctx_func1;         // 함수 끝나면 돌아갈 곳 
    makecontext(&uctx_func2, func2, 0);       // 세이브 파일 생성: "func2부터 시작해!"

    printf("[Main] 스케줄링 시작합니다. \n");

    // Main 에서 Func1 으로 제어권 넘김
    // main_context 에 현재 위치 저장 후, uctx_func1 실행
    swapcontext(&main_context, &uctx_func1);

    printf("[Main] 모든 작업 종료. OS 종료.\n");
    return 0;
}