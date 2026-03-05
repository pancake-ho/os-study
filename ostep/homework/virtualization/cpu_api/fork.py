from __future__ import print_function
import random
import string
from optparse import OptionParser

def random_seed(seed):
    random.seed(seed)

def random_randint(low, hi):
    return int(low + random.random() * (hi - low + 1))

def random_choice(L):
    return L[random_randint(0, len(L)-1)]


class Forker:
    def __init__(self, fork_percentage, actions, action_list, show_tree, just_final,
                 leaf_only, local_reparent, print_style, solve):
        self.fork_percentage = fork_percentage # 무작위 액션을 생성할 때, fork가 나올 확률(비율)
        self.max_actions = actions # 무작위로 생성할 액션의 총 개수 상한
        self.action_list = action_list # 무작위가 아니라 사용자가 액션 리스트를 직접 주는 경우, 그 문자열을 저장
        self.show_tree = show_tree # 출력 모드 옵션
        self.just_final = just_final # 중간 과정은 생략하고 최종 상태만 출력할 지 여부
        self.leaf_only = leaf_only # exit를 시킬 때 leaf(자식 없는 프로세스)만 종료 허용할 지 옵션
        self.local_reparent = local_reparent # 부모가 exit할 때 고아 프로세스들을 로컬 부모로 reparent할 지, 아니면 루트로 몰아넣는 방식을 쓸 지 결정하는 옵션
        self.print_style = print_style # 트리 출력 모양을 결정하는 옵션
        self.solve = solve # 문제 풀이 모드, 사용자가 맞추게 하는 대신 정답(액션/트리)을 함께 출력할 지 여부

        # root process is always this
        self.root_name = 'a' # 루트 프로세스 이름을 항상 'a'로 고정. 이 프로그램은 프로세스 이름을 문자로 표현해서 트리를 그리는데, 그 시작점이 항상 a라는 의미

        # process list: names of all active processes
        self.process_list = [self.root_name] # 현재 살아있는 프로세스들의 이름 목록

        # for each process, it's children
        self.children = {} # 각 프로세스가 가진 자식 리스트를 담는 딕셔너리
        self.children[self.root_name] = [] # 루트 a의 자식 리스트를 초기화 (처음에는 자식 없음)

        # and track parents
        self.parents = {} # 각 프로세스의 부모를 담는 딕셔너리

        # this is for pretty process names...
        self.name_length = 1 # 새 프로세스 이름 생성 관련 상태 / 현재 이름 길이(문자 수)를 1로 시작한다는 의미인데, 이 파일에서는 실제로 이를 직접적으로 쓰진 않고 그냥 이름 풀을 키우는 로직으로만 활용됨
        self.base_names = string.ascii_lowercase + string.ascii_uppercase # 기본 문자 집합 정의, 한 글자 이름으로는 총 52개를 사용할 수 있음
        self.curr_names = self.base_names # 현재 사용 가능한 이름 목록을 base_names 로 시작
        self.curr_index = 1 # curr_names 에서 다음으로 꺼낼 인덱스 / 1부터 시작하는 이유는, 인덱스 0은 'a'(루트)가 이미 쓰고 있으니까 다음 세 프로세스는 'b'부터 뽑게 하려는 의도

    def grow_names(self):
        """
        이름 후보가 바닥났을 때, 더 긴 이름들(2글자, 3글자, ...)을 만들어서 풀을 확장하는 함수
        """
        new_names = [] # 새로 만든 이름들을 담을 리스트
        for b1 in self.curr_names: # 현재 이름 후보의 각 원소를 앞으로 사용
            for b2 in self.base_names: # 뒤로 붙일 원소
                new_names.append(b1 + b2)
        self.curr_names = new_names # 현재 이름 후보 풀을 방금 생성한 더 긴 이름들로 교체
        self.curr_index = 0
    
    def get_name(self):
        """
        다음에 쓸 프로세스 이름을 하나 꺼내서 반환하는 함수
        """
        if self.curr_index == len(self.curr_names): # 현재 이름 풀을 끝까지 다 썼는 지 체크
            self.grow_names() # 다 썼다면 이름 풀을 확장

        name = self.curr_names[self.curr_index] # 현재 인덱스 위치의 이름을 하나 꺼냄
        self.curr_index += 1 # 다음 호출 때는 그 다음 이름을 주도록 인덱스를 1 증가
        return name
    
    def walk(self, p, level, pmask, is_last):
        print('                               ', end='')
        if self.print_style == 'basic':
            for i in range(level):
                print('   ', end='')
            print('%2s' % p)
            for child in self.children[p]:
                self.walk(child, level + 1, {}, False)
            return
        elif self.print_style == 'line1':
            chars = ('|', '-', '+', '|')
        elif self.print_style == 'line2':
            chars = ('|', '_', '|', '|')
        elif self.print_style == 'fancy':
            # these characters taken from 'treelib', a fun printing package for trees
            # https://github.com/caesar0301/treelib
            # chars = ('\u2502', '\u2500', '\u251c', '\u2514')
            chars = (u'\u2502', u'\u2500', u'\u251c', u'\u2514')
        else:
            print('bad style %s' % self.print_style)
            exit(1)
            
        # print stuff before node
        if level > 0:
            # main printing
            for i in range(level-1):
                if pmask[i]:
                    # '|  '
                    print('%s   ' % chars[0], end='')
                else:
                    print('    ', end='')
            if pmask[level-1]:
                # '|__'
                if is_last:
                    print('%s%s%s ' % (chars[3], chars[1], chars[1]), end='')
                else:
                    print('%s%s%s ' % (chars[2], chars[1], chars[1]), end='')
            else:
                # '___' 
                print(' %s%s%s ' % (chars[1], chars[1], chars[1]), end='')

        # print node
        print('%s' % p)

        # undo parent verticals
        if is_last:
            pmask[level-1] = False

        # recurse
        pmask[level] = True
        for child in self.children[p][:-1]:
            self.walk(child, level + 1, pmask, False)
        for child in self.children[p][-1:]:
            self.walk(child, level + 1, pmask, True)
        return
    
    def print_tree(self):
        return self.walk(self.root_name, 0, {}, False)
    
    def do_fork(self, p, c):
        """
        fork가 일어났다고 가정하고, 프로세스 트리 자료구조를 업데이트하는 함수
        """
        self.process_list.append(c) # 현재 살아있는 프로세스 목록에, 새 자식 프로세스 c가 생겼다고 등록
        self.children[c] = [] # 새로 태어난 프로세스 c는 처음에는 자식이 없으니까, 자식 리스트를 빈 리스트로 초기화
        self.children[p].append(c) # 부모 p의 자식 목록에 c를 추가, 즉 p가 c를 fork해서 c가 p의 자식이 된 것
        self.parents[c] = p # 자식 c의 부모를 p로 기록
        return f"{p} forks {c}"
    
    def collect_chilren(self, p):
        """
        프로세스 p의 서브트리 (자기 자신 + 모든 자식) 목록들을 전부 모아서 반환하는 함수
        """
        if self.children[p] == []: # p의 자식 리스트가 비었는지 (리프 노드인 지) 확인
            return [p] # 리프면 더 내려갈 게 없으니, 자기 자신만 담은 리스트를 반환
        else: # 자식이 있다면, p의 서브트리를 다 모아야 함!
            L = [p]
            for c in self.children[p]:
                L += self.collect_chilren(c)
            return L
        
    def do_exit(self, p):
        """
        프로세스 p가 exit했을 때, 트리 자료구조를 올바르게 갱신하는 함수
        """
        # remove the process from the process list
        if p == self.root_name: # 만약 종료하려는 프로세스가 루트(a)라면
            print('root process: cannot exit') # 루트는 이 시뮬레이터에서 "항상 존재"로 가정해서 종료를 허용하지 않음
            exit(1)
        exit_parent = self.parents[p] # p의 부모를 찾음 (즉, exit_parents는 "p가 죽었을 때 p의 부모")
        self.process_list.remove(p) # 살아있는 프로세스 목록에서 p를 제거

        # for each orphan, set its parent to exiting proc's parent or root
        # p의 자식들은 이제 부모를 잃고 고아가 되니까, 그 자식들을 어디에 붙일 지 결정해야함
        if self.local_reparent: # 고아들을 p의 부모에게 붙이면
            for orphan in self.children[p]: # p의 직계 자식들을 순회하면서
                self.parents[orphan] = exit_parent # 각 고아의 부모를 바꿈 (ppid 변경)
                self.children[exit_parent].append(orphan) # exit_parent의 자식 목록에도 고아를 추가
        else: # 다른 정책을 사용하면
            # should set ALL descendants to be child of ROOT
            # p 아래의 모든 자식들을 전부 루트의 직계 자식으로 만들어버림
            descendants = self.collect_chilren(p)
            descendants.remove(p)
            for d in descendants:
                self.children[d] = []
                self.parents[d] = self.root_name
                self.children[self.root_name].append(d)
        
        # remove the entry from its parent child list
        self.children[exit_parent].remove(p)
        self.children[p] = -1 # should never be used again (죽은 프로세스 p의 자식 엔트리를 -1로 무효화)
        self.parents[p] = -1 # should never be used again (역시 동일 무효화)

        # remove the entry for this proc from children
        return f"{p} EXITS"
    
    def bad_action(self, action):
        print(f"bad action ({action}), must be X+Y or X- where X and Y are processes")
        exit(1)
    
    def check_legal(self, action):
        if '+' in action:
            tmp = action.split('+')
            if len(tmp) != 2:
                self.bad_action(action)
            return [tmp[0], tmp[1]]
        elif '-' in action:
            tmp = action.split('-')
            if len(tmp) != 2:
                self.bad_action(action)
            return [tmp[0]]
        else:
            self.bad_action(action)
        return 
    
    def run(self):
        print('                           Process Tree:')
        self.print_tree() # 프로세스 트리를 출력 (초기 상태에는 보통 a만 찍힘)
        print('')

        if self.action_list != '': # 실행 옵션으로 -A 같은 걸 줘서 액션 리스트를 직접 저장했는 지 확인, 즉 사용자가 액션을 직접 줬다면
            # use specific action list
            action_list = self.action_list.split(',') # , 로 쪼개서 리스트로 만들고, 이 리스트를 그대로 "실행할 액션 시나리오"로 사용
        else: # 사용자가 안 줬다면 랜덤으로 fork/exit 이벤트를 생성해서 action_list를 만듦
            action_list = [] # 앞으로 만들 액션들을 저장한 빈 리스트
            actions = 0 # 지금까지 몇 개의 액션을 만들었는 지 카운터
            temp_process_list = [self.root_name] # "시나리오 생성용" 임시 프로세스 목록, 즉 진짜 트리를 바꾸는 게 아니라 랜덤 액션을 만들기 위한 가짜 상태를 굴리는 용도
            level_list = {}
            level_list[self.root_name] = 1

            # this got a little yucky, too much re-doing of the work
            while actions < self.max_actions: # 옵션으로 준 actions 개수만큼 액션을 만들 때까지 전부
                # fork 이벤트 생성할 지 판단
                if random.random() < self.fork_percentage: # 0~1 난수 뽑아서, fork_percentage보다 작으면 fork 생성
                    # FORK:: pick random parent, add child to it
                    # 아래에서는 랜덤 액션을 만들건데, 이를 만들 때 진짜 트리 상태를 건드리면 복잡하게 꼬여버리는 문제가 발생
                    # 따라서 본 단계에서는 "실제 트리는 아예 건드리지 않고, 살아있다고 가정하는 프로세스 이름 목록만 temp_process_list"로 굴림
                    # 즉, 랜덤으로 문제를 만들기 위해 먼저 액션 시나리오만 생성하고 그 시나리오를 진짜 트리에 적용해서 출력 모드를 제어하는 흐름
                    fork_choice = random_choice(temp_process_list) # 현재 살아있다고 가정하는 임시 프로세스들 중 하나를 랜덤으로 골라서 부모 프로세스로 삼음
                    new_child = self.get_name() # 새 프로세스 이름을 하나 만듦
                    action_list.append(f"{fork_choice}+{new_child}") # 문자열 "부모+자식" 형태로 액션을 기록
                    temp_process_list.append(new_child)  # 임시 상태에서도 새 프로세스가 생겼다고 가정해야 다음 랜덤 선택에 포함되니까 추가
                else: # fork가 아니면 exit 이벤트를 만듦
                    # EXIT:: pick random child, remove it
                    #        exception: no killing root process, sorry
                    exit_choice = random_choice(temp_process_list) # 살아있는 임시 프로세스 중 
                    if exit_choice == self.root_name: # 루트는 죽이면 트리가 붕괴하니까 루트 종료는 금지
                        continue
                    temp_process_list.remove(exit_choice) # 임시 상태에서 해당 프로세스가 죽었다고 제거
                    action_list.append(f'{exit_choice}-') # 문자열 "프로세스-" 형태로 액션을 기록
                actions += 1 # 액션 하나 만들었으니 카운터 증가

        # 만들어진 action_list를 진짜 트리 상태에 적용
        for a in action_list:
            tmp = self.check_legal(a) # 액션 문자열이 합법 형식인 지 검사하고 파싱해줌
            if len(tmp) == 2: # fork 액션인 경우
                fork_choice, new_child = tmp[0], tmp[1] # 부모, 자식 이름 추출
                if fork_choice not in self.process_list: # 부모가 현재 살아있는 프로세스가 아니면 말이 안 되니까 에러
                    self.bad_action(a)
                action = self.do_fork(fork_choice, new_child) # 진짜 fork 실행 및 문자열 돌려줌 (ex. a forks b)
            else: # exit 액션인 경우
                exit_choice = tmp[0] # 종료할 프로세스 이름
                if exit_choice not in self.process_list: # 죽일 프로세스가 살아있지 않으면 에러
                    self.bad_action(a)
                if self.leaf_only and len(self.children[exit_choice]) > 0: # 옵션 leaf_only가 켜져 있으면, 자식이 있는 프로세스는 exit 금지
                    action = '%s EXITS (failed: has children)' % exit_choice # 종료 실패했다는 메시지만 뽑고, 실제 트리는 바꾸지 않음
                else: # leaf-only가 아니거나 leaf면 실제로 exit 처리
                    action = self.do_exit(exit_choice)
            
            # if we got here, we actually did an action...
            if self.show_tree: # -t 옵션 같은 걸로 트리를 보여주는 모드면 여기로
                # SHOW TREES (guess actions)
                if self.solve: # solve=True면 정답 모드라 액션을 그대로 보여줌
                    print('Action:', action)
                else: # solve=False면 사용자가 맞추게 함
                    print('Action?')
                # print('Process Tree:')
                if not self.just_final: # final_only가 아니면 매 스텝마다 현재 트리를 출력
                    self.print_tree()
            else: # 트리를 숨기고, 액션을 보여주는 모드면 여기로
                # SHOW ACTIONS (guess tree)
                print('Action:', action)
                if not self.just_final:
                    if self.solve:
                        # print('Process Tree:')
                        self.print_tree()
                    else:
                        print('Process Tree?')
        
        if self.just_final: # 중간 출력은 생략하고 마지막만 보여줘야 하면 여기로
            if self.show_tree:
                print('\n                        Final Process Tree:')
                self.print_tree()
                print('')
            else:
                if self.solve:
                    print('\n                        Final Process Tree:')
                    self.print_tree()
                    print('')
                else:
                    print('\n                        Final Process Tree?\n')



