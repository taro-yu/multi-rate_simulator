from src.yaml_dag_reader import YamlDagReader
# from json_exporter import JsonExporter
# from display_okamu import display_scheduling

from src.access_dag_timer import DAG

# from src.access_simulator import Simulator
from src.access_simulator_not_threshold import Simulator
import random


import os
import networkx

# read node, edge, deadline from yaml
a = 0
dag_num = 200
frag = 0
firstR_list = []
R_list = []
total = []
intra_cc_cost = []
inter_cc_cost = []
intra_core_num = []
intra_comm_occur_num = []
response_times = []
max_response_times = []
success_flags = []
success_ratios = []
# methods = ['EFT']
# methods = ['proposed', 'best', 'greedy', 'EFT']

# methods = ['proposed']
# methods = ['best']
# # methods = ['greedy']
# methods = ['proposed', 'best']

methods = ['kobatomo', 'pro_koba']
# methods = ['pro_koba']
# methods = ['kobatomo']

deadline_ratios = [0.5, 0.6, 0.7, 0.8]
cc_time_ratio = 1.0
sp_node_id = 0

# seed = random.randint(0, 100000)
seed = 0


# for type in types:
#     if type == 'proposed':
#         from ecrts_proposed import Scheduler2
#     elif type == 'worst':
#          from ecrts_worst import Scheduler2
#     elif type == 'best':
#         from ecrts_best import Scheduler2
#     else:
#         from ecrts_EFT import Scheduler2
# for deadline_ratio in range(0, 11, 1):
# for deadline_ratio in deadline_ratios:


deadline_ratio = 0.5
cluster_nums = [5]
cluster_total_cores = [80, 120, 160]

