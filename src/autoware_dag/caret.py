import numpy as np
import os
import glob
from collections import defaultdict

# ディレクトリを指定
current_dir = os.path.dirname(os.path.abspath(__file__))
npy_dir = current_dir+"/merged_latencies"
# npyファイルのパスを取得
file_paths = glob.glob(os.path.join(npy_dir, "*.npy"))


# コールバックごとの最大値を保存する辞書
callback_max_times = defaultdict(float)

np.set_printoptions(threshold=np.inf)

array = np.load('/home/yutaro/wd/multi-rate_simulator/merged_latencies/-system-topic_state_monitor_scenario_planning_trajectory-callback_1.npy')
max = array.max()
print(max)

# for file_path in file_paths:
#     # ファイル名の取得
#     file_name = os.path.basename(file_path)
    
#     # コールバック名を取得（最後の "_callback_数字.npy" を除去）
#     callback_name = "_".join(file_name.split("_callback_")[:-1]) + "_callback"
    
#     # npyファイルを読み込む
#     execution_times = np.load(file_path)
    
#     # 最大値を取得
#     max_time = np.max(execution_times)
    
#     # すでにある最大値と比較して更新
#     callback_max_times[callback_name] = max(callback_max_times[callback_name], max_time)

# # 結果を表示
# for callback, max_time in sorted(callback_max_times.items()):
#     print(f"{callback}: {max_time}")
