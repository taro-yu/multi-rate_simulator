from .dag_timer import DAG, Node
from itertools import combinations
from .cluster_selection import ClusterSlectionMethods
import math, copy, random

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

        #シミュレーション経過時間
        self._sim_time = 0

        # 何でも用
        self._count = 0
    
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

        self._simulator(self._method_name)

        return
        



    def _simulator(
        self,
        method_name
    ):
        HP = self._dag._calc_HP()
        self._dag._allocate_period_from_src()
        cluster_selector = ClusterSlectionMethods()
        # print(HP)
        
        # タイマーノードを一か所に集めておく+初めに実行できるジョブを生成
        for node in self._dag.nodes:
            if node.timer_flag is True:
                self._timer_nodes.append(node)
                new_job = self._dag.make_new_job(node)
                new_job.release_time = self._sim_time
                self._wait_queue.append(new_job)
        
        # 途中のタイマノードに専用コアを割り当てる
        # for timer_node in self._timer_nodes:
        #     if timer_node.id not in self._dag.src:
        #         for cluster_id in range(self._cluster_num):
        #             for cluster_core_id, core_flag in enumerate(self._cluster_remain_available[cluster_id]):
        #                 if core_flag is True:
        #                     core_id = self._calc_core_id(cluster_id, cluster_core_id)
        #                     timer_node.allocated_cores = core_id
        #                     self._cluster_remain_available[cluster_id][cluster_core_id] = False
        #                     self._cluster_remain_cores[cluster_id] -= 1
        #                     break
        #             if len(timer_node.allocated_cores) != 0:
        #                 break

        # シミュレーション開始
        snk_id = self._dag.snk[0]

        while self._sim_time <= HP or self._dag.nodes[snk_id].FT is None:

            # 実行が完了したノードの対応
            ex_to_wait_jobs = []
            for ex_list_id, ex_job in enumerate(self._execution_list):
                # print("job_id = "+str(ex_job.id)+" ex_job.c = "+ str(ex_job.c))

                if ex_job.finish is True:
                    ex_to_wait_jobs.append(ex_list_id)                  
                    self._dag.nodes[ex_job.id].activate_num = 1
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
                        self._dag.nodes[ex_job.id].FT = self._sim_time
                        response_time = self._calc_response_time()
                        if response_time is not None:
                            self._response_times.append(response_time)
            
            self._execution_list = [job for id, job in enumerate(self._execution_list) \
                                                                    if id not in ex_to_wait_jobs]


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
                    # クラスタを選択
                    # print("ex_job = "+str(wait_job.id))
                    # if wait_job.timer_flag is True and wait_job.id not in self._dag.src:
                    # # 途中のタイマノード
                    #     wait_job.core = self._dag.nodes[wait_job.id].allocated_cores[0]
                    # else:
                    # それ以外
                    selected_clusters = cluster_selector.select_clusters( # 別ファイルで定義
                                                            self._dag,
                                                            wait_job.id,
                                                            wait_job.require_core_num,
                                                            self._cluster_remain_cores,
                                                            self._cluster_remain_available,
                                                            method_name
                                                        ) 
                    assert selected_clusters != None
                    # if wait_job.id in [12, 8, 7, 15]:
                    
                    #     print("selected_cluster = "+str(selected_clusters))
                    # if 100 < self._sim_time and self._sim_time <200:
                    #     # if len(selected_clusters) >= 2:
                    #     print("\n")
                    #     print("job_id = "+str(wait_job.id))
                    #     print("req_core = "+str(wait_job.require_core_num)+", selected_c="+str(selected_clusters)+", remain_cores="+str(self._cluster_remain_cores))

                    # コアの確保
                        # print("req_core="+str(wait_job.require_core_num)+", before_cores="+str(self._cluster_remain_cores))
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
                    # if len(selected_clusters) >= 2:
                    # if self._sim_time < 100:
                    # if 100 < self._sim_time and self._sim_time <200:
                    #     # if len(selected_clusters) >= 2:
                    #     print("remain_cores = "+str(self._cluster_remain_cores)+", selected_clusters = "+str(selected_clusters))
                    # # 並列処理によるwcetの変化
                    if len(wait_job.core) >= 2:
                        self._new_wcet(wait_job)
                    # print("after_cores="+str(self._cluster_remain_cores))

                    # クラスタ間通信の時間を追加 (job.cにcomm_timeを追加するため、self._new_wcetよりも後に実行)
                    self._add_cc_comm_time(wait_job)
                    
                    # 実行中リストに追加 & waitキューから除外
                    self._execution_list.append(wait_job)

                    # 並列実行時間＋クラスタ間通信＋待ち時間を応答時間算出のために定義
                    self._dag.nodes[wait_job.id].c_for_respo = wait_job.c + (self._sim_time - wait_job.release_time)
                    

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

    
    def _calc_response_time(self) -> int:
        # #トリガノードとなっている入口ノードを選び出す
        # trigger_timer_node = []
        # for src in self._dag.src:
        #     for succ in self._dag.successors(src):
        #         if self._dag.nodes[succ].trigger_edge == src:
        #             trigger_timer_node.append(src)
        #             break
        
        # #入口ノードがトリガエッジでない場合
        # if len(trigger_timer_node) == 0:
        #     for node in self._timer_nodes:
        #         if node.timer_flag is True and node.id not in self._dag.src:
        #             for succ in self._dag.successors(node.id):
        #                 if self._dag.nodes[succ].trigger_edge == node.id:
        #                     trigger_timer_node.append(node.id)
        #                     break
        
        # #選んだタイマノードの中で、周期が最も大きいものを選ぶ
        # max_period = 0
        # max_period_id = None
        # for id in trigger_timer_node:
        #     if self._dag.nodes[id].period > max_period:
        #         max_period = self._dag.nodes[id].period
        #         max_period_id = id
        
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
        job.set_new_wcet(math.ceil(base_wcet / speed_up))

    

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



    #修論用：コア数決定 by okamuさん IEEE Access
    def _decide_require_core_num_by_okamu(self):
        seed = 0
        # print("num_of_timer = "+str(self._dag.num_of_timer))
        for node in self._dag.nodes:

            random.seed(seed)
            require_core_num = random.randint(1, 9) 
            # require_core_num = 
            node.require_core_num = require_core_num
            seed += 1


    #修論用：コア数決定 by refm
    def _decide_require_core_num_by_okamu(self):
        seed = 0
        # print("num_of_timer = "+str(self._dag.num_of_timer))
        for node in self._dag.nodes:

            random.seed(seed)
            require_core_num = random.randint(1, 9) 
            # require_core_num = 
            node.require_core_num = require_core_num
            seed += 1



