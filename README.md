# multi-rate_simulator

## access_dag_timer.py
DAGクラスとNODEクラスを定義している。

## access_simulator.py
スケジューリングシミュレータのコード。


## access_simulator_not_threshold.py
WCMで一ノード当たりの割り当てコア数にしきい値なし場合のシミュレータコード。　
access_simulator.pyはしきい値が与えられている。
基本的に、methods = [pro_koba, kobatomo]の評価を行わない場合にはaccess_simulator.pyを使用する。
評価コード（例えばaccess_heavy_comm_n.py）を使用する際、デフォルトでは from src.access_simulator.pyとなっているため、場合に応じてfrom src.access_simulator_not_threshold.pyに書き換える
- pro_koba: WCM (kobatomo & okamu, 2025 IEEE Access)で各ノードのコア数決定を行い、クラスタ選択は提案手法を使っている場合
- kobatomo: WCM (kobatomo & okamu, 2025 IEEE Access)で各ノードのコア数決定を行い、クラスタ選択はランダムで行っている場合


## cluster_selection.py
クラスタ選択手法（提案手法）が実装されている。

　

## access_dag_timer.py
DAGクラスとNODEクラスを定義している。




## access_heavy_comm_n.py
ヘビータスクセットのクラスタ間通信（ノード内とノード間）発生回数を求める
コード内の以下の変数：
- cluster_nums
- cluster_total_cores
- methods
を調整することで、一ファイルですべての評価を取ることも可能。逆にこれらを分割することで、複数ファイルで評価を行うことも可能。

## access_light_comm_n.py
access_heavy_comm_n.pyのアベレージタスクセット版。

## access_heavy_respo_n.py
ヘビータスクセットの応答時間を評価するコード
access_heavy_comm_n.pyを少しだけいじって作っているため、中身は似ている。異なる点は、DAGのノード数を一つに固定し、代わりにcluster_comm_ratio (クラスタ間通信一回当たりの遅延時間)を変化させながら行っている点。
こちらも
- cluster_nums
- cluster_total_cores
- methods
を修正することで調整可能。

## access_light_respo_n.py
access_heavy_respo_n.pyと同様。アベレージタスクセットの応答時間を評価するコード。

## Timer_DAG/
評価に使用したDAGが入っている

## autoware_dag
readme参照

## master
readme参照



　