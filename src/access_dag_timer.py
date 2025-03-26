from typing import Optional

import networkx, random, math



class Node:
    def __init__(
        self,
        c: int,
        k_parallel: int,  
        id: int,
        period: int,
        seed: int,
        require_core_num: int = 1,
        activate_num: int = 0 ,
        trigger_edge: int | None = None,
        timer_flag: bool = False,
        laxity: int = 0,
        util: float = 0
    ):
        self._c = c
        self._c_base = c
        self._ft = None
        self._st = None
        self._core_use = None
        self._require_core_num = require_core_num
        self._core = []
        self._laxity = laxity
                
        # # 修論版
        # if k_parallel <= 4:
        #     self._k = (k_parallel+5) / 10
        # else:
        #     self._k = k_parallel / 10

        # クラスタ選択の場合
        if k_parallel >= 1:
            self._k = k_parallel / 10
        else:
            self._k = k_parallel
        self._finish = False
        self._id = id
        self._p = -1
        self._release_flag = False
        self._special_flag = False #ECRTSの評価で特別に多くのコアを与えられるノード
        self._seed = seed
        self._remain_ex_time = self._c

        #修論用
        # 各ノードの利用率
        self._util = util
        self._wcrt = 0
        self._nth_finish = {}
        self._pre_ft = None



        #20241010現在、生成したDAGの周期が20~50のため、10倍している
        self._period = period

        self._activate_num = activate_num
        self._trigger_edge = trigger_edge

        # timer_driven_nodeかの判定フラグ
        self._timer_flag = timer_flag

        # # 何番目のジョブか
        # self._activate_num = 1

        #前に確保したコアの情報を保存
        self._allocated_cores = []

        # 待ち時間を調べるための、リリースタイムと最終的な実行時間（並列実行＋cluster_comm）を保存する変数
        self._release_time = None
        self._c_for_respo = 0
        self._finish_time = 0


        self._lp_list = []
        self._hp_list = []



    @property
    def lp_list(self):
        return self._lp_list

    @lp_list.setter
    def lp_list(self, lp_id: int):
        self._lp_list.append(lp_id) 

    @property
    def hp_list(self):
        return self._hp_list

    @hp_list.setter
    def hp_list(self, hp_id: int):
        self._hp_list.append(hp_id) 


    @property
    def pre_ft(self):
        return self._pre_ft

    @pre_ft.setter
    def pre_ft(self, pre_ft: int):
        self._pre_ft = pre_ft 
    
    @property
    def finish_time(self):
        return self._finish_time

    @finish_time.setter
    def finish_time(self, finish_time: int):
        self._finish_time = finish_time

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: int):
        self._start_time.append(start_time)  

    @property
    def wcrt(self):
        return self._wcrt

    @wcrt.setter
    def wcrt(self, wcrt: int):
        self._wcrt = wcrt  

    @property
    def c_for_respo(self):
        return self._c_for_respo

    @c_for_respo.setter
    def c_for_respo(self, time: int):
        self._c_for_respo = time   

    @property
    def release_time(self):
        return self._release_time

    @release_time.setter
    def release_time(self, time: int):
        self._release_time = time

    def set_new_wcet(self, new_wcet):
        self._c = new_wcet
    @property
    def allocated_cores(self) -> list:
        return self._allocated_cores
    
    @allocated_cores.setter
    def allocated_cores(self, core_id:int):
        self._allocated_cores.append(core_id)

    
    def allocated_cores_clear(self):
        self._allocated_cores.clear()
    
    @property
    def remain_ex_time(self)->int:
        return self._remain_ex_time
    
    @remain_ex_time.setter
    def remain_ex_time(self, n:int):
        self._remain_ex_time += n



    @property
    def release_flag(self) -> bool:
        return self._release_flag

    @release_flag.setter
    def release_flag(self, release_flag: bool):
        self._release_flag = release_flag

    @property
    def c(self) -> int:
        return self._c

    @c.setter
    def c(self, n):
        self._c += n

    @property
    def c_base(self) -> int:
        return self._c_base

    @c_base.setter
    def c_base(self, n):
        self._c_base = n


    @property
    def new_c(self):
        return 

    @property
    def FT(self) -> Optional[int]:
        return self._ft

    @FT.setter
    def FT(self, n: int):
        self._ft = n

    @property
    def ST(self) -> Optional[int]:
        return self._st

    @ST.setter
    def ST(self, n: int):
        self._st = n
    
    @property
    def core(self) -> list[int]:
        return self._core
    
    @core.setter
    def core(self, n: int):
        self._core.append(n)

    @property
    def require_core_num(self):
        return self._require_core_num
    
    @require_core_num.setter
    def require_core_num(self, n: int):
        self._require_core_num = n

    @property
    def core_use(self) -> Optional[int]:
        return self._core_use

    @core.setter
    def core_use(self, n: int):
        self._core_use = n

    @property
    def laxity(self) -> int:
        return self._laxity

    @laxity.setter
    def laxity(self, n: int):
        self._laxity = n

    @property
    def k(self) -> int:
        return self._k
    
    @k.setter
    def k(self, k):
        self._k = k

    @property
    def finish(self) -> bool:
        return self._finish
    
    @finish.setter
    def finish(self, bol: bool) -> bool:
        self._finish = bol

    @property
    def id(self) -> int:
        return self._id

    @property
    def p(self):
        return self._p
    
    @p.setter
    def p(self, n: int):
        self._p = n
    
    @property
    def special_flag(self):
        return self._special_flag
    
    @special_flag.setter
    def special_flag(self, flag: bool):
        self._special_flag = flag

    # @property
    # def ex_times(self):
    #     return self._ex_times
    
    @property
    def seed(self):
        return self._seed
    
    @property
    def timer_flag(self):
        return self._timer_flag
    
    @timer_flag.setter
    def timer_flag(self, timer_flag: bool):
        self._timer_flag = timer_flag

    @property
    def period(self):
        return self._period
    
    @period.setter
    def period(self, period: int):
        self._period = period
    
    @property
    def activate_num(self):
        return self._activate_num
    
    @activate_num.setter
    def activate_num(self, num: int):
        self._activate_num += num
    
    @property
    def trigger_edge(self):
        return self._trigger_edge
    
    @trigger_edge.setter
    def trigger_edge(self, edge: int):
        self._trigger_edge = edge
    
    def core_clear(self):
        self._core.clear()

    @property
    def util(self):
        return self._util
    
    @util.setter
    def util(self, util: float):
        self._util = util
    


