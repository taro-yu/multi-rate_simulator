#!/bin/bash

# スクリプトのリスト
scripts=(
    "access_light_comm_5.py"
    "access_light_comm_8.py"
    "access_light_comm_10.py"
    "access_light_comm_20.py"
    "access_heavy_comm_5.py"
    "access_heavy_comm_8.py"
    "access_heavy_comm_10.py"
    "access_heavy_comm_20.py"
)

# それぞれのスクリプトを新しいターミナルで実行
for script in "${scripts[@]}"; do
    python3 "$script" &
done