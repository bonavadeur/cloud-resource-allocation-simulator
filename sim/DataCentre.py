from sre_constants import JUMP
import simpy
import copy
import json
import networkx as nx



class DataCentre():
    def __init__(self, id, topo):
        self.id = id
        self.topo = topo

        self.activeServer = [] # list of id
        self.power = 0



    def create_pipe(self, sim):
        self.considerPipe = simpy.Store(sim.env)



    def consider(self, sim, sfc):
        anaRes = sfc["app"].selector.analyse(self, sfc) # analyse result
        if(not anaRes in [1, 2]): # 1 is not enough bandwidth, 2 is not enough capacity
            topo = self.fakeDeploy(anaRes)
            power = self.energy(topo)

            _util = sum([node[1]["usage"] for node in list(self.topo.nodes.data()) if node[1]["model"] == "server"])
            _bwCap = sum([edge[2]["capacity"] - edge[2]["usage"] for edge in list(self.topo.edges.data())])
            weight = _util * _bwCap
            
            considerRes = {
                "sfc": anaRes,
                "deltaPower": round(power - self.power, 1),
                "weight": weight,
                "util": _util
            }
        else:
            considerRes = anaRes
        return considerRes



    def deployer(self, sfc, sim, redeploy):
        self.topo = self.fakeDeploy(sfc)
        self.power = self.energy(self.topo)
        outroute = sfc["outroute"]
        for i in range(len(outroute) - 1):
            sim.topology.edges[outroute[i], outroute[i+1]]["usage"] += sfc["outlink"]

        self.cal_active_server()
        
        sim.runningSFCs.append({
            "sfc": sfc,
            "event": sim.env.process(self.release(sfc, sim))
        })

        sim.util += sfc["demand"]
        
        if(redeploy):
            sim.logger.log_event(sim, sim.logger.REDEPLOY, SFC=sfc)
        else:
            sim.logger.log_event(sim, sim.logger.DEPLOY, SFC=sfc)



    def release(self, sfc, sim):
        try:
            start = sim.env.now
            yield sim.env.timeout(sfc["remain"])
            sim.util -= sfc["demand"]
            sfc["remain"] = 0

            sfcTopo = sfc["struct"]
            for vnf in list(sfcTopo.nodes.data()): # release computing resource
                onServer = vnf[1]["server"]
                self.topo.nodes[onServer]["usage"] -= sfcTopo.nodes[vnf[0]]["demand"]
                self.topo.nodes[onServer]['deployed'].remove([sfc["id"], vnf[0]])

            self.cal_active_server()

            for vLink in list(sfcTopo.edges.data()): # release link
                route = vLink[2]['route']
                for i in range(len(route) - 1):
                    self.topo.edges[route[i], route[i+1]]["usage"] -= vLink[2]["demand"]

                    # consider to turn off switch
                    nodeID = route[i]
                    if(self.topo.nodes[nodeID]["model"] == "switch"):
                        for neighborLink in self.topo.adj[nodeID].items():
                            if(neighborLink[1]["usage"] > 0):
                                self.topo.nodes[nodeID]["state"] = True
                            else:
                                self.topo.nodes[nodeID]["state"] = False

            for i in range(len(sfc["outroute"]) - 1): # release substrate link
                sim.topology.edges[sfc["outroute"][i], sfc["outroute"][i+1]]["usage"] -= sfc["outlink"]

            self.power = self.energy(self.topo)

            for e in sim.runningSFCs:
                if(e["sfc"]["id"] == sfc["id"]):
                    if(sim.runningSFCs.index(e) < sim.justRemove or sim.justRemove == -1):
                        sim.justRemove = sim.runningSFCs.index(e)
                    # print("remove sfc has index: ", sim.justRemove)
                    # _run = [e["sfc"]["id"] for e in sim.runningSFCs]
                    # print("runningSFCs before = ", _run)
                    sim.runningSFCs.remove(e)
                    break

            # topo = self.topo_status_json()
            sim.logger.log_event(sim, sim.logger.REMOVE, SFC=sfc)

        except simpy.Interrupt:
            sfc["remain"] -= sim.env.now - start
            sim.util -= sfc["demand"]
            # print(f"{sim.time()}: SFC-{sfc['id']} is interrupted! remain {sfc['remain']} ----->{sfc['id']}")
            sim.logger.log_event(sim, sim.logger.INTERRUPT, sfc)

        

    def reset(self):
        for node in list(self.topo.nodes.data()):
            if(node[1]["model"] == "server"):
                node[1]["deployed"] = []
                node[1]["usage"] = 0
            node[1]["state"] = False
        for link in list(self.topo.edges.data()):
            link[2]['usage'] = 0
        # self.topo = copy.deepcopy(self.freeTopo)
        self.power = 0



    def fakeDeploy(self, sfc): # anaRes is sfc after analysing
        topo = copy.deepcopy(self.topo)

        sfcTopo = sfc["struct"]
        for vnf in list(sfcTopo.nodes.data()):
            onServer = vnf[1]["server"]
            topo.nodes[onServer]["usage"] += sfcTopo.nodes[vnf[0]]["demand"]
            if(topo.nodes[onServer]["usage"] > topo.nodes[onServer]["capacity"]):
                print(f"ERROR: server {onServer} of DC-{self.id} is spilled")
                print("sfc info:")
                print(f"server: {sfc['DataCentre']}")
                for vnf in sfc["struct"]:
                    print(vnf["id"], vnf["server"], vnf["demand"])
                exit()
            topo.nodes[onServer]['deployed'].append([sfc["id"], vnf[0]])

        for vLink in list(sfcTopo.edges.data()):
            route = vLink[2]['route']
            for i in range(len(route) - 1):
                topo.edges[route[i], route[i+1]]['usage'] += vLink[2]["demand"]
                if(topo.edges[route[i], route[i+1]]['usage'] > topo.edges[route[i], route[i+1]]["capacity"]):
                    print(f"ERROR: link {route[i]}-{route[i+1]} of DC-{self.id} is spilled")
                    exit()
                
                # turn on switch
                if(topo.nodes[route[i]]["model"] == "switch"):
                    topo.nodes[route[i]]["state"] = True

        return topo



    def topo_status_json(self):
        topo = {"DC": self.id, "node": [], "link": []}
        for node in list(self.topo.nodes.data()):
            if(node[1]["model"] == "server"):
                if(node[1]["usage"] != 0):
                    topo["node"].append({"id": node[0], **node[1]})
        for plink in list(self.topo.edges.data()):
            if(plink[2]["usage"] != 0):
                topo["link"].append({"s": plink[0], "d": plink[1], **plink[2]})
        topo = json.dumps(topo)
        return topo



    def energy(self, topo): # calculate energy
        serverPower = 0
        switchPower = 0

        for node in list(topo.nodes.data()):
            if(node[1]["model"] == "server"):
                if(node[1]["usage"] != 0):
                    node[1]["state"] = True
                    serverPower += 205.1 + 1.113 * node[1]["usage"]
                else:
                    node[1]["state"] = False
                
            if(node[1]["model"] == "switch"):
                if(node[1]["state"]): # switch is online
                    switchPower += node[1]["basePower"]
                    for neighborLink in topo.adj[node[0]].items():
                        usage = neighborLink[1]["usage"]
                        if(usage <= 10):
                            switchPower += node[1]["portPower"][0]
                        if(usage > 10 and usage <= 100):
                            switchPower += node[1]["portPower"][1]
                        if(usage > 100 and usage <= 1000):
                            switchPower += node[1]["portPower"][2]
        
        return round(serverPower + switchPower, 1)

    

    def cal_active_server(self):
        for node in list(self.topo.nodes.data()):
            if(node[1]["model"] == "server"):
                if(node[1]["usage"] != 0 and (not node[0] in self.activeServer)):
                    self.activeServer.append(node[0])
                if(node[1]["usage"] == 0 and (node[0] in self.activeServer)):
                    self.activeServer.remove(node[0])
