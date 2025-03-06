
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