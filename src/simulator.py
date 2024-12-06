from numpy import argmin, argmax
from dag_timer import DAG, Node
from itertools import combinations
import math, copy, random

class Simulator():

    def __init__(
            self,
            dag: DAG,
            cluster_num: int,
            cluster_core_num: int,
            cc_time_ratio: float,
            selection_method_name: str, # proposed, greedy, best, EFT
            heavy_task_num: int | None = None,
    ):
        # 基本パラメータ
        self._dag = dag
        self._cluster_num = cluster_num
        self._cluster_core_num = cluster_core_num
        self._cc_time_ratio = cc_time_ratio
        self._heavy_task_num = heavy_task_num
        self._selection_method_name = selection_method_name
        self._cluser_remain_cores = [self._cluster_core_num for n in range(self._cluster_num)]
        self._cluster_remain_available = [[True for n in range(self._cluster_core_num)] for l in range(self._cluster_num) ]

        # クラスタ間通信の回数記録用
        self._total_comm_between_node = 0
        self._total_comm_within_node = 0

        #キューを作成
        self._wait_queue = []
        self._execution_list = []
        self._timer_nodes = []

        #シミュレーション経過時間
        self._sim_time = 0


    #使用できるコアをheavy_task_num個に分けて、heavy_task_num個のタスクのparalle_numに設定する
    #均等に分けられない場合（余りが出る場合）、余った分を一つづつ選ばれたタスクに追加していく
    #例：72コアを5つのタスクに割り当てる場合、[16, 16, 15, 15, 15]となる
    def _decide_parallel_core_num_heavy(self, heavy_task_num):
        pass

    #2~5コアをタイマノード以外のすべてに割り当てる
    def _decide_parallel_core_num_light(self):
        pass


    


    def Scheduling(
            self,
            dag_number, 
            task_name: str = "heavy" #"heavy" or "light"
        ):
        

        if task_name == "heavy":
            self._decide_parallel_core_num_heavy(self._heavy_task_num)
        elif task_name == "light":
            self._decide_parallel_core_num_light()

        self._simulator()

        return
        



    def _simulator(
        self
    ):
        HP = self._dag_calc_HP

        # タイマーノードを一か所に集めておく+初めに実行できるジョブを生成
        for node in self._dag.nodes:
            if node.timer_flag is True:
                self._timer_nodes.append(node)
                self._wait_queue.append(self._dag.make_new_job(node))




        # シミュレーション開始
        while self._sim_time <= HP:

            # 実行が完了したノードの対応
            for list_id, ex_job in enumerate(self._execution_list):
                if ex_job.finish is True: 
                    self._release_cores(ex_job)
                    self._execution_list.pop(list_id)
                    # 後続ノードの中で実行可能となったものを待ちキューに追加
                    for succ in self._dag.successors(ex_job.id):
                        if self._dag.nodes[succ].trigger_edge != ex_job.id:
                            continue
                        else:
                            self._wait_queue.append(self._dag.make_new_job(self._dag.nodes[succ]))
                else:
                    pass
            
            
            # タイマノードの周期が来ていたらジョブを追加
            for timer_node in self._timer_nodes:
                if timer_node.period % self._sim_time == 0:
                    timer_node.activate_num(1)
                    self._wait_queue.append(self._dag.make_new_job(timer_node))
            
            # 待ちキューをlaxityの値でソート
            self._wait_queue.sort(key=lambda x: x.laxity)

            # 実行可能なものを実行
            for wait_job in self._wait_queue:
                if wait_job.parallel_core_num < sum(self._cluser_remain_cores):
                    break
                else:
                    selected_cores = self._select_clusters() #TODO: 別ファイルからインポートした関数に変更
                    for core in selected_cores:
                        wait_job.core = core
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
        pass

    def _select_clusters(self):
        pass

    
                
    




