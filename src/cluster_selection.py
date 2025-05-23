from itertools import combinations
from .dag_timer import DAG

import copy
import random

class ClusterSlectionMethods():
    
    def __init__(self, kobatomo_seed: int):
        self._seed_for_kobatomo_fit = kobatomo_seed


    # クラスタ選択を行う
    def select_clusters(
            self,
            dag: DAG,
            node_id: int,
            require_core_num: int,
            cluster_remain_cores: list[int],
            cluster_remain_available: list[list[bool]],
            method_name: str #proposed, greedy, best, EFT
            
    ) -> int | list[int] | None:
        # print("at select_cluster: node_id="+str(node_id))
        
        # ガード節
        if require_core_num > sum(cluster_remain_cores):
            return None
        
        parameters = [
            dag,
            node_id, 
            require_core_num,
            cluster_remain_cores,
            cluster_remain_available
        ]

        if method_name == 'proposed' or method_name == 'pro_koba':
            return self._proposed_method(parameters)
        elif method_name == 'greedy':
            return self._greedy_fit(parameters)
        elif method_name == 'best':
            return self._best_fit_mix(parameters)
        elif method_name == 'kobatomo':
            return self._kobatomo_fit(parameters)
        else:
            return self._EFT(parameters)
        

    def _proposed_method(
        self,
        parameters: list[DAG|int|list]
    ):
        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]

        if require_core_num == sum(cluster_remain_cores):
            return self._EFT(parameters)

        if require_core_num <= max(cluster_remain_cores):
            cluster_id = self._pred_fit(parameters)
            if cluster_id != None:
                return cluster_id
            else:
                return self._best_fit(parameters)
        else:
            greedy_ids = self._greedy_fit(parameters)
            comb_ids = self._comb_fit(parameters, len(greedy_ids))
            if comb_ids != None and len(comb_ids) <= len(greedy_ids):
                return comb_ids
            else:
                return greedy_ids


    