class DAG:
    def __init__(
        self,
        weights: list[int],
        edges: list[(int, int)],
        deadline: int,
        k_parallel: list[int],
        index: list[int],
        periods: list[int],
        seeds: list[int]
    ):
        # DiGraph
        self.G = networkx.DiGraph()
        self.G.add_nodes_from(range(len(weights)))

    

        #DSD2024では、WCETをex_timesの最大値とするため、weightsを使用しない
        # wcets: list[int] = []
        # for ex_ts in ex_times:
        #     wcet = max(ex_ts)
        #     wcets.append(wcet)

        self._nodes = [Node(c, k, id, period, seed) for c, k, id, period, seed \
                         in zip(weights, k_parallel, index, periods, seeds)]
        self.G.add_edges_from(edges)
        self._core_ft = [0 for n in range(len(weights))]
        self._core_use = [0]*len(weights)
        self._max_wcet = 0
        self._jobs: list[Node] = []
        #タイマノード（途中）の数
        self._num_of_timer = 3
        

        # srcノードにタイマの設定をする
        for src in self.src:
            self.nodes[src].timer_flag = True

        
        #タイマノードの決定
        count = 0
        seed = 0
        while count < self._num_of_timer:
            # for n in range(self._num_of_timer):
            # seed = self._nodes[n].seed
            random.seed(seed)
            time_node_id = random.randint(0, len(self._nodes)-1) 
            # print("time_node_id="+str(time_node_id))
            # print("time_node_id = "+str(time_node_id))
            # 出口ノードでなければOK
            if len(self.successors(time_node_id)) != 0 and time_node_id not in self.src and \
                self._nodes[time_node_id].timer_flag is False:
                self._nodes[time_node_id].timer_flag = True
                self._nodes[time_node_id].k = 0
                count += 1 
                seed += 1
            else:
                seed += 1
       
        # member
        self._deadline = deadline
        self._culc_laxity()
        self._c_path = self._culc_c_path()
        self._c_path2 = self._culc_c_path2()

        #利用率の計算
        for node in self._nodes:
            node.util = node.c / node.period





    @property
    def num_of_timer(self) -> int:
        return self._num_of_timer
    
    
    # return index list [1, ..., n]
    @property
    def c_path(self) -> list[int]:
        return self._culc_c_path()
    
    @property
    def c_path2(self) -> list[int]:
        return self._culc_c_path2()
    

    @property
    def core_ft(self) -> int:
        return self._core_ft

    @core_ft.setter
    def core_ft(self, n: int):
        self._core_ft.append(n)

    @property
    def core_use(self) -> int:
        return self._core_use

    @core_use.setter
    def core_use(self, n: int):
        self._core_use.append(n)

    def predecessors(self, n: int) -> list[int]:
        return list(self.G.predecessors(n))

    def successors(self, n: int) -> list[int]:
        return list(self.G.successors(n))

    # return index list
    @property
    def src(self) -> list[int]:
        return [i for i, node in enumerate(self.G.nodes) if len(list(self.predecessors(i))) == 0]

    # return index list
    @property
    def snk(self) -> list[int]:
        return [i for i, node in enumerate(self.G.nodes) if len(list(self.successors(i))) == 0]

    @property
    def deadline(self) -> int:
        return self._deadline

    @property
    def jobs(self):
        return self._jobs
    

    @property
    def makespan(self) -> int:
        m=0
        for n in self.nodes:
            if n.FT is not None and n.FT > m:
                m = n.FT
        return m

    def _culc_laxity(self):
        def culc(n: int, l: int):
            if self.nodes[n].laxity == 0:
                self.nodes[n].laxity = l
            elif self.nodes[n].laxity > l:
                self.nodes[n].laxity = l
            # print("n="+str(n)+", l="+str(self.nodes[n].laxity))
            for s in list(self.G.predecessors(n)):
                culc(s, l-self.nodes[s].c)

        for n in self.snk:
            culc(n, self.deadline-self.nodes[n].c)

    @property
    def nodes(self):
        return self._nodes


    def _culc_c_path(self) -> list[int]:
        cp = []
        length = 0
        for s in self.src:
            for d in self.snk:
                for path in list(networkx.all_simple_paths(self.G, s, d)):
                    # print(path)
                    tmp_length = sum([self.nodes[n].c for n in path])
                    if tmp_length > length:
                        cp = path
                        length = tmp_length

        return cp
    
    #二番目のクリティカルパスを求める
    def _culc_c_path2(self) -> list[int]:
        cp = []
        cp_length = 0
        second_cp = []
        second_cp_length = 0
        for s in self.src:
            for d in self.snk:
                for path in list(networkx.all_simple_paths(self.G, s, d)):
                    # print(path)
                    tmp_length = sum([self.nodes[n].c for n in path])
                    if tmp_length > cp_length:
                        cp = path
                        cp_length = tmp_length
        
        for s in self.src:
            for d in self.snk:
                for path in list(networkx.all_simple_paths(self.G, s, d)):
                    # print(path)
                    tmp_length = sum([self.nodes[n].c for n in path])
                    if tmp_length > second_cp_length and tmp_length < cp_length:
                        second_cp = path
                        second_cp_length = tmp_length

        return second_cp
    
    
    def calc_node_level(self, node_id: int):
        level = 0
        for s in self.src:
            for path in list(networkx.all_simple_paths(self.G, s, node_id)):
                if level < len(path)-1:
                    level =  len(path)-1
        return level
    
    # ソース以外と途中の周期ノード以外の周期を0に初期化
    def _reset_period(self) -> None:
        for node in self._nodes:
            if node.id not in self.src and node.timer_flag is False:
                node.period = 0


    # 先行ノードの中で一番大きい周期をそのノードの周期とする
    def _allocate_period_from_src(self):
        count = 0
        self._reset_period()
        while count < len(self.nodes)-len(self.src)-self._num_of_timer:
            # print("in-loop: 0-id node period = "+str(self.nodes[self.src[0]].period))
            for node in self.nodes:
                tmp_max_period = 0
                trigger_edge_id = None
                if node.id not in self.src and node.timer_flag is False: 
                    for pre_node in self.predecessors(node.id):
                        if tmp_max_period <= self._nodes[pre_node].period:
                            tmp_max_period = self._nodes[pre_node].period
                            trigger_edge_id = pre_node
                    if tmp_max_period > 0:
                        node.period = tmp_max_period
                        node.trigger_edge = trigger_edge_id
                        count += 1

                else:
                    pass
            # print("in-l/oop-end: 0-id node period = "+str(self.nodes[self.src[0]].period))

    

    # ソースノードのHPを求める
    def _calc_HP(self) -> int:
        src_periods = []
        for node in self.nodes:
            if node.id in self.src or node.timer_flag is True:
                src_periods.append(node.period)
        # src_periods = [node.period for node in self._nodes if node.id in self.src or node.timer_flag is True]
        hp = math.lcm(*src_periods)
        return hp
    
    #HP内のジョブ数を決め生成する
    def _generate_all_jobs(self):
        hp = self._calc_HP()
        self._allocate_period_from_src()

        #max_job_numは、応答時間を求める関係上snkノードの   job_numにしている
        max_job_num = 1
        for node in self._nodes:
            self._jobs.append(node)
            job_num = int(hp/node.period)
            if node.id in self.snk:
                max_job_num = job_num
            for n in range(job_num):
                new_job = Node(node.c, 
                               node.k,
                               node.id,
                               node.period,
                               node.seed,
                               activate_num=n+2,
                               trigger_edge=node.trigger_edge,
                               timer_flag=node.timer_flag,
                               laxity=node.laxity)
                self._jobs.append(new_job)
        return max_job_num
    
    
    def sort_jobs(self):
        max_job_num = self._generate_all_jobs()
        tmp_list = []
        tmp_src_list = []
        priority_queue = []
        for n in range(max_job_num):
            for node in self._jobs:
                if node.activate_num == n+1:
                    if node.id in self.src:
                        tmp_src_list.append(node)
                    else:
                        tmp_list.append(node)
            tmp_src_list.sort(key=lambda x: x.laxity)
            tmp_list.sort(key=lambda x: x.laxity)
            
            
            priority_queue.extend(tmp_src_list)
            priority_queue.extend(tmp_list)
            # if n == 1:
            #     for n in priority_queue:
            #         print(n.id)
            tmp_list = []
            tmp_src_list = []
        return priority_queue
    
    # 新しいジョブを作成する関数
    def make_new_job(self, node: Node):
        now_active_num = node.activate_num
        new_job = Node(
            node.c, 
            node.k,
            node.id,
            node.period,
            node.seed,
            require_core_num=node.require_core_num,
            activate_num=node.activate_num,
            trigger_edge=node.trigger_edge,
            timer_flag=node.timer_flag,
            laxity=node.laxity+node.period*(now_active_num-1),
            util=node.util
        )
        return new_job
    

    # 修論用
    def _priorities(self, node: Node) -> list[int]:
        hp_list = []
        lp_list = []
        for nd in self.nodes:
            # ガード節
            if node.id == nd.id:
                continue

            if nd.laxity <= node.laxity:
                node.hp_list=nd.id

            if nd.laxity > node.laxity:
                node.lp_list=nd.id
        
        return hp_list, lp_list
    

    # 修論用
    def _low_priorities(self, node: Node) -> list[int]:
        lp_list = []
        for nd in self.nodes:
            # ガード節
            if node.id == nd.id:
                continue

            if nd.laxity > node.laxity:
                lp_list.append(nd.id)
        
        return lp_list
    


    




        



