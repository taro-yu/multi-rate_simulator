import random
from .dag_timer import DAG

class DecideCoreNum:
    def __init__(
        self,
        method_name: str,
        dag: DAG
    ):
        self._method_name = method_name

    def deceide_core_num(
           self,
    ):
        if self._method_name == 'okamu':
            pass
        elif self._method_name == 'yutaro':
            pass



    def assigh_req_cores(self):
        pass



    def _assign_req_cores(self):
        idx = 0
        q = math.log(2)
        assigned_core_num = 0
        for node in self._dag.nodes:
            heavy_task_flag = True if node.util > 1 else False
            can_decide_flag = False
            
            #ヘビータスクの場合
            if heavy_task_flag:
                req_core_num = _require(node)
                if idx + req_core_num > self._total_core_num:
                    # 対策を考える
                    print("heavy_exit")
                    exit(0)
                else:
                    for n in range(req_core_num):
                        self._task_map[idx].append(node.id)
                        idx += 1
                        assigned_core_num += 1
                    node.require_core_num = req_core_num
                    can_decide_flag = True
            # ライトタスクの場合
            else:
                for n in range(self._total_core_num):
                    total_util = 0
                    m = self._total_core_num
                    for id in self._task_map[n]:
                        total_util += self._dag.nodes[id].util
                    if node.util + total_util < q:
                        self._task_map[n].append(node.id)
                        node.require_core_num = 1
                        can_decide_flag = True
                        assigned_core_num += 1
                        break
                if can_decide_flag is None:
                    if idx >= self._total_core_num - 1:
                        #対策を考える
                        print("light_exit")
                        exit(0)
                    self._task_map[idx].append(node.id)
                    idx += 1
                    assigned_core_num = 0
            
            self._additional_cores(
                assigned_core_num,
                self._task_map,
                self._dag,
                self._total_core_num
            )
        
        def _require(node):
            wcet_n = node.c
            req_core_num = 1

            while wcet_n > node.period:
                req_core_num += 1
                wcet_n = self._req_parallel_ex_time(node, req_core_num)

            return req_core_num
        
    def _additional_cores(
            self, 
            assigned_core_num,
            task_map,
            dag,
            total_core_num
    ):
        
        idx = assigned_core_num
        while idx < total_core_num:
            target_node = self._req_node_by_okamu()
            for list_id, task_in_core in enumerate(self._task_map):
                if len(task_in_core) >= 2 and target_node.id in task_in_core:
                    self._task_map[list_id] = [n for n in self._task_map[list_id] if n != target_node.id]
            target_node.require_core_num += 1
            idx += 1












#     #修論用：コア数決定 by okamuさん IEEE Access
#    def _decide_require_core_num_by_okamu():
#         seed = 0
#         # print("num_of_timer = "+str(self._dag.num_of_timer))
#         for node in self._dag.nodes:

#             random.seed(seed)
#             require_core_num = random.randint(1, 9) 
#             # require_core_num = 
#             node.require_core_num = require_core_num
#             seed += 1


#     #修論用：コア数決定 by refm
#    def _decide_require_core_num_by_okamu():
#         seed = 0
#         # print("num_of_timer = "+str(self._dag.num_of_timer))
#         for node in self._dag.nodes:

#             random.seed(seed)
#             require_core_num = random.randint(1, 9) 
#             # require_core_num = 
#             node.require_core_num = require_core_num
#             seed += 1
    
