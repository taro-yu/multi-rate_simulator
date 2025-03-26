# 基本的に使用するファイル
## シミュレーション関係
- acceess_simulator.py
    - 各ノードの要求コア数を決定し、実際にシミュレーションを行うファイル
- acceess_simulator_not_threshod.py
    - IEEE Accessの査読対応用に作成したファイル。内容はacceess_simulator.pyのコピペ
    - 異なる部分は、追加評価(batomo IEEE Access) において一ノード当たりの割り当て制を無くしていること (scheduling関数の内容のみ異なる)
- access_dag_timer.py
    - DAGとNodeをクラスとして定義している
- cluster_selection.py
    - 提案手法（クラスタ選択手法)を定義している

## 評価関係
- access_light_comm_n.py
    - averageタスクセットのクラスタ間通信の回数を評価するコード
    - 論文ではaverageタスクセットとなっているが、コードではlightとしている
    - nの部分はクラスタ数を表しているが、一つのファイルで12パターンすべて評価することも可能
    - クラスタ構造のほかに、DAGのノード数を変化させて評価している

- access_heavy_comm.py
    - heavyタスクセットのクラスタ間通信の回数を評価するコード
    - lightと違う点は、ノード数を固定していて（現在は80）、heavyタスクの数を変化させて評価している
- access_light_respo.py
    - averageタスクセットの応答時間を評価するコード
    - ノード数を80に固定して、cc_cost（一回当たりのクラスタ間通信の値）を0.1~5.0まで0.1刻みで変化させて評価している
- access_heavy_respo.py
    - lightと違う点は、ノード数80だけでなく、ヘビータスクの数を固定（今回は4）にして評価をしている


## 図の作成関係
- IEEE_light_plot_2.ipynb
    - アベレージタスクセットのplotコード
    - 2がついてない同名のファイルがあるが、IEEE Accessの査読前に使用していたやつでほぼ内容は一緒だが、データ保管のために取ってある。基本は2の付く法を使用

- IEEE_heavy_plot_2.ipynb
    - lightと同様
