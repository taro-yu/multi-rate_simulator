class ClusterSlectionMethod():
    
    def __init__(
            self,
            require_core_num: int,
            cluster_remain_cores: list,
            cluster_remain_available: list,
    ):
        self._require_core_num = require_core_num
        self._cluster_remain_cores = cluster_remain_cores
        self._cluster_remain_available = cluster_remain_available 

    # クラスタ選択と、割り当てを、一つの関数内で行う
    def selection_method(
           self,
           method_name: str #proposed, greedy, best, EFT
    ) -> list[int]:
        if method_name == 'proposed':
            return porposed_cluster_selection_method()
        elif method_name == 'greedy':
            return greedy_fit()
        elif method_name == 'best':
            return best_fit()
        else:
            return EFT()
    


    def _pred_fit(
        self,

    ):
        pass

    def _EFT(
        self,

    ):

