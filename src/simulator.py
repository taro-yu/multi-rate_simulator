from .dag_timer import DAG, Node
from itertools import combinations
from .cluster_selection import ClusterSlectionMethods
import math, copy, random, networkx

class Simulator():

    def __init__(
            self,
            dag: DAG,
            cluster_num: int,
            cluster_core_num: int,
            cluster_comm_ratio: float,
            method_name: str, # proposed, greedy, best, EFT
            heavy_task_num: int | None = None,
    ):
        # 基本パラメータ
        self._dag = dag
        self._cluster_num = cluster_num
        self._cluster_core_num = cluster_core_num
        self._total_core_num = cluster_num * cluster_core_num
        self._cluster_comm_ratio = cluster_comm_ratio
        self._cluster_comm_time = 1 * self._cluster_comm_ratio
        self._method_name = method_name
        self._heavy_task_num = heavy_task_num
        self._method_name = method_name
        self._cluster_remain_cores = [self._cluster_core_num for n in range(self._cluster_num)]
        self._cluster_remain_available = [[True for n in range(self._cluster_core_num)] for l in range(self._cluster_num) ]

        # クラスタ間通信の回数記録用
        self._total_inter_cc_cost = 0
        self._total_intra_cc_cost = 0
        self._intra_core_num = []


        #キューを作成
        self._wait_queue = []
        self._execution_list = []
        self._timer_nodes = []
        self._response_times = []
        self._response_times_c = []

        #シミュレーション経過時間
        self._sim_time = 0

        # 何でも用
        self._count = 0

        # 修論用
        self._task_map = [[] for n in range(self._total_core_num) ]
        self._parallel_num_threshold = 10
        self._largest_path = None
        self._allocate_cores = 0
    
    # main関数
    def Scheduling(
            self,
            # dag_number, 
            task_name: str = "heavy" #"heavy" or "light"
        ):
        

        if task_name == "heavy":
            self._decide_require_core_num_heavy(self._heavy_task_num)
        elif task_name == "light":
            self._decide_require_core_num_light()
        elif task_name == "okamu":
            result = self._core_allocation_by_okamu()
            if result is False:
                return False
        elif task_name == "yutaro":
            result = self._core_allocation_by_yutaro()
            if result is False:
                return False

        self._simulator(self._method_name, task_name)

        return True
        



    def _simulator(
        self,
        method_name,
        task_name: str
    ):
        HP = self._dag._calc_HP()
        self._dag._allocate_period_from_src()
        cluster_selector = ClusterSlectionMethods()
        # print(HP)

        # total = 0
        # for id in self._largest_path:
        #     total += self._dag.nodes[id].require_core_num
        #     print("id = "+str(id)+", req = "+str(self._dag.nodes[id].require_core_num))
        # print("total = "+str(total))
        
        # タイマーノードを一か所に集めておく+初めに実行できるジョブを生成
        for node in self._dag.nodes:
            if node.timer_flag is True:
                self._timer_nodes.append(node)
                new_job = self._dag.make_new_job(node)
                new_job.release_time = self._sim_time
                self._wait_queue.append(new_job)
                # print("timer = "+str(node.id))
        
        # シミュレーション開始
        snk_id = self._dag.snk[0]

        # HPまでやるか、少なくとも一回は出口ノードがfinishするか
        while self._sim_time <= HP or len(self._dag.nodes[snk_id].finish_time) == 0:

            # 実行が完了したノードの対応
            finish_jobs = []
            for ex_list_id, ex_job in enumerate(self._execution_list):
                # print("job_id = "+str(ex_job.id)+" ex_job.c = "+ str(ex_job.c))

                if ex_job.finish is True:
                    finish_jobs.append(ex_list_id)
                    self._dag.nodes[ex_job.id].finish_time = self._sim_time         
                    self._dag.nodes[ex_job.id].activate_num = 1
                    # self._dag.nodes[ex_job.id].FT = self._sim_time
                    # print("job_id = "+str(ex_job.id)+" ex_job.c = "+ str(ex_job.c))


                    # if ex_job.timer_flag is True and ex_job.id not in self._dag.src:
                    #     pass #途中のタイマノードならコアを解放しない
                    # else:
                    self._release_cores(ex_job)

                    # 後続ノードの中で実行可能となったものを待ちキューに追加
                    if len(self._dag.successors(ex_job.id)) != 0:
                        for succ in self._dag.successors(ex_job.id):
                            if self._dag.nodes[succ].trigger_edge != ex_job.id:
                                continue
                            else:
                                new_job = self._dag.make_new_job(self._dag.nodes[succ])
                                new_job.release_time = self._sim_time
                                self._wait_queue.append(new_job)
                    
                    # 出口ノードが終了したら、終了時間を求め、応答時間を算出
                    if ex_job.id in self._dag.snk:
                        # FTは、最終ノードが終わるまでシミュレーションを行うための仕組み
                        if task_name == 'okamu' or 'yutaro':
                            response_time, response_time_c = self._calc_response_time_2()
                            if response_time is not None:
                                self._response_times.append(response_time)
                                self._response_times_c.append(response_time_c)

                        else:
                            response_time, response_time_c = self._calc_response_time()
                            if response_time is not None:
                                self._response_times.append(response_time)
                                self._response_times_c.append(response_time_c)
                        # response_time = self._calc_response_time()
                        # if response_time is not None:
                        #     self._response_times.append(response_time)
            
            self._execution_list = [job for id, job in enumerate(self._execution_list) \
                                                                    if id not in finish_jobs]


            # タイマノードの周期が来ていたらジョブを追加
            if self._sim_time != 0:
                for timer_node in self._timer_nodes:
                    if self._sim_time % timer_node.period == 0:
                        timer_node.activate_num = 1
                        new_job = self._dag.make_new_job(timer_node)
                        new_job.release_time = self._sim_time
                        self._wait_queue.append(new_job)
            
            # 待ちキューをlaxityの値でソート
            self._wait_queue.sort(key=lambda x: x.laxity)


            # 実行可能なものを実行
            wait_to_ex_job = 0
            for wait_job in self._wait_queue:
                if wait_job.require_core_num > sum(self._cluster_remain_cores):
                    # print("req="+str(wait_job.require_core_num)+"sum = "+str(sum(self._cluster_remain_cores)))
                    break
                else:
                    selected_clusters = cluster_selector.select_clusters( # 別ファイルで定義
                                                            self._dag,
                                                            wait_job.id,
                                                            wait_job.require_core_num,
                                                            self._cluster_remain_cores,
                                                            self._cluster_remain_available,
                                                            method_name
                                                        ) 
                    assert selected_clusters != None

                    allocate_count = 0
                    for cluster_id in selected_clusters:
                        for cluster_core_id, core_flag in enumerate(self._cluster_remain_available[cluster_id]):
                            if core_flag is False:
                                pass
                            elif core_flag is True and allocate_count != wait_job.require_core_num:
                                core_id = self._calc_core_id(cluster_id, cluster_core_id)
                                wait_job.core = core_id
                                self._cluster_remain_cores[cluster_id] -= 1
                                self._cluster_remain_available[cluster_id][cluster_core_id] = False
                                allocate_count += 1
                    # # 並列処理によるwcetの変化
                    if len(wait_job.core) >= 2:
                        self._new_wcet(wait_job)
                    # print("after_cores="+str(self._cluster_remain_cores))

                    # クラスタ間通信の時間を追加 (job.cにcomm_timeを追加するため、self._new_wcetよりも後に実行)
                    self._add_cc_comm_time(wait_job)
                    
                    # 実行中リストに追加 & waitキューから除外
                    self._execution_list.append(wait_job)


                    # 並列実行時間＋クラスタ間通信＋待ち時間を応答時間算出のために定義
                    # if wait_job.id in self._largest_path:
                        # print("id = "+str(wait_job.id)+"c = "+str(wait_job.c)+", wait_time = "+str(self._sim_time - wait_job.release_time))
                    # self._dag.nodes[wait_job.id].c_for_respo = wait_job.c + (self._sim_time - wait_job.release_time)
                    self._dag.nodes[wait_job.id].c_for_respo = wait_job.c
                    self._dag.nodes[wait_job.id].start_time = self._sim_time

                    assert len(self._dag.nodes[wait_job.id].c_for_respo) == len(self._dag.nodes[wait_job.id].start_time)
                    
                                         

                    # print("new_ex_job.laxity = "+str(wait_job.laxity))
                    wait_to_ex_job += 1
            # wait_queueから実行された分をwait_queueから削除
            for n in range(wait_to_ex_job):
                self._wait_queue.pop(0)

            # 時間を一つ進める+残り実行時間をマイナス
            self._sim_time += 1
            for id, ex_job in enumerate(self._execution_list):
                # if self._sim_time < 10:
                # print("job_id="+str(ex_job.id)+": remain_ex_time = "+str(ex_job.c))
                if ex_job.c - 1 <= 0: 
                    ex_job.finish = True
                else:
                    ex_job.c = -1
        # print("count = "+str(self._count))

    def _release_cores(self, ex_job: Node):
        self._dag.nodes[ex_job.id].allocated_cores_clear()
        for core in ex_job.core:
            cluster_id, cluster_core_id = self._calc_cluster_index(core)
            self._cluster_remain_available[cluster_id][cluster_core_id] = True
            self._cluster_remain_cores[cluster_id] += 1
            self._dag.nodes[ex_job.id].allocated_cores = core

        # errorチェック
        sum_available = 0
        for cluster_id in range(self._cluster_num):
            sum_available += self._cluster_remain_available[cluster_id].count(True)
        assert sum(self._cluster_remain_cores) == sum_available

    
    #IEEE Access用
    def _calc_response_time(self) -> int:

        node_id = self._dag.snk[0]
        response_time = 0
        is_finish = False

        # snkノードから順に実行時間を足していく
        while (is_finish is False):
            #     print(self._dag.nodes[node_id].timer_flag)
            response_time += self._dag.nodes[node_id].c_for_respo
            # print("node_id = "+str(node_id)+" c_for_respo = "+str(self._dag.nodes[node_id].c_for_respo)+" require_core_num = "+str(self._dag.nodes[node_id].require_core_num))
            
            if self._dag.nodes[node_id].timer_flag is True:
                is_finish = True
                # print(response_time)
                return response_time

            
            node_id = self._dag.nodes[node_id].trigger_edge
            assert node_id is not None
    
    # 修論用
    def _calc_response_time_2(self):
        
        
        assert self._largest_path is not None or self._allocate_cores == self._total_core_num


        response_time = 0
        response_time_c = 0
        # 追加のコアが割り当てられなかった場合は、比較を行わない
        if self._largest_path is None and self._allocate_cores == self._total_core_num:
            return None, None
        # print(self._largest_path)


        snk_id = self._dag.snk[0]

        #最新のスタートタイムを取得
        start_time = self._dag.nodes[snk_id].start_time[-1]
        time_index = None

        # print(self._largest_path)

        list_id = len(self._largest_path) - 1

        # for id in self._largest_path:
        #     for start, finish in zip(self._dag.nodes[id].start_time, self._dag.nodes[id].finish_time):
        #         print("node_id = "+str(id)+", start = "+str(start)+", finish = "+str(str(finish)))

        for node_id in reversed(self._largest_path):
            # print("now node_id = "+str(node_id)+", now list_id = "+str(list_id))
            # print("id = "+str(id)+" c_for = "+str(self._dag.nodes[id].c_for_respo)+", c = "+str(self._dag.nodes[id].c)+", req = "+str(self._dag.nodes[id].require_core_num))
            if node_id in self._dag.src:
                assert time_index is not None
                if self._dag.nodes[node_id].c_for_respo[time_index] is None:
                    return None, None
                response_time += self._dag.nodes[node_id].c_for_respo[time_index]
                response_time_c += self._dag.nodes[node_id].c_for_respo[time_index]
                list_id -= 1

                # print("node_id = "+str(node_id)+", start = "+str(start_time)+", pre_ft = "+str(str(ft)))
                # print("active_num="+str(self._dag.nodes[node_id].activate_num))

                # print("node_id = "+str(node_id)+", respo = "+str(response_time))

            
            else:
                if node_id == snk_id:
                    time_index = self._dag.nodes[snk_id].start_time.index(start_time)

                assert time_index is not None

                # print("be="+str(time_index))
                # print(node_id)
                # print(self._dag.nodes[node_id].start_time)
                start_time = self._dag.nodes[node_id].start_time[time_index]
                c_for_respo = self._dag.nodes[node_id].c_for_respo[time_index]
                if c_for_respo is None:
                    return None, None
                
                pre_max_ft = -1
                pre_time_index = None

                pre_node_id = self._largest_path[list_id-1]
                for id, ft in enumerate(self._dag.nodes[pre_node_id].finish_time):
                    # print("node_id = "+str(node_id)+", ft = "+str(ft))
                    if ft <= start_time and ft > pre_max_ft:
                        pre_max_ft = ft
                        pre_time_index = id
                
                if pre_time_index is None:
                    print("pre_time_index is None")
                    return None, None
                response_time += c_for_respo + (start_time - pre_max_ft)
                response_time_c += c_for_respo
                # print("node_id = "+str(node_id)+", start = "+str(start_time)+", ft = "+str(str(pre_max_ft)))
                time_index = pre_time_index
                list_id -= 1

                # print(self._dag.nodes[pre_node_id].finish_time)
                # print(self._dag.nodes[pre_node_id].start_time)
                # print(pre_node_id)
                # print("af="+str(time_index))

             
             
                # 待ち時間を考慮
                # response_time += self._dag.nodes[id].c_for_respo + (self._dag.nodes[id].start_time - self._dag.nodes[pre_job_id].FT)
                # print(self._dag.nodes[id].start_time - self._dag.nodes[pre_job_id].FT)
                # # print("id = "+str(id)+", pre = "+str(pre_job_id)+", timer = "+str(self._dag.nodes[id].timer_flag) )
                # assert (self._dag.nodes[id].start_time - self._dag.nodes[pre_job_id].FT) >= 0
        
        return response_time, response_time_c


    # 確保したコアが、どのクラスタ所属で、そのクラスタで何番目のコアかを調べる
    # ex) 5クラスタ, 一クラスタ当たり16コアの場合, core_id = 10 -> cluster_id = 0, cluster_core_id = 10 
    def _calc_cluster_index(self, core_id: int) -> tuple[int, int]:
        cluster_id = int(core_id / self._cluster_core_num)  
        cluster_core_id = core_id % self._cluster_core_num 
        return (cluster_id, cluster_core_id)
    
    def _calc_core_id(self, cluster_id: int, cluster_core_id: int):
        core_id = cluster_id*self._cluster_core_num + cluster_core_id
        return core_id
    

    def _add_cc_comm_time(self, job: Node):
        inter_node_frag = False # ノード間クラスタ通信が行われるか
        intra_node_flag = False #　ノード内クラスタ通信が行われるか
        cc_cost = 0 #ノード内クラスタ通信のコスト　（2クラスタでクラスタ間通信⇒1, 3クラスタで行われている⇒2, ...）
        cc_list = []
        pre_cores = set()
        core_pre = set()

        # ノード間
        # タイマノードならノード間クラスタ間通信は追加しない
        # トリガエッジと同じ or トリガエッジが確保したクラスタをすべて使っていたら(包含していたら)OK
        if job.timer_flag is False:
            core = {x//self._cluster_core_num for x in job.core}
            core_pre = {x//self._cluster_core_num for x in self._dag.nodes[job.trigger_edge].allocated_cores}
            if len(core_pre) == 0:
                pass
            else:
                # pre_cores = core_pre | pre_cores
                if core_pre <= core:
                    inter_node_frag = False
                else:
                    inter_node_frag = True
                    self._total_inter_cc_cost += self._cluster_comm_time
        
        # ノード内
        if len(job.core) > 1:
            for core_id in job.core:
                cluster_id = int(core_id / self._cluster_core_num)
                if len(cc_list) == 0:
                    cc_list.append(cluster_id)
                elif cluster_id not in cc_list:
                    cc_list.append(cluster_id)
            
            cc_cost = (len(cc_list) -1 ) * self._cluster_comm_time
            if len(cc_list) > 1:
                intra_node_flag = True
        
        self._total_intra_cc_cost += cc_cost
        if cc_cost >= 1:
            self._intra_core_num.append(cc_cost)
        # print("cc_cost="+str(cc_cost))

        if inter_node_frag is True and intra_node_flag is True:
            job.c = self._cluster_comm_time + cc_cost
            # print("cost1="+str(self._cc_comm_time + cc_cost))
        elif inter_node_frag is True and intra_node_flag is False:
            job.c = self._cluster_comm_time
            # print("cost2="+str(self._cc_comm_time))
        elif inter_node_frag is False and intra_node_flag is True:
            job.c = cc_cost    
        

    def _new_wcet(self, job: Node):

        base_wcet = job.c
        K = job.k
        N = len(job.core)

        #与えられたコア数で並列処理すると、もとのWCETが何倍速になるのかをアムダールの式で計算
        assert N != 0

        speed_up = 1 / ((1-K) + (K/N))
        job.set_new_wcet(base_wcet / speed_up)

    

    #使用できるコアをheavy_task_num個に分けて、heavy_task_num個のタスクのparalle_numに設定する
    #均等に分けられない場合（余りが出る場合）、余った分を一つづつ選ばれたタスクに追加していく
    #例：72コアを5つのタスクに割り当てる場合、[16, 16, 15, 15, 15]となる
    def _decide_require_core_num_heavy(self, heavy_task_num):
        max_parallel_num = (self._total_core_num-self._dag.num_of_timer) // heavy_task_num #商
        remain_core_num = (self._total_core_num-self._dag.num_of_timer) % heavy_task_num #余り
        selected_nodes = []

        count = 0
        seed = 0
        while (count < heavy_task_num):
            random.seed(seed)
            selected_node = random.randint(0, len(self._dag.nodes)-1) 
            

            if self._dag.nodes[selected_node].require_core_num < max_parallel_num:
                self._dag.nodes[selected_node].require_core_num = max_parallel_num
                selected_nodes.append(selected_node)
                count += 1 
                seed += 1
            else:
                seed += 1
        
        #余りがある場合
        while remain_core_num >= 1:
            for selected_node in selected_nodes:
                self._dag.nodes[selected_node].require_core_num += 1
                remain_core_num -= 1

        seed = 0
        for node in self._dag.nodes:

            if node.require_core_num > 1:
                continue

            random.seed(seed)
            core_parallel_num = random.randint(1, 3)
            # core_parallel_num = 1
            node.require_core_num = core_parallel_num
            seed += 1

    #2~5コアをタイマノード以外のすべてに割り当てる
    def _decide_require_core_num_light(self):
        seed = 0
        # print("num_of_timer = "+str(self._dag.num_of_timer))
        for node in self._dag.nodes:

            random.seed(seed)
            require_core_num = random.randint(1, 9) 
            # require_core_num = 
            node.require_core_num = require_core_num
            seed += 1
    

    #修論用

    def _core_allocation_by_okamu(self) -> bool:
        nth_path = 1
        total_parallel_cores = self._allocate_to_under_period()
        self._allocate_cores = total_parallel_cores

        #割り当て失敗の場合、スケジューリング終了
        if total_parallel_cores is None:
            return False

        while(total_parallel_cores < self._total_core_num):
            # print("total_parallel_cores = "+str(total_parallel_cores))
            max_wcet = -1
            max_id = None
            while max_id is None:
                max_path = self._req_max_path(nth_path)
                # print(max_path)
                max_wcet = -1
                for id in max_path:
                    wcet_n = self._req_parallel_ex_time(
                        self._dag.nodes[id],
                        self._dag.nodes[id].require_core_num
                    )
                    # print(self._dag.nodes[id].k)
                    # print("wcet="+str(wcet_n))

                    if wcet_n > max_wcet and self._dag.nodes[id].k != 0 and \
                                self._dag.nodes[id].require_core_num+1 <= self._parallel_num_threshold:
                        max_wcet = wcet_n
                        max_id = id
                        # print(wcet_n)
                        # print(self._dag.nodes[id].k)
                        # print(max_id)
                        # print(self._dag.nodes[max_id].require_core_num)

                if max_id is None:
                    # print(self._dag.nodes[max_id].k)
                    # max_id = None
                    nth_path += 1
                    
            # print("max_wcrt = "+str(max_wcet))
            # print("max_id = "+str(max_id))
            if self._dag.nodes[max_id].require_core_num == 1:
                total_parallel_cores += 2
                self._dag.nodes[max_id].require_core_num += 1
            else:
                total_parallel_cores += 1
                self._dag.nodes[max_id].require_core_num += 1 
            # print("id="+str(max_id)+", req = "+str(self._dag.nodes[max_id].require_core_num))

        
        #割り当て成功
        return True

    def _core_allocation_by_yutaro(self) -> bool:
        nth_path = 1
        total_parallel_cores = self._allocate_to_under_period()
        self._allocate_cores = total_parallel_cores

        #割り当て失敗の場合、スケジューリング終了
        if total_parallel_cores is None:
            return False
        
        while(total_parallel_cores < self._total_core_num):
            # print(total_parallel_cores)
            max_path = self._req_max_path(nth_path)
            selected_id = self._reduction_effectiveness_method(max_path) 
            while selected_id is None:
                nth_path += 1
                max_path = self._req_max_path(nth_path)
                selected_id = self._reduction_effectiveness_method(max_path)

            # print("max_id = "+str(selected_id))
            # print("max_wcrt = "+str(self._dag.nodes[selected_id].wcrt))
            if self._dag.nodes[selected_id].require_core_num == 1:
                total_parallel_cores += 2
                self._dag.nodes[selected_id].require_core_num += 1
            else:
                total_parallel_cores += 1
                self._dag.nodes[selected_id].require_core_num += 1 
            # print("id="+str(selected_id)+", req = "+str(self._dag.nodes[selected_id].require_core_num))
        
        #割り当て成功
        return True
    
    
    def _require(self, node):
        wcet_n = node.c
        req_core_num = 1

        while wcet_n > node.period:
            req_core_num += 1
            wcet_n = self._req_parallel_ex_time(node, req_core_num)
            if req_core_num > self._total_core_num:
                break
        
        # print(req_core_num)
        # print("node.k="+str(node.k)+", period="+str(node.period)+", wcet_n="+str(wcet_n)+", wcet_1="+str(node.c))

        return req_core_num
    
    def _allocate_to_under_period(self): 
        total_parallel_cores = 0

        for node in self._dag.nodes:
            if node.c / node.period < 1 or node.k == 0:
                continue
            req_cores = self._require(node)
            total_parallel_cores += req_cores
            node.require_core_num = req_cores
            # print(total_parallel_cores)
        

        if total_parallel_cores > self._total_core_num:
            return None
        else:
            return total_parallel_cores



    

    def _reduction_effectiveness_method(self, path: list[int]):

        selected_id = None
        tmp_reduction_diff = 0
        total_diff = 0
        # print(path)
        for id in path:
            if self._dag.nodes[id].require_core_num > 1:
                base_c = self._req_parallel_ex_time(
                    self._dag.nodes[id],
                    self._dag.nodes[id].require_core_num
                )
            else:
                base_c = self._dag.nodes[id].c
            new_c = self._req_parallel_ex_time(
                self._dag.nodes[id],
                self._dag.nodes[id].require_core_num+1
            )
            # print("node_id = "+str(id)+", require_core = "+str(self._dag.nodes[id].require_core_num))
            # print("base_c = "+str(base_c)+", new_c = "+str(new_c)+", diff = "+str(base_c - new_c))
            if base_c - new_c > tmp_reduction_diff and self._dag.nodes[id].require_core_num+1 <= self._parallel_num_threshold:
                tmp_reduction_diff = base_c - new_c
                selected_id = id

                #コアを増やしても差が出来なくなったら別のpathに変えるため
                total_diff +=tmp_reduction_diff 
                # print("tmp_diff = "+str(tmp_reduction_diff)+", node_id ="+str(selected_id))
        
        # assert selected_id is not None

        if total_diff == 0:
            return None
        else:
            return selected_id


    
    def _calc_node_wcrt(self, node: Node):
        hp_list = self._dag._high_priorities(node)
        lp_list = self._dag._low_priorities(node)

        # bi (: nodeより優先度が低いタスクの中で最も大きいC^n)を求める
        bi_max = 0
        for lp_id in lp_list:
            if self._dag.nodes[lp_id].require_core_num > 1:
                lp_wcet_n = self._req_parallel_ex_time(
                            self._dag.nodes[lp_id],
                            self._dag.nodes[lp_id].require_core_num
                        )
            else:
                lp_wcet_n = self._dag.nodes[lp_id].c
            if lp_wcet_n > bi_max:
                bi_max = lp_wcet_n
        
        # 優先度が高いタスクによる遅延を計算
        total_hp_delay = 0
        for hp_id in hp_list:
            if self._dag.nodes[hp_id].require_core_num > 1:
                hp_wcet_n = self._req_parallel_ex_time(
                            self._dag.nodes[hp_id],
                            self._dag.nodes[hp_id].require_core_num
                )
            else:
                hp_wcet_n = self._dag.nodes[hp_id].c
            hp_period = self._dag.nodes[hp_id].period
            for n in range(math.ceil(node.period / hp_period)):
                if node.laxity < self._dag.nodes[hp_id].laxity + (n-1) * hp_period:
                    break
                else:
                    total_hp_delay += hp_wcet_n
       
        # 自身の並列実行時間を取得
        if node.require_core_num > 1:
            node_wcet_n = self._req_parallel_ex_time(
                            node,
                            node.require_core_num
                        )
        else:
            node_wcet_n = node.c
        
        # WCRTを求め return
        node_wcrt = node_wcet_n + bi_max + total_hp_delay
        node.wcrt = node_wcrt

        return node_wcrt

    
    def _req_parallel_ex_time(
        self,
        node: Node,
        req_core_num: int
    ):  
        K = node.k
        N = req_core_num

        #与えられたコア数で並列処理すると、もとのWCETが何倍速になるのかをアムダールの式で計算
        assert N != 0

        speed_up = 1 / ((1-K) + (K/N))
        wcet_n = (node.c / speed_up)
        # print(wcet_n)

        return wcet_n
    

    def _req_max_path(self, n:int):

        # pathの中で、トータルwcrtがn番目に大きいpathを選択する
        nth_path = n 
        length = 0
        path_sums = []
        max_respo_chain = []
        for s in self._dag.src:
            for d in self._dag.snk:
                for path in list(networkx.all_simple_paths(self._dag.G, s, d)):
                    # print("s = "+str(s)+"d = "+str(d))
                    tmp_length = 0
                    for i in path:
                        wcrt_i = self._calc_node_wcrt(self._dag.nodes[i])
                        # print(wcrt_i)
                        if self._dag.nodes[i].trigger_edge in path:
                            period_i = self._dag.nodes[i].period
                        else:
                            period_i = 0
                        tmp_length += wcrt_i + period_i
                    path_sums.append((path, tmp_length))
        path_sums.sort(key=lambda x: x[1])
                    # print("max_value = "+str(length))
                    # print("max_path = "+str(max_respo_chain))
        # print(max_respo_chain)
    
        if n == 1 and self._largest_path is None:
            self._largest_path = path_sums[nth_path-1][0]
            # print(self._largest_path)
            # for n in self._largest_path:
            #     print("n="+str(n))
        return path_sums[nth_path-1][0]



