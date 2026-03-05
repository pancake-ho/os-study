"""
- 프로세스가 CPU에서 실행될 때 프로세스 상태가 어떻게 변화하는 지를 보여주는 코드

프로세스 상태는 다음의 4단계
    1. RUNNING: 지금 당장 CPU 쓰는 중
    2. READY: CPU를 쓸 준비는 됐는데, 다른 프로세스가 CPU를 잡고 있어서 대기 중
    3. BLOCKED: I/O를 요청해놓고 (ex.디스크 읽기) I/O 완료를 기다리는 중
    4. DONE: 실행이 끝남
"""


from __future__ import annotations
import sys
from optparse import OptionParser
import random

def random_seed(seed):
    random.seed(seed)

# process switch behavior
SCHED_SWITCH_ON_IO = 'SWITCH_ON_IO'
SCHED_SWITCH_ON_END = 'SWITCH_ON_END'

# io finish behavior
IO_RUN_LATER = 'IO_RUN_LATER'
IO_RUN_IMMEDIATE = 'IO_RUN_IMMEDIATE'

# process states
STATE_RUNNING = 'RUNNING' # 지금 cpu 잡고 실행 중
STATE_READY = 'READY' # 실행 가능 (대기열)
STATE_DONE = 'DONE' # 끝남
STATE_WAIT = 'BLOCKED' # I/O 때문에 멈춤

# members of process structure
PROC_CODE = 'code_'
PROC_PC = 'pc_'
PROC_ID = 'pid_'
PROC_STATE = 'proc_state_'

# things a process can do
# 프로세스는 내부에 실행할 명령 리스트를 가지고 있고, 종류는 세 종류
DO_COMPUTE = 'cpu' # CPU를 1 tick 사용
DO_IO = 'io' # I/O 요청 시작 -> 이 순간 프로세스는 BLOCKED로 바뀜
DO_IO_DONE = 'io_done' # I/O가 끝난 뒤 완료 처리용 1 tick


