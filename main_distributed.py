from sim.Simulator import *
from sim.Application import *
from sim.Distribution import *
from sim.Selector import *
from sim.DataCentre import *
from sim.Ingress import *
from sim.Substrate import *
from sim.SubstrateSelector import *
from library import *

from pathlib import Path
import sys
import json
import random
import logging



def main_distributed(randomSeed, appArgs, runtime, argument, DCPos, IngressPos):
    np.random.seed(randomSeed)
    random.seed(randomSeed)


    # selector = WaxmanSelector()
    # selector = VNFG()
    # selector = ONP_SFO(15)
    # selector = MIX_ver2(30)
    selector = HRE_ver2()


    subSelector = ShortestPath()
    # subSelector = AlphaSubsel()
    # subSelector = BetaSubsel()


    # app = SequenceApp(dist, selector, subSelector, *appArgs)
    app = WaxmanApp(dist, selector, subSelector, *appArgs)
    apps = [app]



    # origin
    # substrate = Abilene(DCPos=[1, 4, 6, 11], IngressPos=[5, 7, 9, 10], linkCap=100,
    #                     DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)


    # best
    # substrate = Abilene(DCPos=[1, 2, 4, 8], IngressPos=[5, 7, 9, 10], linkCap=100,
                        # DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)


    # substrate = Abilene(DCPos=[6, 9, 10, 12], IngressPos=IngressPos, linkCap=100,
    #                     DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)
    # substrate = Europe(DCPos=[], IngressPos=[5, 7, 9, 10], linkCap=100,
    #                     DCArgs=[], IngressArgs=[apps, apps, apps, apps], n_clusters=4)
    # substrate = Atlanta(DCPos=[], IngressPos=[5, 7, 9, 10], linkCap=100,
    #                     DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=4)
    # substrate = France(DCPos=[], IngressPos=[5, 7, 9, 10], linkCap=100,
    #                     DCArgs=[10], IngressArgs=[apps, apps, apps, apps], n_clusters=4)


    substrate = Abilene(DCPos=DCPos, IngressPos=IngressPos, linkCap=100,
                        DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)
    # substrate = BigAbilene(DCPos=DCPos, IngressPos=IngressPos, linkCap=100,
    #                     DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)
    # substrate = Europe(DCPos=DCPos, IngressPos=IngressPos, linkCap=100,
    #                     DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)
    # substrate = France(DCPos=DCPos, IngressPos=IngressPos, linkCap=100,
    #                     DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)
    # substrate = Atlanta(DCPos=DCPos, IngressPos=IngressPos, linkCap=100,
    #                     DCArgs=[4, 6, 6, 8], IngressArgs=[apps, apps, apps, apps], n_clusters=0)


    ######################################## folder name
    # spec = f"{n_VNFs[0]}{n_VNFs[1]}_{demand_VNF[0]}{demand_VNF[1]}_{bw[0]}{bw[1]}_{runtime}"
    spec = f"{DCPos[0]}{DCPos[1]}{DCPos[2]}{DCPos[3]}/{IngressPos[0]}{IngressPos[1]}{IngressPos[2]}{IngressPos[3]}"
    folder_result = f"{selector.name}/dist/{spec}"
    ########################################

    folder_log = Path(f"results/{folder_result}")
    folder_log.mkdir(parents=True, exist_ok=True)
    folder_log = str(folder_log) + "/dist_"
    if(len(argument) == 1):
        folder_log = str(folder_log) + f"{argument[0]}"
    if(len(argument) == 2):
        folder_log = str(folder_log) + f"{argument[0]}{argument[1]}"

    sim = Simulator(substrate, folder_log, logging.DEBUG, True, *argument)
    sim.run(runtime)

    logging.warning("DISTRIBUTED")
    logging.warning(f"L = {dist.lamda}, TTL = {avg_TTL}")
    logging.warning(f"nvnf = {n_VNFs}, bw = {bw}")
    logging.warning(f"runtime = {runtime}, strategy = {argument[0]}")
    logging.warning(f"randomSeed = {randomSeed}")
    if(len(argument) == 2):
        logging.warning(f"sortmode = {argument[1]}")



if __name__ == "__main__":
    print("-----START SIMULATION-----")
    strategy = int(sys.argv[1])
    if(len(sys.argv) == 3):
        sortmode = sys.argv[2]
        arg = [strategy, sortmode]
    else:
        arg = [strategy]

    randomSeed = 1111

    dist = Poisson(lamda=2)
    avg_TTL = 120
    n_VNFs = [4, 10]
    demand_VNF = [15, 30]
    bw = [10, 90]
    runtime = 200
    appArgs = [avg_TTL, n_VNFs, demand_VNF, bw, [0.5, 0.5]]

    # run one case
    main_distributed(randomSeed=randomSeed, appArgs=appArgs, runtime=runtime, argument=arg, DCPos=[1, 4, 6, 11], IngressPos=[5, 7, 9, 10])

    # brute force
    # # N_NODES = 12 # Abilene
    # # N_NODES = 39 # BigAbilene
    # # N_NODES = 37 # Europe
    # N_NODES = 25 # France
    # # N_NODES = 15 # Atlanta
    # BUFFER = 230
    # IGR_PER_DC_CASE = 500
    # nodes = list(range(1, N_NODES + 1))
    # shell = int(sys.argv[2])
    # DCPos = list(itertools.combinations(nodes, 4))
    # dcCount = BUFFER * (shell-1)
    # for _dcpos in DCPos[BUFFER*(shell-1) : BUFFER*shell]:
    #     dcCount += 1
    #     ingressSpace = [node for node in nodes if not node in _dcpos]
    #     ingressPos = list(itertools.combinations(ingressSpace, 4))
    #     ingCount = 0
    #     for i in range(1, IGR_PER_DC_CASE + 1):
    #         ingCount += 1
    #         print(f"DC: {dcCount}/{len(DCPos)} ({round(dcCount % BUFFER / BUFFER * 100, )}%), Ingress: {ingCount}/{IGR_PER_DC_CASE}")
    #         main_distributed(randomSeed, appArgs, runtime, arg, list(_dcpos), list(ingressPos[random.randint(0, len(ingressPos) + 1)]))
    #     # for _ingpos in ingressPos:
    #     #     ingCount += 1
    #     #     print(f"DC: {dcCount}/{len(DCPos)} ({round(dcCount % BUFFER / BUFFER * 100, )}%), Ingress: {ingCount}/{len(ingressPos)}")
    #     #     main_distributed(randomSeed, appArgs, runtime, arg, list(_dcpos), list(_ingpos))
