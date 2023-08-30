from sim.Logger import *
from sim.SubstrateSelector import *
from sim.Simulator import *

import copy
import time
import simpy
import networkx as nx
import random
import logging



class Simulator():
    def __init__(self, substrate, folder_log, logLevel, logCSV, *arg):
        self.env = simpy.Environment()
        self.logger = Logger(self, folder_log, logCSV)

        logging.basicConfig(level=logLevel, format="%(message)s")
        self.strategy = arg[0] # 1 is not remap, 2 is remap

        if(len(arg) == 2): self.sortmode = arg[1]

        self.topology = copy.deepcopy(substrate.topology)
        self.DataCentres = copy.deepcopy(substrate.DCs)
        self.Ingresses = copy.deepcopy(substrate.Ingresses)

        # self.selectorLog = []

        self.capacity = 0 # sum of all Server's capacity
        for DC in self.DataCentres:
            for node in list(DC.topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    self.capacity += node[1]["capacity"]

        self.reqQueue = simpy.Store(self.env)

        self.SFCcounter = 0 # for numbering SFC in Ingress.py

        self.SFCs = []
        self.runningSFCs = []
        self.stat = {
            "accepted": [], # list of id
            "failed": [], # list of id
            "acceptedVNFs": 0,
            "failedVNFs": 0,
            "runtime": 0
        }

        self.util = 0
        self.power = 0
        self.activeServer = 0

        self.migration = 0
        self.justRemove = -1



    def prehandler(self):
        while True:
            sfc = yield self.reqQueue.get()
            # logging.debug(f"get sfc-{sfc['id']}")

            if(self.strategy == 1):
                self.handler(sfc, rehandler=False)
            if(self.strategy == 2):
                backupRunningSFCs = self.runningSFCs

                self.logger.log_event(self, self.logger.REMAP_START)
                try:
                    # stop all running SFCs
                    for aliveSFC in self.runningSFCs:
                        aliveSFC["event"].interrupt()
                        yield self.env.timeout(0)

                    # reset all DC and substrate
                    for DC in self.DataCentres:
                        DC.reset()
                    for outlink in list(self.topology.edges.data()):
                        outlink[2]["usage"] = 0

                    _runningSFCs = backupRunningSFCs

                    ##### remap procedure
                    if(_runningSFCs != []):
                        lastSFC = _runningSFCs[-1]
                        if self.sortmode == "d":
                            _runningSFCs.sort(reverse=True, key=lambda e : len(e["sfc"]["struct"].nodes))
                        if self.sortmode == "i":
                            _runningSFCs.sort(reverse=False, key=lambda e : len(e["sfc"]["struct"].nodes))
                        
                        for e in _runningSFCs:
                            if(e["sfc"]["id"] == lastSFC["sfc"]["id"]):
                                index = _runningSFCs.index(e)
                                break

                        if(self.justRemove != -1):
                            logging.debug(f"\n----------just remove {self.justRemove}----------\n")
                            if index > self.justRemove:
                                index = self.justRemove
                            self.justRemove = -1

                        sortedSFCs = _runningSFCs[:index]
                        remapSFCs = _runningSFCs[index:]
                        self.runningSFCs = []
                        for e in sortedSFCs:
                            logging.debug(f"redeploy SFC-{e['sfc']['id']} using backup")
                            [DC for DC in self.DataCentres if DC.id == e['sfc']["DataCentre"]][0].deployer(e['sfc'], self, True)
                        for e in remapSFCs:
                            self.handler(e["sfc"], rehandler=True)
                    ####################

                    ##### old remap method
                    # if(self.sortmode == 'd'):
                    #     _runningSFCs.sort(reverse=True, key=lambda e : len(e["sfc"]["struct"].nodes))
                    # if(self.sortmode == 'i'):
                    #     _runningSFCs.sort(reverse=False, key=lambda e : len(e["sfc"]["struct"].nodes))
                    # self.runningSFCs = []
                    # for e in _runningSFCs: # redeploy
                    #     self.handler(e["sfc"], True)
                    #####

                    self.logger.log_event(self, self.logger.REMAP_SUCCESS)
                    self.handler(sfc, False)
                except:
                    logging.debug(f"\n{self.time()}:-----remap failed, turn back previous status-----\n")

                    for aliveSFC in self.runningSFCs:
                        aliveSFC["event"].interrupt()
                        yield self.env.timeout(0)
                    
                    for DC in self.DataCentres:
                        DC.reset()
                    for outlink in list(self.topology.edges.data()):
                        outlink[2]["usage"] = 0

                    _runningSFCs = backupRunningSFCs
                    self.runningSFCs = []

                    for e in _runningSFCs:
                        logging.debug(f"deploy SFC-{e['sfc']['id']} using backup")
                        [DC for DC in self.DataCentres if DC.id == e['sfc']["DataCentre"]][0].deployer(e['sfc'], self, redeploy=True)
                    self.logger.log_event(self, self.logger.REMAP_FAIL)
                    self.handler(sfc, rehandler=False)

                    

    def handler(self, sfc, rehandler):
        failed, failDetail, decision = sfc["app"].subSelector.analyse(self, sfc)

        if(failed == len(self.DataCentres)):
            sfc["failDetail"] = failDetail
            if((sfc["id"] in self.stat["accepted"])):
                logging.warning("ERROR: droped a accepted SFC")
                exit()
            if((not sfc["id"] in self.stat["failed"])):
                self.stat["failed"].append(sfc["id"])
                self.stat["failedVNFs"] += len(sfc["struct"].nodes)
            self.logger.log_event(self, self.logger.DROP, sfc)
        else:
            if(not sfc["id"] in self.stat["accepted"]):
                self.stat["accepted"].append(sfc["id"])
                self.stat["acceptedVNFs"] += len(sfc["struct"].nodes)
            [DC for DC in self.DataCentres if DC.id == decision['DataCentre']][0].deployer(decision, self, redeploy=rehandler)
        


    def cal_power(self):
        self.power = 0
        for DC in self.DataCentres:
            self.power += DC.power
        return self.power



    def cal_active_server(self):
        self.activeServer = 0
        for DC in self.DataCentres:
            self.activeServer += len(DC.activeServer)
        return self.activeServer



    def time(self): # return time
        return self.env.now # minutes
        return f"{self.env.now//60}h{self.env.now%60:2d}m:" # format 2h43m
        


    def run(self, runtime):
        for ingress in self.Ingresses:
            ingress.generator(self)

        self.env.process(self.prehandler())
        startTime = int(time.time())
        self.env.run(until=runtime)
        endTime = int(time.time())
        self.logger.close()

        total = len(self.SFCs)
        accepted = len(self.stat['accepted'])
        failed = len(self.stat['failed'])
        acceptance = round(accepted / total * 100, 1)

        acceptedVNFs = self.stat["acceptedVNFs"]
        failedVNFs = self.stat["failedVNFs"]
        totalVNFs = acceptedVNFs + failedVNFs
        acceptanceVNFs = round(acceptedVNFs / totalVNFs * 100, 1)

        self.stat["runtime"] = int(endTime - startTime)

        logging.info(f"accepted: {accepted} / {total} SFCs ({acceptance}%)")
        logging.info(f"failed: {failed} SFCs")
        logging.info(f"accepted VNFs: {acceptedVNFs} / {totalVNFs} VNFs ({acceptanceVNFs}%)")
        logging.info(f"failed VNFs: {failedVNFs} VNFs")
        logging.info(f"migration: {self.migration} times")
        logging.info(f"Simulator time: {(endTime - startTime) // 60}m{(endTime - startTime) % 60}s")

        return self.stat