# トリガエッジと同じクラスタになるべく割り当てたい
    def _pred_fit(
        self, 
        parameters: list[DAG|int|list]
    ) -> list[int] | None:
        
        dag = parameters[0]
        node_id = parameters[1]
        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]

        if dag.nodes[node_id].timer_flag is True:
            return None
        else:
            pre_nodes_cluster_list =[]
            trigger_edge = dag.nodes[node_id].trigger_edge

            for core_id in dag.nodes[trigger_edge].allocated_cores:
                cluster_id, _ = self._calc_cluster_index(core_id, parameters)
                if len(pre_nodes_cluster_list) == 0:
                    pre_nodes_cluster_list.append(cluster_id)
                elif cluster_id not in pre_nodes_cluster_list:
                    pre_nodes_cluster_list.append(cluster_id)
            if len(pre_nodes_cluster_list) == 1:
                cluster_id = pre_nodes_cluster_list[0]
                if require_core_num <= cluster_remain_cores[cluster_id]:
                    # print("pred")
                    return [cluster_id]
        return None
    

    def _greedy_fit(
        self,
        parameters: list[DAG|int|list]
    ) -> list[int] | int:
        
        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]
        max_core_num = 0
        total_core_num = 0
        max_id = None
        worst_cluster_ids = []
        cluster_remain_cores_copy = copy.deepcopy(cluster_remain_cores)

        while total_core_num < require_core_num:
            for cluster_id, remain_core_num in enumerate(cluster_remain_cores_copy):
                if max_core_num < remain_core_num:
                    max_core_num = remain_core_num
                    max_id = cluster_id
            total_core_num += max_core_num
            worst_cluster_ids.append(max_id)
            cluster_remain_cores_copy[max_id] = -1
            max_core_num = 0
            max_id = None
        return worst_cluster_ids

    def _best_fit(
            self,
            parameters: list[DAG|int|list]
        ) -> list[int]:   

        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]
        best_cluster_id = -1
        min_core_num = 100000000 #大きい数で初期化

        for cluster_id, remain_core_num in enumerate(cluster_remain_cores):
            if remain_core_num >= require_core_num and remain_core_num < min_core_num:
                min_core_num = remain_core_num
                best_cluster_id = cluster_id
        if best_cluster_id != -1:
            return [best_cluster_id]
        
    def _comb_fit(
        self,
        parameters: list[DAG|int|list],
        greedy_elem_num: int
    ) -> tuple | None:
        
        # print("comb")
        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]
        min_length = float('inf')
        min_combination = None
        selected_cluster_ids = []
        # cluster_remain_cores_copy = copy.deepcopy(cluster_remain_cores)

        for r in range(2, greedy_elem_num+1):
            for combination in combinations(cluster_remain_cores, r):
                if sum(combination) == require_core_num and len(combination) < min_length:
                    min_length = len(combination)
                    min_combination = combination
                    # print("comb = "+str(combination))
                    break
            if min_combination is not None:
                break

        if min_combination is None:
            return min_combination
        else:
            for n in min_combination:
                for id, c in enumerate(cluster_remain_cores):
                    if n == c and id not in selected_cluster_ids:
                        selected_cluster_ids.append(id)
                        break
            # print(selected_cluster_ids)
            return selected_cluster_ids

        
        

    def _EFT(
        self,
        parameters: list[DAG|int|list]
    ) -> list[int]:
        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]
        cluster_remain_available = parameters[4]
        selected_cluster_ids = []

        allocate_count = 0
        for cluster_id in range(len(cluster_remain_cores)):
            for core_flag in cluster_remain_available[cluster_id]:
                if core_flag is True:
                    allocate_count += 1
                    if cluster_id not in selected_cluster_ids:
                        selected_cluster_ids.append(cluster_id)
                    if allocate_count == require_core_num:
                        return  selected_cluster_ids


    def _min_fit(
        self,
        parameters: list[DAG|int|list]
    ):
        id = parameters[1]
        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]
        min_core_num = 100000000 #大きい数で初期化
        total_core_num = 0
        min_id = None
        min_cluster_ids = []
        cluster_remain_cores_copy = copy.deepcopy(cluster_remain_cores)

        while total_core_num < require_core_num:
            for cluster_id, remain_core_num in enumerate(cluster_remain_cores_copy):
                if remain_core_num != 0 and remain_core_num < min_core_num:
                    min_core_num = remain_core_num
                    min_id = cluster_id
            # min_core_num = min(cluster_remain_cores_copy)
            # min_id = cluster_remain_cores_copy.index(min_core_num)
            # if min_core_num == 0:
            #     cluster_remain_cores_copy[min_id] = 100000000
            # else:
            total_core_num += min_core_num
            min_cluster_ids.append(min_id)
            cluster_remain_cores_copy[min_id] = 100000000
            min_core_num = 100000000
            min_id = None
        return min_cluster_ids

    # 評価用
    def _best_fit_mix(
        self,
        parameters: list[DAG|int|list]
    ):

        require_core_num = parameters[2]
        cluster_remain_cores = parameters[3]

        if require_core_num <= max(cluster_remain_cores):
            return self._best_fit(parameters)
        else:
            return self._min_fit(parameters)
        
    def _kobatomo_fit(
            self,
            parameters: list[DAG|int|list]
        ) -> list[int]:   
            require_core_num = parameters[2]
            cluster_remain_cores = parameters[3]
            cluster_remain_cores_copy = copy.deepcopy(cluster_remain_cores)
            total_core_num = 0
            selected_cluster_ids = []
            self._seed_for_kobatomo_fit += 1
            
            while total_core_num < require_core_num:
                random.seed(self._seed_for_kobatomo_fit)
                # print("seed = "+str(self._seed_for_kobatomo_fit))
                selected_cluster_id = random.randint(0, len(cluster_remain_cores_copy)-1)
                if cluster_remain_cores_copy[selected_cluster_id] != 0:
                    selected_cluster_ids.append(selected_cluster_id)
                    total_core_num += cluster_remain_cores_copy[selected_cluster_id]
                    cluster_remain_cores_copy[selected_cluster_id] = 0
                self._seed_for_kobatomo_fit += 1
            # print("selected_cluster_ids = "+str(selected_cluster_ids))
            return selected_cluster_ids
                





        


    def _calc_cluster_index(
        self,
        core_id: int,
        parameters: list[DAG|int|list]
    ) -> tuple[int, int]:
        
        cluster_remain_available = parameters[4]
        cluster_core_num = len(cluster_remain_available[0])

        cluster_id = int(core_id / cluster_core_num)  
        cluster_core_id = core_id % cluster_core_num 
        return (cluster_id, cluster_core_id)
