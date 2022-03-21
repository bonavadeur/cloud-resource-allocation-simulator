from sim.Simulator import *
from sim.Application import *
from sim.SFC import *
from sim.Distribution import *
from sim.Selector import *
from sim.DataCentre import *
from sim.Ingress import *
from library import *

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import sys
import json
import random



def main(argument):
    np.random.seed(2405)
    random.seed(2405)

    switchSpecs = {
        "basePower": 39,
        "portPower": [0.42, 0.48, 0.9]
    }
    serverCapacity = 4
    serverSpecs = {
        "capacity": serverCapacity,
        "usage": 0,
        # "power": [205.1, 232.9, 260.7, 288.6, 316.4]
        "power": [0, 232.9, 260.7, 288.6, 316.4]
    }

    ############################################################ CONFIG HERE
    dist = Poisson(lamda=10)
    avg_TTL = 30
    n_VNFs_range = [10, 20]
    bw_range = [10, 150]
    runtime = 60
    arg = [avg_TTL, n_VNFs_range, bw_range, [0.5, 0.5]]
    ########################################################################

    selector = WaxmanSelector()
    app = WaxmanApp("WaxmanApp", dist, selector, *arg)
    # selector = VNFFG_node_splitting()
    # app = VNFGApp("VNFGApp", dist, selector, *arg)

    apps = [app]

    folder_result = f"{serverCapacity}_{dist.lamda}_{avg_TTL}_{n_VNFs_range[0]}{n_VNFs_range[1]}_{bw_range[0]}{bw_range[1]}_{runtime}"
    folder_log = Path(f"results/{folder_result}/{apps[0].name}")
    folder_log.mkdir(parents=True, exist_ok=True)
    folder_log = str(folder_log) + "/cent_"
    if(len(argument) == 1):
        folder_log = str(folder_log) + f"{argument[0]}"
    if(len(argument) == 2):
        folder_log = str(folder_log) + f"{argument[0]}{argument[1]}"

    # big topo
    topology = DistributedTopo()
    DCs = []
    DCs.append(DataCentre(2, fat_tree(10, switchSpecs, serverSpecs)))
    Ingresses = []
    Ingresses.append(Ingress(5, apps))
    Ingresses.append(Ingress(7, apps))
    Ingresses.append(Ingress(9, apps))
    Ingresses.append(Ingress(10, apps))

    sim = Simulator(topology, DCs, Ingresses, folder_log, *argument)
    sim.run(runtime) # runtime = 120 minutes
    print("CENTRALIZED")
    print(f"ram = {serverCapacity}, L = {dist.lamda}, TTL = {avg_TTL}")
    print(f"nvnf = {n_VNFs_range}, bw = {bw_range}")
    print(f"runtime = {runtime}, strategy = {argument[0]}")
    if(len(argument) == 2):
        print(f"sortmode = {argument[1]}")


if __name__ == "__main__":
    print("-----START SIMULATION-----")
    strategy = int(sys.argv[1])
    if(len(sys.argv) == 3):
        sortmode = sys.argv[2]
        arg = [strategy, sortmode]
    else:
        arg = [strategy]

    main(arg)