from sim.Simulator import *
from sim.Application import *
from sim.Distribution import *
from sim.Selector import *
from sim.DataCentre import *
from sim.Ingress import *
from sim.Substrate import *
from library import *
from threading import Thread
from pathlib import Path

import threading
import numpy as np
import matplotlib.pyplot as plt
import random
import logging



def main_distributed(randomSeed, appArgs, runtime, argument, results, index):
    np.random.seed(randomSeed)
    random.seed(randomSeed)

    selector = WaxmanSelector_0()
    # selector = VNFG()
    # selector = ONP_SFO(k_sub = 15)
    app = WaxmanApp(dist, selector, *appArgs)
    apps = [app]

    substrate = Abilene(DCPos=[1, 4, 6, 11], IngressPos=[5, 7, 9, 10], 
                        linkCap=100,
                        DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps])

    # folder name
    spec = f"{n_VNFs[0]}{n_VNFs[1]}_{demand_VNF[0]}{demand_VNF[1]}_{bw[0]}{bw[1]}_{runtime}"
    folder_result = f"{selector.name}/{spec}_seed{randomSeed}"

    folder_log = Path(f"results/{folder_result}")
    folder_log.mkdir(parents=True, exist_ok=True)
    folder_log = str(folder_log) + "/dist_"
    if(len(argument) == 1):
        folder_log = str(folder_log) + f"{argument[0]}"
    if(len(argument) == 2):
        folder_log = str(folder_log) + f"{argument[0]}{argument[1]}"

    sim = Simulator(substrate, folder_log, logging.WARNING, *argument)
    result = sim.run(runtime)
    results[index] = result


def main_centralized(randomSeed, appArgs, runtime, argument, results, index):
    np.random.seed(randomSeed)
    random.seed(randomSeed)

    selector = WaxmanSelector()
    # selector = VNFG()
    # selector = ONP_SFO(15)
    app = WaxmanApp(dist, selector, *appArgs)
    apps = [app]

    substrate = Abilene(DCPos=[2], IngressPos=[5, 7, 9, 10], 
                        linkCap=100,
                        DCArgs=[10], IngressArgs=[apps, apps, apps, apps])

    # folder name
    spec = f"{n_VNFs[0]}{n_VNFs[1]}_{demand_VNF[0]}{demand_VNF[1]}_{bw[0]}{bw[1]}_{runtime}"
    folder_result = f"{selector.name}/{spec}_seed{randomSeed}"

    folder_log = Path(f"results/{folder_result}")
    folder_log.mkdir(parents=True, exist_ok=True)
    folder_log = str(folder_log) + "/cent_"
    if(len(argument) == 1):
        folder_log = str(folder_log) + f"{argument[0]}"
    if(len(argument) == 2):
        folder_log = str(folder_log) + f"{argument[0]}{argument[1]}"

    sim = Simulator(substrate, folder_log, logging.WARNING, *argument)
    result = sim.run(runtime)
    results[index] = result


if __name__ == "__main__":
    print("-----START SIMULATION-----")

    dist = Poisson(lamda=2)
    avg_TTL = 120
    n_VNFs = [4, 20]
    demand_VNF = [25, 25]
    bw = [10, 50]
    runtime = 60
    appArgs = [avg_TTL, n_VNFs, demand_VNF, bw, [0.5, 0.5]]

    threads = []
    results_dist1 = []
    results_dist2d = []

    case = 6
    for i in range(0, case):
        t = threading.Thread(target=main_distributed,
            args=(i, appArgs, runtime, [1], results_dist1, len(results_dist1),),
            daemon=True)
        threads.append(t)
        results_dist1.append([])

        t = threading.Thread(target=main_distributed,
            args=(i, appArgs, runtime, [2, "d"], results_dist2d, len(results_dist2d),),
            daemon=True)
        threads.append(t)
        results_dist2d.append([])
    
    n_threads = len(threads)
    block = 4
    i = 0
    while i < n_threads:
        if i + block <= n_threads: 
            for j in range(0, block):
                print(f"processing thread {i + j + 1}/{n_threads}")
                threads[i + j].start()
            for j in range(0, block):
                threads[i + j].join()
            i += block
        else:
            a = n_threads - i
            for j in range(0, a):
                threads[i + j].start()
            for j in range(0, a):
                threads[i + j].join()
            break
    print(results_dist1)
    print(results_dist2d)
    