#
# main
#

parser = OptionParser()
parser.add_option('-s', '--seed', default=-1, help='the random seed', action='store', type='int', dest='seed')
parser.add_option('-f', '--forks', default=0.7, help='percent of actions that are forks (not exits)', action='store', type='float', dest='fork_percentage')
parser.add_option('-A', '--action_list', default='', help='action list, instead of randomly generated ones (format: a+b,b+c,b- means a fork b, b fork c, b exit)', action='store', type='string', dest='action_list')
parser.add_option('-a', '--actions', default=5, help='number of forks/exits to do', action='store', type='int', dest='actions')
parser.add_option('-t', '--show_tree', help='show tree (not actions)', action='store_true', default=False, dest='show_tree')
parser.add_option('-P', '--print_style', help='tree print style (basic, line1, line2, fancy)', action='store', type='string', default='fancy', dest='print_style')
parser.add_option('-F', '--final_only', help='just show final state', action='store_true', default=False, dest='just_final')
parser.add_option('-L', '--leaf_only', help='only leaf processes exit', action='store_true', default=False, dest='leaf_only')
parser.add_option('-R', '--local_reparent', help='reparent to local parent', action='store_true', default=False, dest='local_reparent')
parser.add_option('-c', '--compute', help='compute answers for me', action='store_true', default=False, dest='solve')

(options, args) = parser.parse_args()

if options.seed != -1:
    random_seed(options.seed)

if options.fork_percentage <= 0.001:
    print('fork_percentage must be > 0.001')
    exit(1)

print('')
print('ARG seed', options.seed)
print('ARG fork_percentage', options.fork_percentage)
print('ARG actions', options.actions)
print('ARG action_list', options.action_list)
print('ARG show_tree', options.show_tree)
print('ARG just_final', options.just_final)
print('ARG leaf_only', options.leaf_only)
print('ARG local_reparent', options.local_reparent)
print('ARG print_style', options.print_style)
print('ARG solve', options.solve)
print('')

f = Forker(options.fork_percentage, options.actions, options.action_list, options.show_tree, options.just_final, options.leaf_only, options.local_reparent, options.print_style, options.solve)
f.run()