for method_name in methods:
    #クラスタ数とトータルコア数を固定
    with open(f'result/access_respo_light_{method_name}_5.txt', 'w') as f:
    # with open(f'result/test', 'w') as f:
    # with open(f'result/access_respo_light_{method_name}_not_5.txt', 'w') as f:
        for cluster_num in cluster_nums:
            for cluster_total_core in cluster_total_cores:
                # cluster_num = 5
                # cluster_total_core = 80
                cluster_core_num = cluster_total_core // cluster_num
                ave_list_intra = [] 
                ave_list_inter = [] 
                success_flags = []
                ave_list_respo = []
                max_response_times = []
                ave_success_ratio = []
                for cluster_comm_ratio in range(1, 51, 1):
                # for cluster_comm_ratio in range(1, 2, 1):
                    cluster_comm_ratio *= 0.1
                    for n in range(dag_num):
                        # print(n)
                        print("\rlight_respo: evaluated "+str(method_name)+" cluster_comm_ration : "+str(cluster_comm_ratio)+" DAG, cluster_num="+str(cluster_num)+", total_core="+str(cluster_total_core)+", task num="+str(n)+ "  ",end="")
                        # n=21
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        reader = YamlDagReader(current_dir+"/Timer_DAG/DAG80/dag_"+str(n)+".yaml")

                        wcets, edges, deadline, k_parallel, index, periods, seeds = reader.read()

                        # make dag from wcets, edges, deadline
                        dag = DAG(wcets, edges, deadline, k_parallel, index, periods, seeds)

                        seed += 1
                        # do list scheduling
                        core_num = 1
                        # cluster_num = 5
                        # cluster_core_num = 16
                        # deadline_ratio = 0.8
                        simulator = Simulator(dag, cluster_num, cluster_core_num, cluster_comm_ratio, method_name, seed=seed)
                        ave_response_time = simulator.Scheduling(task_name="light")

                        # scheduler = Scheduler2(dag, cluster_num, cluster_core_num, sp_node_id, deadline_ratio, cc_time_ratio, heavy_task_num=4, consider_compute_core=True)
                        # ave_response_time = scheduler.Scheduling(n, task_name="heavy")
                        # if scheduler._Frag is True:
                        #     frag += 1
                        # else:
                        #     print("dag_number = "+str(n))
                        # R_list.append(ave_response_time)

                        #今回は率を計算するため、トータルの回数で割っている
                        # print(scheduler._total_comm_within_node)
                        # print(scheduler._total_intra_cc_cost)
                        # print(scheduler._total_comm_between_node)
                        # print(scheduler._total_inter_cc_cost)
                        # print("#")
                        # print("total_intra_cc_cost = "+str(scheduler._total_intra_cc_cost))
                        if simulator._total_intra_cc_cost == 0:
                            pass
                        else:
                            intra_cc_cost.append(simulator._total_intra_cc_cost)
                        inter_cc_cost.append(simulator._total_inter_cc_cost)
                        
                        
                        if len(simulator._intra_core_num) == 0:
                            pass
                        else:
                            intra_core_num.append(sum(simulator._intra_core_num) / len(simulator._intra_core_num))
                           
                            # 一ジョブが複数クラスタからの確保を行った回数
                            intra_comm_occur_num.append(len(simulator._intra_core_num))
                        max_respo = max(simulator._response_times)
                        response_times.append(max_respo)
                        # print(simulator._response_times)


                    # success_ratio = sum(success_flags)/dag_num
                    # ave_list_intra.append(sum(intra_cc_cost) / dag_num)
                    # ave_list_inter.append(sum(inter_cc_cost) / dag_num)
                    ave_list_respo.append(sum(response_times) / dag_num)
                    max_response_times.append(max(response_times))
                    # ave_list_intra.append(sum(intra_cc_cost))
                    # ave_list_inter.append(sum(inter_cc_cost))
                    # ave_success_ratio.append((sum(success_flags) / dag_num))
                    # print("response_time_list = "+str(R_list))
                    # print("response_time_avw = "+str(sum(R_list)/len(R_list)))
                    print("\n")
                    # print("total_inter_comm_ave = "+str(sum(inter_cc_cost) / dag_num))
                    # print("total_intra_comm_ave = "+str(sum(intra_cc_cost) / len(intra_cc_cost)))
                    # print("average_intra_comm = "+str(sum(intra_core_num) / len(intra_core_num)))
                    # # print("intra_comm_occur_num = "+ str(intra_comm_occur_num))
                    # print("average_intra_comm_occur_num = "+ str(sum(intra_comm_occur_num)/ len(intra_comm_occur_num)))
                    # print("max_respo_ave = "+str(sum(response_times) / len(response_times)))
                    # print("response_times = "+str(response_times))
                    # print("max_respo = "+str(max_response_times))

                    # print("total_inter_comm = "+str(inter_cc_cost))
                    # print("total_intra_comm = "+str(intra_cc_cost))
                    # print("len(intra_cc_cost) = "+str(len(intra_cc_cost)))
                    # print("len(intra_core_num) = "+str(len(intra_core_num)))
                    # print("average_intra_comm_num = "+str(intra_core_num))


                    intra_cc_cost = []
                    inter_cc_cost = []
                    intra_core_num = []
                    intra_comm_occur_num = []
                    R_list = []
                    success_flags = []
                    response_times = []
                    print("\n")

                # f.write(f"test_result_4_{method}_light_false_{cluster_num}_{cluster_core_num}_intra={ave_list_intra}\n")
                # f.write(f"test_result_4_{method}_light_false_{cluster_num}_{cluster_core_num}_inter={ave_list_inter}\n")
                # f.write(f"test_result_4_{method}_light_false_{cluster_num}_{cluster_core_num}_success_ratio={ave_list_respo}\n\n")
                f.write(f"respo_{method_name}_light_{cluster_num}_{cluster_core_num}_respo_ave={ave_list_respo}\n")
                # f.write(f"respo_{method_name}_light_{cluster_num}_{cluster_core_num}_not_respo_ave={ave_list_respo}\n")
                # f.write(f"respo_{method_name}_light_{cluster_num}_{cluster_core_num}_max_respo={max_response_times}\n\n")

