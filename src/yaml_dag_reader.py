import yaml

class YamlDagReader:
    def __init__(self, file_path):
        with open(file_path, 'r') as yml:
            self.dict = yaml.safe_load(yml)

    def read(self) -> tuple([[int], [(int, int)], int, [int], [int]]):
        nodes_yaml = self.dict["nodes"]
        #WCETをyamlファイルから取ってくる
        wcets = [n["execution_time"] for n in sorted(nodes_yaml, key=lambda x: x["id"])]

        #並列度 "k" をymalファイルから取ってくる
        k_parallel = [n["k"] for n in sorted(nodes_yaml, key=lambda x: x["id"])]

        index = [n["id"] for n in sorted(nodes_yaml, key=lambda x: x["id"])]

        periods = [n["Period"]*10 for n in sorted(nodes_yaml, key=lambda x: x["id"])]

        # deadlineを取ってくる
        for n in nodes_yaml:
            if "end_to_end_deadline" in n:
                deadline = n["end_to_end_deadline"]

        edge_yaml = self.dict["links"]
        # edges = [(0,1),(0,2),(0,3),(1,5),(1,6),(2,4),(3,7),(4,7),(4,8),(5,9),(6,10),(7,10),(8,10),(8,11),(9,11),(10,11)]
        edges = [(e["source"], e["target"]) for e in edge_yaml]

        #ノードが持つ複数の実行時間
        # ex_times = [[n["ex1"], n["ex2"], n["ex3"], n["ex4"], n["ex5"]] for n in sorted(nodes_yaml, key=lambda x: x["id"])]

        #seed値の取得
        seeds = [n["seed"] for n in sorted(nodes_yaml, key=lambda x: x["id"])]

        return wcets, edges, deadline, k_parallel, index, periods, seeds