class Scheduler:
    def __init__(self, process_switch_behavior, io_done_behavior, io_length):
        # keep set of instructions for each of the process
        self.proc_info = {} # 프로세스 정보를 담는 "프로세스 테이블" 딕셔너리
        self.process_switch_behavior = process_switch_behavior # 언제 프로세스 전환할 지 정책 저장
        self.io_done_behavior = io_done_behavior # I/O가 끝났을 때 그 프로세스를 즉시 CPU에 올릴 지 / 나중에 돌릴 지 정책 저장
        self.io_length = io_length # I/O가 몇 tick 걸리는 지 저장
        return
    
    def new_process(self):
        """
        새 프로세스를 하나 생성해서 proc_info에 등록하고, 그 PID를 반환하는 함수
        """
        proc_id = len(self.proc_info) # 현재 등록된 프로세스 개수 = 다음에 쓸 PID (PID를 0, 1, 2... 순서대로 자동 부여)
        self.proc_info[proc_id] = {} # 새 PID 칸에 프로세스용 딕셔너리 만들고
        self.proc_info[proc_id][PROC_PC] = 0 # 프로그램 카운터(PC) 초기값 0으로
        self.proc_info[proc_id][PROC_ID] = proc_id # PID 저장
        self.proc_info[proc_id][PROC_CODE] = [] # 이 프로세스가 실행할 "명령 리스트"를 빈 리스트로 만들어 둠
        self.proc_info[proc_id][PROC_STATE] = STATE_READY # 생성 직후 상태는 실행 가능 대기 상태
        return proc_id
    
    # program looks like this:
    # c7,i,c1,i
    # which means
    # compute for 7, then i/o, then compute for 1, then i/o
    def load_program(self, program): # program은 "c7,i,c1,i" 같은 문자열
        """
        "사람이 문자열로 짠 미니 프로그램"을 파싱해서, 해당 프로세스의 _code 리스트로 변환하는 함수
        """
        proc_id = self.new_process() # 새 프로세스를 하나 만들고, 그 PID를 확보
        for line in program.split(','): # "c7", "i", "c1", "i" 순서로 loop
            opcode = line[0] # 각 토큰의 첫 글자를 opcode로 간주
            if opcode == 'c': # compute (CPU 계산 구간이면)
                num = int(line[1:]) # "c7"의 7을 뽑아서 몇 tick 연속 CPU를 쓰는 지로 해석
                for i in range(num): # num번 만큼 cpu 명령을 리스트에 삽입
                    self.proc_info[proc_id][PROC_CODE].append(DO_COMPUTE)
            elif opcode == 'i': # I/O 요청이면
                self.proc_info[proc_id][PROC_CODE].append(DO_IO) # io 명령 1개를 추가 (이 tick에 IO를 시작한다)
                # add one compute to HANDLE the I/O completion
                # I/O가 완료되면 현실에서도 인터럽트 처리/후처리 등 CPU가 해야 할 일이 조금 있는데, 이 시뮬레이터에서는 그걸 "CPU 1 tick짜리 명령"으로 모델링한 것
                self.proc_info[proc_id][PROC_CODE].append(DO_IO_DONE) # 그리고 바로 뒤에 io_done을 1개 더 붙임
            else:
                print('bad opcode %s (shouble be c or i)' % opcode)
                exit(1)
        return
    
    def load(self, program_description): # program_description은 문자열이고 보통 "X:Y" 형태
        proc_id = self.new_process() # 새 프로세스를 하나 만들고 (pid 발급), 이 프로세스의 PROC_CODE 리스트에 명령을 채워 넣을 준비
        tmp = program_description.split(':') # X와 Y를 분리
        if len(tmp) != 2: # 분리에 실패하면
            print('Bad description (%s): Must be number <x:y>' % program_description)
            print(' where X is the number of instructions') # X는 (기본) 명령 개수
            print(' and Y is the percent change that an instruction is CPU not IO') # Y는 CPU 명령이 나올 확률 (퍼센트)
            exit(1)
        
        num_instructions, chance_cpu = int(tmp[0]), float(tmp[1])/100.0
        for i in range(num_instructions):
            if random.random() < chance_cpu: # 이번 명령은 CPU로
                self.proc_info[proc_id][PROC_CODE].append(DO_COMPUTE)
            else: # 이번 명령은 IO로
                self.proc_info[proc_id][PROC_CODE].append(DO_IO)
                # add one compute to HANDLE the I/O completion
                self.proc_info[proc_id][PROC_CODE].append(DO_IO_DONE)
        return
    
    def move_to_ready(self, expected, pid=-1):
        if pid == -1:
            pid = self.curr_proc
        assert(self.proc_info[pid][PROC_STATE] == expected)
        self.proc_info[pid][PROC_STATE] = STATE_READY
        return
    
    def move_to_wait(self, expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_WAIT
        return

    def move_to_running(self, expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_RUNNING
        return

    def move_to_done(self, expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_DONE
        return
    
    def next_proc(self, pid=-1):
        if pid != -1:
            self.curr_proc = pid
            self.move_to_running(STATE_READY)
            return
        for pid in range(self.curr_proc + 1, len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] == STATE_READY:
                self.curr_proc = pid
                self.move_to_running(STATE_READY)
                return
        for pid in range(0, self.curr_proc + 1):
            if self.proc_info[pid][PROC_STATE] == STATE_READY:
                self.curr_proc = pid
                self.move_to_running(STATE_READY)
                return
        return
    
    def get_num_processes(self):
        return len(self.proc_info)
    
    def get_num_instructions(self, pid):
        return len(self.proc_info[pid][PROC_CODE])
    
    def get_instruction(self, pid, index):
        return self.proc_info[pid][PROC_CODE][index]
    
    def get_num_active(self):
        num_active = 0
        for pid in range(len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] != STATE_DONE:
                num_active += 1
        return num_active
    
    def get_num_runnable(self):
        num_active = 0
        for pid in range(len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] == STATE_READY or self.proc_info[pid][PROC_STATE] == STATE_RUNNING:
                num_active += 1
        return num_active
    
    def get_ios_in_flight(self, current_time): # 입력으로 지금 시간(tick)을 받음
        """
        현재 시각 기준으로 아직 끝나지 않은 I/O가 총 몇 개 떠있는 지를 세는 함수
        """
        num_in_flight = 0 # 아직 안 끝난 I/O 개수를 0으로 초기화
        for pid in range(len(self.proc_info)): # 모든 프로세스를 돎
            for t in self.io_finish_times[pid]: # self.io_finish_times[pid]는 "그 pid가 과거에 시작한 IO들의 완료 예정 tick 목록"
                if t > current_time: # 완료 예정 시각 t가 현재 시각보다 뒤에 있으면, 그 IO는 아직 진행 중!
                    num_in_flight += 1
        return num_in_flight
    
    def check_for_switch(self):
        return
    
    def space(self, num_columns):
        for i in range(num_columns):
            print('%10s' % ' ', end='')
    
    def check_if_done(self):
        if len(self.proc_info[self.curr_proc][PROC_CODE]) == 0:
            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING:
                self.move_to_done(STATE_RUNNING)
                self.next_proc()
        return
    
    def run(self):
        """
        시간을 1 tick씩 실행시키면서, 다음과 같은 로직을 가짐.

        - CPU 실행/IO 요청 및 완료/스케줄링 전환 시뮬레이션
        - 시뮬레이션 과정을 표 형태로 출력
        - CPU/IO 바쁜 시간 통계를 반환
        """
        clock_tick = 0 # 시뮬레이션의 "현재 시간"을 0에서 시작

        if len(self.proc_info) == 0:
            return
        
        # track outstanding IOs, per process
        # 프로세스의 "진행 중 IO" 추적 구조 만들기
        self.io_finish_times = {} # 프로세스별로, 현재 진행 중인 io들이 언제 끝나는 지를 저장하는 dict
        for pid in range(len(self.proc_info)): # 모든 PID에 대해
            self.io_finish_times[pid] = [] # 해당 PID가 발행한 IO들의 "완료 tick"을 담는 리스트 생성

        # make first one active
        self.curr_proc = 0 # 처음에는 PID 0을 "현재 실행 대상"으로 설정
        self.move_to_running(STATE_READY) # PID 0이 READY 상태여야 한다는 것을 확인하고, RUNNING으로 상태 변경

        # OUTPUT: headers for each columns
        print('%s ' % 'Time', end='')
        for pid in range(len(self.proc_info)):
            print('%14s' % ('PID:%2d' % (pid)), end='')
        print('%14s' % 'CPU', end='')
        print('%14s' % 'IOs', end='')
        print('')

        # init statistics
        io_busy = 0 # 한 tick 동안 outstanding IO가 1개라도 있었던 tick 수
        cpu_busy = 0 # 한 tick에 실제로 CPU 명령 1개를 실행한 tick 수

        while self.get_num_active() > 0: # DONE이 아닌 프로세스가 하나라도 남아있으면 계속 돌기
            clock_tick += 1 # 시간이 1 tick 흐름

            # check for io finish
            io_done = False # 이번 tick에 IO 완료가 발생했는 지 표시하는 플래그
            for pid in range(len(self.proc_info)): # 모든 프로세스에 대해 "이번 tick에 IO가 끝나는 게 있는 지" 검사
                if clock_tick in self.io_finish_times[pid]: # 해당 PID의 완료 예정 리스트에 현재 tick이 있으면, IO가 지금 끝난 것
                    io_done = True
                    self.move_to_ready(STATE_WAIT, pid) # 상태 검사 -> IO 완료는 반드시 BLOCKED에만 발생해야 한다는 모델
                    if self.io_done_behavior == IO_RUN_IMMEDIATE: # IO 끝난 프로세스를 "즉시 실행" 정책이면 (바로 CPU에 올려줌, 즉 즉시 스케줄)
                        # IO_RUN_IMMEDIATE
                        if self.curr_proc != pid:
                            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING: # 현재 다른 프로세스가 RUNNING이면
                                self.move_to_ready(STATE_RUNNING) # 그 프로세스를 READY로 내림
                        self.next_proc(pid) # 그리고 그 pid를 RUNNING으로 만들고 curr_proc을 교체
                    else: # 나중에 실행 정책이면 (단, IO 끝났다고 바로 실행하지는 않음)
                        # IO_RUN_LATER
                        # 단, 조건부로 실행을 당겨두는 예외를 둠
                        if self.process_switch_behavior == SCHED_SWITCH_ON_END and self.get_num_runnable() > 1: # Runnable이 여럿이라면
                            # this means the process that issued the io should be run
                            # 원래는 IO에서 switch 안 하는 시스템인데, runnable이 여럿이면 IO 끝난 놈을 다음으로 선택해버림
                            self.next_proc(pid)
                        if self.get_num_runnable() == 1: # Runnable이 1개라면
                            # this is the only thing to run: so run it
                            # 그걸 실행해야 시뮬레이션이 멈추지 않으니까, 올림
                            self.next_proc(pid)
                    self.check_if_done() # IO 완료 처리로 인해 curr_proc이 바뀌었을 수 있으니, 현재 RUNNING인 애가 이미 코드 비었으면 DONE 처리하고 다음으로 ㄱㄱ

            # if current proc is RUNNING and has an instruction, execute it
            instruction_to_execute = '' # 이번 tick에 실행할 명령을 담을 곳
            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING and \
            len(self.proc_info[self.curr_proc][PROC_CODE]) > 0:
                instruction_to_execute = self.proc_info[self.curr_proc][PROC_CODE].pop(0)
                cpu_busy += 1

            # OUTPUT: print what everyone is up to
            if io_done:
                print(f"{clock_tick:>3}*", end="")
            else:
                print(f"{clock_tick:>3}", end="")
            for pid in range(len(self.proc_info)):
                if pid == self.curr_proc and instruction_to_execute != '':
                    print(f"{('RUN:' + instruction_to_execute):>14}", end="")
                else:
                    print(f"{self.proc_info[pid][PROC_STATE]:>14}", end="")

            # CPU output here: if no instruction executes, output a space, otherwise a 1
            if instruction_to_execute == '':
                print(f"{' ':>14}", end="")
            else:
                print(f"{'1':>14}", end="")
            
            # IO output here:
            num_outstanding = self.get_ios_in_flight(clock_tick)
            if num_outstanding > 0:
                print(f"{num_outstanding:>14}", end="")
                io_busy += 1
            else:
                print(f"{' ':>10}", end="")
            print('')

            # if this is an IO start instruction, switch to waiting state
            # and add an io completion in the future
            if instruction_to_execute == DO_IO: # 방금 실행한 요청이 IO 요청이면    
                self.move_to_wait(STATE_RUNNING) # BLOCKED 로 전환
                self.io_finish_times[self.curr_proc].append(clock_tick + self.io_length + 1)
                if self.process_switch_behavior == SCHED_SWITCH_ON_IO:
                    self.next_proc()

            # ENDCASE: check if currently running thing is out of instrucitons
            self.check_if_done()
        return (cpu_busy, io_busy, clock_tick)
    

#
# PARSE ARGUMENTS
#

parser = OptionParser()
parser.add_option('-s', '--seed', default=0, help='the random seed', action='store', type='int', dest='seed')
parser.add_option('-P', '--program', default='', help='more specific controls over programs', action='store', type='string', dest='program')
parser.add_option('-l', '--processlist', default='', help='a comma-separated list of processes to run, in the form X1:Y1,X2:Y2,... where X is the number of instructions that process should run, and Y the chances (from 0 to 100) that an instruction will use the CPU or issue an IO (i.e., if Y is 100, a process will ONLY use the CPU and issue no I/Os; if Y is 0, a process will only issue I/Os)', action='store', type='string', dest='process_list')
parser.add_option('-L', '--iolength', default=5, help='how long an IO takes', action='store', type='int', dest='io_length')
parser.add_option('-S', '--switch', default='SWITCH_ON_IO', help='when to switch between processes: SWITCH_ON_IO, SWITCH_ON_END', action='store', type='string', dest='process_switch_behavior')
parser.add_option('-I', '--iodone', default='IO_RUN_LATER', help='type of behavior when IO ends: IO_RUN_LATER, IO_RUN_IMMEDIATE', action='store', type='string', dest='io_done_behavior')
parser.add_option('-c', help='compute answers for me', action='store_true', default=False, dest='solve')
parser.add_option('-p', '--printstats', help='print statistics at end; only useful with -c flag (otherwise stats are not printed)', action='store_true', default=False, dest='print_stats')
(options, args) = parser.parse_args()

random_seed(options.seed)

assert(options.process_switch_behavior == SCHED_SWITCH_ON_IO or options.process_switch_behavior == SCHED_SWITCH_ON_END)
assert(options.io_done_behavior == IO_RUN_IMMEDIATE or options.io_done_behavior == IO_RUN_LATER)

s = Scheduler(options.process_switch_behavior, options.io_done_behavior, options.io_length)

if options.program != '':
    for p in options.program.split(':'):
        s.load_program(p)
else:
    # example process description (10:100,10:100)
    for p in options.process_list.split(','):
        s.load(p)

assert(options.io_length >= 0)

if options.solve == False:
    print('Produce a trace of what would happen when you run these processes:')
    for pid in range(s.get_num_processes()):
        print('Process %d' % pid)
        for inst in range(s.get_num_instructions(pid)):
            print('  %s' % s.get_instruction(pid, inst))
        print('')
    print('Important behaviors:')
    print('  System will switch when ', end='')
    if options.process_switch_behavior == SCHED_SWITCH_ON_IO:
        print('the current process is FINISHED or ISSUES AN IO')
    else:
        print('the current process is FINISHED')
    print('  After IOs, the process issuing the IO will ', end='')
    if options.io_done_behavior == IO_RUN_IMMEDIATE:
        print('run IMMEDIATELY')
    else:
        print('run LATER (when it is its turn)')
    print('')
    exit(0)

(cpu_busy, io_busy, clock_tick) = s.run()

if options.print_stats:
    print('')
    print('Stats: Total Time %d' % clock_tick)
    print('Stats: CPU Busy %d (%.2f%%)' % (cpu_busy, 100.0 * float(cpu_busy)/clock_tick))
    print('Stats: IO Busy  %d (%.2f%%)' % (io_busy, 100.0 * float(io_busy)/clock_tick))
    print('')