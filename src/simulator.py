from numpy import argmin, argmax
from dag_timer import DAG, Node
from itertools import combinations
from cluster_selection import ClusterSlectionMethods
import math, copy, random

class Simulator():

    def __init__(
            self,
            dag: DAG,
            cluster_num: int,
            cluster_core_num: int,
            cluster_comm_ratio: float,
            selection_method_name: str, # proposed, greedy, best, EFT
            heavy_task_num: int | None = None,
    ):
        # 基本パラメータ
        self._dag = dag
        self._cluster_num = cluster_num
        self._cluster_core_num = cluster_core_num
        self._cluster_comm_ratio = cluster_comm_ratio
        self._cluster_comm_time = 1 * self._cluster_comm_ratio
        self._heavy_task_num = heavy_task_num
        self._selection_method_name = selection_method_name
        self._cluser_remain_cores = [self._cluster_core_num for n in range(self._cluster_num)]
        self._cluster_remain_available = [[True for n in range(self._cluster_core_num)] for l in range(self._cluster_num) ]

        # クラスタ間通信の回数記録用
        self._total_inter_cc_cost = 0
        self._total_intra_cc_cost = 0


        #キューを作成
        self._wait_queue = []
        self._execution_list = []
        self._timer_nodes = []

        #シミュレーション経過時間
        self._sim_time = 0


    #使用できるコアをheavy_task_num個に分けて、heavy_task_num個のタスクのparalle_numに設定する
    #均等に分けられない場合（余りが出る場合）、余った分を一つづつ選ばれたタスクに追加していく
    #例：72コアを5つのタスクに割り当てる場合、[16, 16, 15, 15, 15]となる
    def _decide_require_core_num_heavy(self, heavy_task_num):
        pass

    #2~5コアをタイマノード以外のすべてに割り当てる
    def _decide_require_core_num_light(self):
        pass


    

    # main関数
    def Scheduling(
            self,
            dag_number, 
            method_name: str,
            task_name: str = "heavy" #"heavy" or "light"
        ):
        

        if task_name == "heavy":
            self._decide_require_core_num_heavy(self._heavy_task_num)
        elif task_name == "light":
            self._decide_require_core_num_light()

        self._simulator(method_name)

        return
        



    def _simulator(
        self,
        method_name
    ):
        HP = self._dag_calc_HP
        cluster_selector = ClusterSlectionMethods()
        
        # タイマーノードを一か所に集めておく+初めに実行できるジョブを生成
        for node in self._dag.nodes:
            if node.timer_flag is True:
                self._timer_nodes.append(node)
                self._wait_queue.append(self._dag.make_new_job(node))
        
        # 途中のタイマノードに専用コアを割り当てる
        for timer_job in self._wait_queue:
            if timer_job.id not in self._dag.src:
                for cluster_id in range(self._cluster_num):
                    for cluster_core_id, core_flag in enumerate(self._cluster_remain_available[cluster_id]):
                        if core_flag is True:
                            core_id = self._calc_core_id(cluster_id, cluster_core_id)
                            timer_job.core(core_id)
                            self._dag.nodes[timer_job.id].allocated_cores(core_id)
                            self._cluster_remain_available[cluster_id][cluster_core_id] = False
                            self._cluser_remain_cores[cluster_id] -= 1
                            break
                    if len(timer_job.core) != 0:
                        break
            




        # シミュレーション開始
        while self._sim_time <= HP:

            # 実行が完了したノードの対応
            for list_id, ex_job in enumerate(self._execution_list):
                if ex_job.finish is True: 
                    
                    if ex_job.timer_flag is True or ex_job.id not in self._dag.src:
                        pass #途中のタイマノードならコアを解放しない
                    else:
                        self._release_cores(ex_job)
                    self._execution_list.pop(list_id)
                    # 後続ノードの中で実行可能となったものを待ちキューに追加
                    if self._dag.successors(ex_job.id) is not None:
                        for succ in self._dag.successors(ex_job.id):
                            if self._dag.nodes[succ].trigger_edge != ex_job.id:
                                continue
                            else:
                                self._wait_queue.append(self._dag.make_new_job(self._dag.nodes[succ]))


            # タイマノードの周期が来ていたらジョブを追加
            if self._sim_time != 0:
                for timer_node in self._timer_nodes:
                    if timer_node.period % self._sim_time == 0:
                        timer_node.activate_num(1)
                        self._wait_queue.append(self._dag.make_new_job(timer_node))
            
            # 待ちキューをlaxityの値でソート
            self._wait_queue.sort(key=lambda x: x.laxity)

            # 実行可能なものを実行
            for wait_job in self._wait_queue:
                if wait_job.require_core_num > sum(self._cluser_remain_cores):
                    break
                else:
                    # クラスタを選択
                    
                    if wait_job.timer_flag is True and wait_job.id not in self._dag.src:
                    # 途中のタイマノード
                        selected_clusters = []
                        selected_clusters.append(self._dag.nodes[wait_job.id].allocated_cores[0])
                    else:
                    # それ以外
                        selected_clusters = cluster_selector.select_clusters( # 別ファイルで定義
                                                                method_name,
                                                                self._dag,
                                                                wait_job.id,
                                                                wait_job.require_core_num,
                                                                self._cluster_core_num,
                                                                self._cluster_remain_available
                                                            ) 
                    assert selected_clusters != None

                    # コアの確保
                    allocate_count = 0
                    for cluster_id in selected_clusters:
                        for cluster_core_id, core_flag in enumerate(self._cluster_remain_available[cluster_id]):
                            if core_flag is True and allocate_count != wait_job.require_core_num:
                                core_id = self._calc_core_id(cluster_id, cluster_core_id)
                                wait_job.core(core_id)
                                self._cluster_core_num[cluster_id] -= 1
                                self._cluster_remain_available[cluster_id][cluster_core_id] = False

                    # 並列処理によるwcetの変化
                    if len(wait_job.core) >= 2:
                        self._new_wcet(wait_job)
 
                    # クラスタ間通信の時間を追加 (job.cにcomm_timeを追加するため、self._new_wcetよりも後に実行)
                    self._add_cc_comm_time(wait_job)
                    
                    # 実行中リストに追加
                    self._execution_list.append(wait_job)
            

            # 時間を一つ進める+残り実行時間をマイナス
            self._sim_time += 1
            for job_id, ex_job in enumerate(self._execution_list):
                if ex_job.remain_ex_time - 1 == 0: 
                    ex_job.finish = True
                else:
                    ex_job.remain_ex_time(-1)
     

    def _release_cores(self, ex_job: Node):
        self._dag.nodes[ex_job.id].allocated_cores_clear()
        for core in ex_job.core:
            cluster_id, cluster_core_id = self._calc_cluster_index(core)
            self._cluster_remain_available[cluster_id][cluster_core_id] = True
            self._cluster_remain_core[cluster_id] += 1
            self._dag.nodes[ex_job.id].allocated_cores(core)

        # errorチェック
        sum_available = 0
        for cluster_id in range(self._cluster_num):
            sum_available += self._cluster_remain_available[cluster_id].count(True)
        assert sum(self._cluster_remain_core) == sum_available




    # 確保したコアが、どのクラスタ所属で、そのクラスタで何番目のコアかを調べる
    # ex) 5クラスタ, 一クラスタ当たり16コアの場合, core_id = 10 -> cluster_id = 0, cluster_core_id = 10 
    def _calc_cluster_index(self, core_id: int) -> tuple[int, int]:
        cluster_id = int(core_id / self._cluster_core_num)  
        cluster_core_id = core_id % self._cluster_core_num 
        return (cluster_id, cluster_core_id)
    
    def _calc_core_id(self, cluster_id: int, cluster_core_id: int):
        core_id = cluster_id*self._cluster_core_num + cluster_core_id
        # print("core_id="+str(core_id))
        # print("cluster_id="+str(cluster_id))
        # print("cluster_core_id="+str(cluster_core_id))
        return core_id
    

    def _add_cc_comm_time(self, job: Node):
        inter_node_frag = False # ノード間クラスタ通信が行われるか
        intra_node_flag = False #　ノード内クラスタ通信が行われるか
        cc_cost = 0 #ノード内クラスタ通信のコスト　（2クラスタでクラスタ間通信⇒1, 3クラスタで行われている⇒2, ...）
        cc_list = []

        # ノード間
        if len(self._dag.predecessors(job.id)) != 0:
            core = {x//self._cluster_num for x in job.core}
            for pre in self._dag.predecessors(job.id):
                core_pre = {x//self._cluster_num for x in self._dag.nodes[pre].allocated_cores}
                pop_and_pre = core & core_pre
                if len(core - pop_and_pre) != 0:
                    inter_node_frag = True
            if inter_node_frag is True:
                self._total_inter_cc_cost += self._cluster_comm_time
        
        # ノード内
        if len(job.id.core) > 1:
            for core_id in job.core:
                cluster_id = int(core_id / self._cluster_num)
                if len(cc_list) == 0:
                    cc_list.append(cluster_id)
                elif cluster_id not in cc_list:
                    cc_list.append(cluster_id)
            cc_cost = (len(cc_list) -1 ) * self._cluster_comm_time
            if len(cc_list) > 1:
                intra_node_flag = True
        
        self._total_intra_cc_cost += cc_cost

        if inter_node_frag is True and intra_node_flag is True:
            job.c += self._cluster_comm_time + cc_cost
            # print("cost1="+str(self._cc_comm_time + cc_cost))
        elif inter_node_frag is True and intra_node_flag is False:
            job.c += self._cluster_comm_time
            # print("cost2="+str(self._cc_comm_time))
        elif inter_node_frag is False and intra_node_flag is True:
            job.c += cc_cost
            # print("cost3="+str(cc_cost))

        
        # return inter_node_frag, intra_node_flag
    

    def _new_wcet(self, job: Node):

        base_wcet = job.c
        K = job.k
        N = len(job.core)
    
        #与えられたコア数で並列処理すると、もとのWCETが何倍速になるのかをアムダールの式で計算
        assert N != 0

        speed_up = 1 / ((1-K) + (K/N))

        #len(self._dag.nodes[node_index].core) <= core_num) 
        #up_speedをもとに、速くなったWCETを求め、値を更新
        # if self._dag.nodes[node_index].c > math.ceil(base_wcet / up_speed):
        job.c = math.ceil(base_wcet / speed_up)

    
                
    




