from abc import ABC, abstractmethod
from sys import prefix

import numpy as np
import networkx as nx
import random

import copy
import logging



class Selector(ABC):
    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def analyse(self):
        pass



class SimpleSelector(Selector):
    """
    all of this class is used to test input and output of analyse()
    no useful algorithm is implemented
    """
    def __init__(self):
        super().__init__()


    def analyse(self, DC, sfc):
        topo = copy.deepcopy(DC.topo)

        def randPlacement(bin, package):
            n_bin = len(bin)
            n_package = len(package)
            arg = round(5 / 4 * pow(4 * n_bin, 2/3) + 1)
            alloc = [-1] * n_package
            for i in range(n_package):
                for _ in range(1, 20):
                    idx = np.random.randint(0, n_bin)
                    if(bin[idx] > package[i]):
                        bin[idx] -= package[i]
                        alloc[i] = idx + arg
                        break
                    return 0

            return alloc

        # alloc vnf to server
        serverCap = []
        for node in list(topo.nodes.data()):
            if(node[1]["model"] == "server"):
                serverCap.append(node[1]["capacity"] - node[1]["usage"])
        vnfCap = []
        for vnf in list(sfc["struct"].nodes.data()):
            vnfCap.append(vnf[1]["demand"])
        
        alloc = randPlacement(serverCap, vnfCap)

        if(alloc):
            for vnf in list(sfc["struct"].nodes.data()):
                c_server = alloc[vnf[0]] # the choosen server
                vnf[1]["server"] = c_server

            for vlink in list(sfc["struct"].edges.data()):
                s = sfc["struct"].nodes[vlink[0]]["server"]
                d = sfc["struct"].nodes[vlink[1]]["server"]

                _topo = copy.deepcopy(topo)
                
                v_link = sfc["struct"].edges[vlink[0], vlink[1]]
                for p_link in list(_topo.edges.data()):
                    if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                        _topo.remove_edge(p_link[0], p_link[1])
                try:
                    route = nx.shortest_path(_topo, s, d)
                    for i in range(len(route) - 1):
                        topo.edges[route[i], route[i+1]]['usage'] + v_link["demand"]
                    sfc["struct"].edges[vlink[0], vlink[1]]["route"] = route
                except:
                    logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                    sfc["struct"].edges[vlink[0], vlink[1]]["route"] = []
                    return False
            sfc["DataCentre"] = DC.id
            return copy.deepcopy(sfc)
        else:
            logging.debug("cannot alloc")
            return False




class WaxmanSelector_0(Selector):
    """
    selector algorithm for analysing SFC waxman random topo
    """
    def __init__(self):
        super().__init__()


    def analyse(self, DC, sfc):
        topo = copy.deepcopy(DC.topo)

        def fat_tree(k):
            lastCore = int((k/2)**2)
            lastAggre = int(lastCore + k**2 / 2)
            lastEdge = int(lastAggre  + k**2 / 2)
            lastServer = int(lastEdge + k**3 / 4)
            G = nx.Graph()
            for i in range(lastServer): G.add_node(i + 1)
            for pod in range(k): # create all links
                for aggre in range(int(k / 2)):
                    for i in range(int(k / 2)):
                        G.add_edge(int(lastCore+pod*k/2+aggre+1), int(2*lastCore/k*aggre+i+1))
                        G.add_edge(int(lastCore+pod*k/2+aggre+1), int(lastAggre+pod*k/2+i+1))
                        G.add_edge(int(lastAggre+pod*k/2+i+1), int(lastEdge+pod*k**2/4+k/2*i+aggre+1))
            return G

        def randPlacement(bin, package):
            # print(bin)
            # print(package)
            n_bin = len(bin)
            n_package = len(package)
            # print("n_bin = ", n_bin)
            # print("n_package = ", n_package)
            arg = round(5 / 4 * pow(4 * n_bin, 2/3) + 1)
            alloc = [-1] * n_package
            for i in range(n_package):
                for _ in range(0, 10):
                    idx = np.random.randint(0, n_bin)
                    # print(i, idx, bin[idx])
                    if(bin[idx] >= package[i]):
                        bin[idx] -= package[i]
                        alloc[i] = idx + arg
                        break
                    if(_ == 9):
                        return 0
            return alloc

        def usagebw(_topo):
            usage = 0
            for link in list(_topo.edges.data()):
                usage += link[2]["bw"][1]
            return usage

        # alloc vnf to server
        serverCap = []
        for node in list(topo.nodes.data()):
            if(node[1]["model"] == "server"):
                serverCap.append(node[1]["RAM"][0] - node[1]["RAM"][1])
        vnfCap = []
        for vnf in list(sfc["struct"].nodes.data()):
            vnfCap.append(vnf[1]["RAM"])

        alloc = randPlacement(serverCap, vnfCap)

        if(alloc):
            for vnf in list(sfc["struct"].nodes.data()):
                c_server = alloc[vnf[0]] # the choosen server
                vnf[1]["server"] = c_server

            for vlink in list(sfc["struct"].edges.data()):
                s = sfc["struct"].nodes[vlink[0]]["server"]
                d = sfc["struct"].nodes[vlink[1]]["server"]
                _topo = copy.deepcopy(topo)
                
                v_link = sfc["struct"].edges[vlink[0], vlink[1]]
                for p_link in list(_topo.edges.data()):
                    if(p_link[2]["bw"][0] - p_link[2]['bw'][1] < v_link["bw"]):
                        _topo.remove_edge(p_link[0], p_link[1])
                try:
                    route = nx.shortest_path(_topo, s, d)
                    for i in range(len(route) - 1):
                        topo.edges[route[i], route[i+1]]['bw'] = [
                            topo.edges[route[i], route[i+1]]['bw'][0],
                            topo.edges[route[i], route[i+1]]['bw'][1] + v_link["bw"]
                        ]
                    sfc["struct"].edges[vlink[0], vlink[1]]["route"] = route
                except:
                    logging.debug(f"cannot routing from {s} to {d}")
                    return False
            sfc["DataCentre"] = DC.id

            return copy.deepcopy(sfc)

        else:
            return False


class DemoSelector(Selector):
    def __init__(self):
        super().__init__()
        


    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo) #M
        sfc = copy.deepcopy(sfcInput) #M
        
        def placement(bin, package):
            n_bin = len(bin)
            n_package = len(package)
            arg = round(5 / 4 * pow(4 * n_bin, 2/3) + 1)
            alloc = [-1] * n_package
            for i in range(n_package):
                for _ in range(1, 20):
                    idx = np.random.randint(0, n_bin)
                    if(bin[idx] > package[i]):
                        bin[idx] -= package[i]
                        alloc[i] = idx + arg
                        break
                    return 0

            return alloc

        # alloc vnf to server
        serverCap = []
        for node in list(topo.nodes.data()):
            if(node[1]["model"] == "server"):
                serverCap.append(node[1]["capacity"] - node[1]["usage"])
        vnfCap = []
        for vnf in list(sfc["struct"].nodes.data()):
            vnfCap.append(vnf[1]["demand"])
            usage = []
        for node in list(DC.topo.nodes.data()):
            if(node[1]["model"] == "server"):
                nei = list(DC.topo.neighbors(node[0]))[0]
                usage.append(DC.topo[node[0]][nei]['usage'])

        alloc = placement(serverCap, vnfCap)

        if(alloc):
            for vnf in list(sfc["struct"].nodes.data()):
                c_server = alloc[vnf[0]] # the choosen server
                vnf[1]["server"] = c_server

            data = list(sfc["struct"].edges.data())

            demand_bw = []
            for i in data:
                demand_bw.append(i[2]['demand'])

            for itr in np.argsort(demand_bw)[::-1]:
                s = sfc["struct"].nodes[data[itr][0]]["server"]
                d = sfc["struct"].nodes[data[itr][1]]["server"]

                _topo = copy.deepcopy(topo)
                
                v_link = sfc["struct"].edges[data[itr][0], data[itr][1]]
                for p_link in list(_topo.edges.data()):
                    if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                        _topo.remove_edge(p_link[0], p_link[1])
                try:
                    route = nx.shortest_path(_topo, s, d)
                    for i in range(len(route) - 1):
                        topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                    if len(route) == 1: route = []
                    sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = route
                except:
                    logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                    sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = []
                    return 1

            sfc["DataCentre"] = DC.id
            return copy.deepcopy(sfc)
        else:
            logging.debug("cannot alloc")
            return 2
        


import matplotlib.pyplot as plt

class HRE(Selector):
    """
    Heuristic Resource and Energy Aware SFC Embedding Algorithm
    ===
    selector HRE algorithm for analysing SFC waxman random topo
    """
    def __init__(self):
        super().__init__()
        


    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo)
        # nx.draw(topo, with_labels = True)
        # plt.show()
        sfc = copy.deepcopy(sfcInput)

        def Placement(serverCap, package):
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            k = round((len(serverCap)*4)**(1/3))
            a,b,a2,b2,onState = [],[],[],[],[]
            for i in serverCap:
                if i==100: onState.append(1)
                else: onState.append(0)
            for i in range(2*len(serverCap)//k):
                a.append(sum(onState[i*k//2:(i+1)*k//2]))
                a2.append(sum(serverCap[i*k//2:(i+1)*k//2]))
            for i in range(4*len(serverCap)//(k**2)):
                b.append(a[i*(k//2):(i+1)*k//2])
                b2.append(a2[i*(k//2):(i+1)*k//2])
            b = np.array(b)
            b2 = np.array(b2)

            def process(b):
                vnf_c = 0
                result = []
                if np.sum(b) == 0:
                    array = np.argsort(np.sum(b,axis=1))[::-1]
                else:
                    array = np.argsort(np.sum(b2,axis=1))
                for j in array:
                    # choose candidate groups with the least number of servers in ON State
                    for i in np.argsort(b2[j]):
                        addr = (k//2)*j+i
                        temp = np.array(serverCap[addr*(k//2):(addr+1)*(k//2)])
                        for l in np.argsort(temp):
                            while temp[l] >= package[vnf_c]:
                                temp[l] -= package[vnf_c]
                                result.append(addr*(k//2)+l)
                                vnf_c += 1
                                # print(temp)
                                if vnf_c >= len(package): return result
                return result

            result = process(b)
            if len(result) < len(package): return False
            alloc = []
            for i in result:
                alloc += [i+arg]
            return alloc

        # alloc vnf to server
        serverCap = []
        for node in list(topo.nodes.data()):
            if(node[1]["model"] == "server"):
                serverCap.append(node[1]["capacity"] - node[1]["usage"])
        vnfCap = []
        for vnf in list(sfc["struct"].nodes.data()):
            vnfCap.append(vnf[1]["demand"])
            usage = []
        for node in list(DC.topo.nodes.data()):
            if(node[1]["model"] == "server"):
                nei = list(DC.topo.neighbors(node[0]))[0]
                usage.append(DC.topo[node[0]][nei]['usage'])
        print('serverCap',serverCap)
        # print('vnfCap',vnfCap)
        alloc = Placement(serverCap, vnfCap)

        if(alloc):
            for vnf in list(sfc["struct"].nodes.data()):
                c_server = alloc[vnf[0]] # the choosen server
                vnf[1]["server"] = c_server

            data = list(sfc["struct"].edges.data())

            demand_bw = []
            for i in data:
                demand_bw.append(i[2]['demand'])

            for itr in np.argsort(demand_bw)[::-1]:
                s = sfc["struct"].nodes[data[itr][0]]["server"]
                d = sfc["struct"].nodes[data[itr][1]]["server"]

                _topo = copy.deepcopy(topo)
                
                v_link = sfc["struct"].edges[data[itr][0], data[itr][1]]
                for p_link in list(_topo.edges.data()):
                    if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                        _topo.remove_edge(p_link[0], p_link[1])
                try:
                    route = nx.shortest_path(_topo, s, d)
                    for i in range(len(route) - 1):
                        topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                    if len(route) == 1: route = []
                    sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = route
                except:
                    logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                    sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = []
                    return 1

            sfc["DataCentre"] = DC.id
            # print(sfc['struct'].edges.data())
            # print(sfc['struct'].nodes.data())
            return copy.deepcopy(sfc)
        else:
            logging.debug("cannot alloc")
            return 2




class VNFG(Selector):
    """
    VNF-FG algorithm
    ===
    Using VNF-FG algorithm for the paper: Online Joint VNF Chain
    Composition Embedding for 5G Networks ::

        selector = VNFG()
    """
    def __init__(self):
        super().__init__()

    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo)
        sfc = copy.deepcopy(sfcInput)

        def rand_FeasibleNodes(cap, demand):
            feasibleNodes = [i for i in range(len(cap)) if cap[i] >= demand]
            if len(feasibleNodes) == 0:
                return False
            id = random.randint(0, len(feasibleNodes) - 1)
            return feasibleNodes[id]

        def RandPlacement(serverCap, package):
            """
            random placement with the node spliting
            """
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            alloc = []
            count = len(package)
            for i in range(len(package)):
                rand_id = rand_FeasibleNodes(serverCap, 1)
                if rand_id == False:
                    return False
                elif serverCap[rand_id] >= package[i]:
                    alloc.append(rand_id + arg)
                    sfc["struct"].nodes[i]["server"] = rand_id + arg
                    serverCap[rand_id] -= package[i]
                else: # splitting
                    print('try to split virtual node:', i)
                    alloc.append(rand_id + arg)
                    old_cap = serverCap[rand_id]
                    new_cap = package[i] - serverCap[rand_id]
                    serverCap[rand_id] = 0
                    new_id = rand_FeasibleNodes(serverCap, new_cap)
                    if new_id == False:
                        return False
                    else:
                        new_server = new_id + arg
                    # create a new node: count
                    sfc["struct"].add_node(count, SFC=sfc["struct"].nodes[0]['SFC'], demand=new_cap, server=new_server)
                    serverCap[new_id] -= new_cap
                    # edit old
                    sfc["struct"].nodes[i]["server"] = rand_id + arg
                    sfc["struct"].nodes[i]['demand'] = old_cap
                        
                    for neig in sfc["struct"].neighbors(i):
                        abc = sfc["struct"][i][neig]['demand']
                        old_bw = (abc*old_cap)//package[i]
                        sfc["struct"][i][neig]['demand'] = old_bw
                        new_bw = abc - old_bw
                        # add new edge, with properties as same as old node
                        sfc["struct"].add_edge(count,neig,demand=new_bw,route=[])
                    count += 1
                    # print(sfc["struct"].edges.data())

            if len(alloc) < len(package):
                return False

            return True
            
        # alloc vnf to server
        serverCap = []
        for node in list(topo.nodes.data()):
            if(node[1]["model"] == "server"):
                serverCap.append(node[1]["capacity"] - node[1]["usage"])
        vnfCap = []
        for vnf in list(sfc["struct"].nodes.data()):
            vnfCap.append(vnf[1]["demand"])

        # print(sfc["struct"].edges.data())
        alloc = RandPlacement(serverCap, vnfCap)

        result = copy.deepcopy(sfcInput)

        if(alloc):
            for vlink in list(sfc["struct"].edges.data()):
                s = sfc["struct"].nodes[vlink[0]]["server"]
                d = sfc["struct"].nodes[vlink[1]]["server"]

                _topo = copy.deepcopy(topo)
                
                v_link = sfc["struct"].edges[vlink[0], vlink[1]]
                for p_link in list(_topo.edges.data()):
                    if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                        _topo.remove_edge(p_link[0], p_link[1])
                try:
                    route = nx.shortest_path(_topo, s, d)
                    for i in range(len(route) - 1):
                        topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                    sfc["struct"].edges[vlink[0], vlink[1]]["route"] = route
                except:
                    logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                    sfc["struct"].edges[vlink[0], vlink[1]]["route"] = []
                    return 1

            sfc["DataCentre"] = DC.id
            return copy.deepcopy(sfc)
        else:
            logging.debug("cannot alloc")
            return 2




class PWS(Selector):
    """
    Parallelized Waxman SFC (tên tạm)
    ===
    This is just a researching algorithm

    Made by Ma Duc
    """
    def __init__(self, k_sub):
        super().__init__()
        self.k_sub = k_sub
        self.name = "PWS_" + str(k_sub)

    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo)
        sfc = copy.deepcopy(sfcInput)
        
        avr_bw = 0
        for bw in sfc['struct'].edges.data():
            avr_bw += bw[2]['demand']
        # if len(sfcInput['struct'].edges.data()) == 0: return False
        avr_bw = avr_bw // len(sfc['struct'].edges.data())

        splited_bw = [self.k_sub]*(avr_bw//self.k_sub)
        if avr_bw % self.k_sub != 0:
            splited_bw.append(avr_bw % self.k_sub)

        def Placement(serverCap, vnfCap, bwCap):
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            serverCap = np.array(serverCap)
            bwCap = np.array(bwCap)
            k = round((len(serverCap)*4)**(1/3))
            a,b=[],[]

            def transfer(array):
                for i in range(2*len(array)//k):
                    a.append(sum(array[i*k//2:(i+1)*k//2]))
                for i in range(4*len(array)//(k**2)):
                    b.append(a[i*(k//2):(i+1)*k//2])
                return np.array(b)

            b = transfer(bwCap)
            def process():
                vnf_c = 0
                result = []
                for i in np.argsort(np.sum(b,axis=1)):
                    for j in np.argsort(b[i]):
                        addr = (k//2)*i+j
                        temp = np.array(serverCap[addr*(k//2):(addr+1)*(k//2)])
                        for l in np.argsort(np.array(bwCap[addr*(k//2):(addr+1)*(k//2)])):
                            # print(serverCap[addr+l])
                            while temp[l] >= vnfCap[vnf_c]:
                                temp[l] -= vnfCap[vnf_c]
                                result.append([addr*(k//2)+l,temp[l]])
                                vnf_c += 1
                                # print(temp)
                                if vnf_c >= len(vnfCap): return result
                return result

            result = process()
            if len(result) < len(vnfCap): return False
            alloc = []
            for i in result:
                alloc += [i[0]+arg]
            return alloc

        def processing(sfc):
            # alloc vnf to server
            serverCap = []
            bwCap = []
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])
                    near = list(topo.neighbors(node[0]))
                    bwCap.append(topo.edges[node[0],near[0]]['usage'])
            
            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])

            alloc = Placement(serverCap, vnfCap, bwCap)

            if(alloc):
                for vnf in list(sfc["struct"].nodes.data()):
                    c_server = alloc[vnf[0]] # the choosen server
                    vnf[1]["server"] = c_server
                    topo.nodes[c_server]['usage'] += vnf[1]["demand"]

                for vlink in list(sfc["struct"].edges.data()):
                    s = sfc["struct"].nodes[vlink[0]]["server"]
                    d = sfc["struct"].nodes[vlink[1]]["server"]
                    # print('s',s,'d',d)

                    _topo = copy.deepcopy(topo)
                    
                    v_link = sfc["struct"].edges[vlink[0], vlink[1]]
                    for p_link in list(_topo.edges.data()):
                        if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                            _topo.remove_edge(p_link[0], p_link[1])
                    try:
                        route = nx.shortest_path(_topo, s, d)
                        for i in range(len(route) - 1):
                            topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                        sfc["struct"].edges[vlink[0], vlink[1]]["route"] = route
                    except:
                        logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                        sfc["struct"].edges[vlink[0], vlink[1]]["route"] = []
                        return 1
                sfc["DataCentre"] = DC.id
                # return sfc
                return copy.deepcopy(sfc)
            else:
                logging.debug("cannot alloc")
                return 2
        
        result = copy.deepcopy(sfcInput)

        temp = nx.Graph()
        for (itr, sbw) in enumerate(splited_bw):
            """ Split an Original User Request"""
            if itr != 0: print('sub-user:',itr+1)
            sfc_i = copy.deepcopy(sfcInput)

            # split bandwidth for sub-user
            for bw in sfc_i['struct'].edges.data():
                bw[2]['demand'] = round((bw[2]['demand']*sbw)/avr_bw)
            # split CPU demand
            for dm in sfc_i['struct'].nodes.data():
                dm[1]['demand'] = round((dm[1]['demand']*sbw)/avr_bw)

            output = processing(sfc_i)
            # print("sfci",sfc_i['struct'].edges.data())
            # print("sfci",sfc_i['struct'].nodes.data())

            # change nodes name
            if itr > 0:
                leng = len(sfc_i['struct'].nodes.data())
                mapping = dict(zip(sfc_i['struct'], range(leng*itr,leng*(itr+1))))
                sfc_i['struct'] = nx.relabel_nodes(sfc_i['struct'], mapping)

            if output == 1 or output == 2: return output
            else:
                temp = nx.disjoint_union(temp, sfc_i['struct'])

        result["DataCentre"] = DC.id
        result['struct'] = temp
        # print(result['struct'].edges.data())
        # print(result['struct'].nodes.data())
        return copy.deepcopy(result)




class ONP_SFO_linear(Selector):
    """
    Using Online Parallelized SFC Orchestration algorithm for the paper:
    
    Online Parallelized Service Function Chain Orchestration in Data Center Networks
    ===
    Use for chaining SFC (0 - 1 - 2 - 3 ...)

    `Lưu ý`: Chỉ sử dụng cho chuỗi SFC! ::

        selector = ONP_SFO(k_sub = 10)
    """
    def __init__(self, k_sub):
        super().__init__()
        self.k_sub = k_sub
        self.name = "ONP_SFO_" + str(k_sub)

    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo)
        sfc = copy.deepcopy(sfcInput)
        
        avr_bw = 0
        for bw in sfc['struct'].edges.data():
            avr_bw += bw[2]['demand']
        avr_bw = avr_bw // len(sfc['struct'].edges.data())

        splited_bw = [self.k_sub]*(avr_bw//self.k_sub)
        if avr_bw % self.k_sub != 0:
            splited_bw.append(avr_bw % self.k_sub)
        
        temp = nx.Graph()
        result = copy.deepcopy(sfcInput)

        def process():
            nd, nd2 = 0, 0
            count = 0
            for i in np.argsort(agg_bw):
                # choose less bw group
                for j in np.argsort(np.array(edge_bw[i*(k//2):(i+1)*(k//2)])):
                    addr = i*(k//2)+j
                    # choose smallest bw
                    for l in np.argsort(np.array(serverCap[addr*(k//2):(addr+1)*(k//2)])):
                        # l from 0 to k/2 - 1
                        nd = addr*(k//2)+l+arg  # node

                        if nd2 != 0:
                            _topo = copy.deepcopy(topo)
                            v_link = sfc_i["struct"].edges[count-1, count]
                            for p_link in list(_topo.edges.data()):
                                if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                                    _topo.remove_edge(p_link[0], p_link[1])
                            try:
                                route = nx.shortest_path(_topo, nd, nd2)
                                # print('nd',nd,'nd2',nd2)
                                
                                for i in range(len(route) - 1):
                                    topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                                sfc_i["struct"].edges[count-1, count]["route"] = route
                                # print('route',route)
                            except:
                                # logging.debug(f"cannot routing from {nd} to {nd2}, bw = {v_link['demand']} ---------")
                                # sfc_i["struct"].edges[count-1, count]["route"] = []
                                # return 1
                                continue

                        if sfc_i["struct"].nodes[count]['demand'] > (topo.nodes[nd]['capacity'] - topo.nodes[nd]['usage']):
                            continue

                        while sfc_i["struct"].nodes[count]['demand'] <= (topo.nodes[nd]['capacity'] - topo.nodes[nd]['usage']):
                            topo.nodes[nd]['usage'] = topo.nodes[nd]['usage'] + sfc_i["struct"].nodes[count]['demand']
                            sfc_i["struct"].nodes[count]['server'] = nd
                            count += 1
                            if count >= len(sfc["struct"].nodes.data()): return
                        
                        nd2 = nd

            if count < len(sfc["struct"].nodes.data()):
                return 2    # can not alloc

        for (itr, sbw) in enumerate(splited_bw):
            serverCap = []
            agg_bw_temp = []
            edge_bw = []
            # print(topo.nodes.data())
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])
                else:
                    us = 0
                    for near in topo.neighbors(node[0]):
                        us += topo[node[0]][near]['usage']
                    if(node[1]["tag"] == "aggregation"):
                        agg_bw_temp.append(us)
                    if(node[1]["tag"] == "edge"):
                        edge_bw.append(us)

            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            k = round((len(serverCap)*4)**(1/3))

            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])
            agg_bw = []
            for i in range((len(agg_bw_temp)*2)//k):
                agg_bw.append(sum(agg_bw_temp[i*(k//2):(i+1)*(k//2)]))
            agg_bw = np.array(agg_bw)

            """ Split an Original User Request"""
            if itr != 0: print('sub-user:',itr+1)
            sfc_i = copy.deepcopy(sfcInput)
            # split bandwidth for sub-user
            for bw in sfc_i['struct'].edges.data():
                bw[2]['demand'] = round((bw[2]['demand']*sbw)/avr_bw)
            # split CPU demand
            for dm in sfc_i['struct'].nodes.data():
                dm[1]['demand'] = round((dm[1]['demand']*sbw)/avr_bw)

            output = process()
            if output == 1 or output == 2: return output
            
            # or else
            leng = len(sfc_i['struct'].nodes.data())
            mapping = dict(zip(sfc_i['struct'], range(leng*itr,leng*(itr+1))))
            sfc_i['struct'] = nx.relabel_nodes(sfc_i['struct'], mapping)
            temp = nx.disjoint_union(temp, sfc_i['struct'])

        result["DataCentre"] = DC.id
        result['struct'] = temp
        # print(result['struct'].edges.data())
        # print(result['struct'].nodes.data())
        return copy.deepcopy(result)




class ONP_SFO_waxman(Selector):
    """
    Using Online Parallelized SFC Orchestration algorithm for the paper:
    
    Online Parallelized Service Function Chain Orchestration in Data Center Networks
    ===
    Use for waxman
    """
    def __init__(self, k_sub):
        super().__init__()
        self.k_sub = k_sub
        self.name = "ONP_SFO_" + str(k_sub)

    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo)
        sfc = copy.deepcopy(sfcInput)
        
        avr_bw = 0
        for bw in sfc['struct'].edges.data():
            avr_bw += bw[2]['demand']
        # if len(sfcInput['struct'].edges.data()) == 0: return False
        avr_bw = avr_bw // len(sfc['struct'].edges.data())

        splited_bw = [self.k_sub]*(avr_bw//self.k_sub)
        if avr_bw % self.k_sub != 0:
            splited_bw.append(avr_bw % self.k_sub)

        def Placement(serverCap, vnfCap):
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            result = []
            for vnf in vnfCap:
                temp = []
                for i in range(len(serverCap)):
                    if vnf <= serverCap[i]: temp.append(i)
                if len(temp) == 0:
                    return False
                else:
                    itr = random.randint(0,len(temp)-1)
                    result.append(temp[itr])
                    serverCap[temp[itr]] -= vnf
            
            alloc = []
            for i in result:
                alloc += [i+arg]
            return alloc

        def processing(sfc):
            # alloc vnf to server
            serverCap = []
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])

            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])

            # print("serverCap",serverCap)
            # print("vnfCap",vnfCap)
            alloc = Placement(serverCap, vnfCap)

            if(alloc):
                for vnf in list(sfc["struct"].nodes.data()):
                    c_server = alloc[vnf[0]] # the choosen server
                    vnf[1]["server"] = c_server
                    # print('a', topo.nodes[c_server]['usage'], ' + ',vnf[1]["demand"])
                    topo.nodes[c_server]['usage'] += vnf[1]["demand"]
                    # print('b =', topo.nodes[c_server]['usage'])

                for vlink in list(sfc["struct"].edges.data()):
                    s = sfc["struct"].nodes[vlink[0]]["server"]
                    d = sfc["struct"].nodes[vlink[1]]["server"]
                    # print('s',s,'d',d)

                    _topo = copy.deepcopy(topo)
                    
                    v_link = sfc["struct"].edges[vlink[0], vlink[1]]
                    for p_link in list(_topo.edges.data()):
                        if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                            _topo.remove_edge(p_link[0], p_link[1])
                    try:
                        route = nx.shortest_path(_topo, s, d)
                        for i in range(len(route) - 1):
                            topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                        sfc["struct"].edges[vlink[0], vlink[1]]["route"] = route
                    except:
                        logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                        sfc["struct"].edges[vlink[0], vlink[1]]["route"] = []
                        return 1
                sfc["DataCentre"] = DC.id
                # return sfc
                return copy.deepcopy(sfc)
            else:
                logging.debug("cannot alloc")
                return 2
        
        result = copy.deepcopy(sfcInput)

        temp = nx.Graph()
        for (itr, sbw) in enumerate(splited_bw):
            """ Split an Original User Request"""
            if itr != 0: print('sub-user:',itr+1)
            sfc_i = copy.deepcopy(sfcInput)

            # split bandwidth for sub-user
            for bw in sfc_i['struct'].edges.data():
                bw[2]['demand'] = round((bw[2]['demand']*sbw)/avr_bw)
            # split CPU demand
            for dm in sfc_i['struct'].nodes.data():
                dm[1]['demand'] = round((dm[1]['demand']*sbw)/avr_bw)

            output = processing(sfc_i)

            if output in [1,2]:
                return output

            # change nodes name
            leng = len(sfc_i['struct'].nodes.data())
            mapping = dict(zip(sfc_i['struct'], range(leng*itr,leng*(itr+1))))
            sfc_i['struct'] = nx.relabel_nodes(sfc_i['struct'], mapping)
            temp = nx.disjoint_union(temp, sfc_i['struct'])

        result["DataCentre"] = DC.id
        result['struct'] = temp
        # print(result['struct'].edges.data())
        # print(result['struct'].nodes.data())
        return copy.deepcopy(result)



class HRE_split(Selector):
    """
    HRE with Parallelized splitting
    ===
    Example::

        selector = HRE_split(30)        # k_sub = 30

    selector HRE algorithm for analysing SFC waxman random topo
    """
    def __init__(self, k_sub):
        super().__init__()
        self.k_sub = k_sub
        self.name = "HRE_split_" + str(k_sub)

    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo)
        sfc = copy.deepcopy(sfcInput)
        
        avr_bw = 0
        for bw in sfc['struct'].edges.data():
            avr_bw += bw[2]['demand']
        # if len(sfcInput['struct'].edges.data()) == 0: return False
        avr_bw = avr_bw // len(sfc['struct'].edges.data())

        splited_bw = [self.k_sub]*(avr_bw//self.k_sub)
        if avr_bw % self.k_sub != 0:
            splited_bw.append(avr_bw % self.k_sub)

        def Placement(serverCap, package):
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            k = round((len(serverCap)*4)**(1/3))
            a,b,a2,b2,onState = [],[],[],[],[]
            for i in serverCap:
                if i==100: onState.append(1)
                else: onState.append(0)
            for i in range(2*len(serverCap)//k):
                a.append(sum(onState[i*k//2:(i+1)*k//2]))
                a2.append(sum(serverCap[i*k//2:(i+1)*k//2]))
            for i in range(4*len(serverCap)//(k**2)):
                b.append(a[i*(k//2):(i+1)*k//2])
                b2.append(a2[i*(k//2):(i+1)*k//2])
            b = np.array(b)
            b2 = np.array(b2)

            def process(b):
                vnf_c = 0
                result = []
                if np.sum(b) == 0:
                    array = np.argsort(np.sum(b,axis=1))[::-1]
                else:
                    array = np.argsort(np.sum(b2,axis=1))
                for j in array:
                    # choose candidate groups with the least number of servers in ON State
                    for i in np.argsort(b2[j]):
                        addr = (k//2)*j+i
                        temp = np.array(serverCap[addr*(k//2):(addr+1)*(k//2)])
                        for l in np.argsort(temp):
                            while temp[l] >= package[vnf_c]:
                                temp[l] -= package[vnf_c]
                                result.append(addr*(k//2)+l)
                                vnf_c += 1
                                # print(temp)
                                if vnf_c >= len(package): return result
                return result

            result = process(b)
            if len(result) < len(package): return False
            alloc = []
            for i in result:
                alloc += [i+arg]
            return alloc

        def processing(sfc):
            # alloc vnf to server
            serverCap = []
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])

            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])

            # print("serverCap",serverCap)
            # print("vnfCap",vnfCap)
            alloc = Placement(serverCap, vnfCap)

            if(alloc):
                for vnf in list(sfc["struct"].nodes.data()):
                    c_server = alloc[vnf[0]] # the choosen server
                    vnf[1]["server"] = c_server
                    # print('a', topo.nodes[c_server]['usage'], ' + ',vnf[1]["demand"])
                    topo.nodes[c_server]['usage'] += vnf[1]["demand"]
                    # print('b =', topo.nodes[c_server]['usage'])

                for vlink in list(sfc["struct"].edges.data()):
                    s = sfc["struct"].nodes[vlink[0]]["server"]
                    d = sfc["struct"].nodes[vlink[1]]["server"]
                    # print('s',s,'d',d)

                    _topo = copy.deepcopy(topo)
                    
                    v_link = sfc["struct"].edges[vlink[0], vlink[1]]
                    for p_link in list(_topo.edges.data()):
                        if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                            _topo.remove_edge(p_link[0], p_link[1])
                    try:
                        route = nx.shortest_path(_topo, s, d)
                        for i in range(len(route) - 1):
                            topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                        sfc["struct"].edges[vlink[0], vlink[1]]["route"] = route
                    except:
                        logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                        sfc["struct"].edges[vlink[0], vlink[1]]["route"] = []
                        return 1
                sfc["DataCentre"] = DC.id
                # return sfc
                return copy.deepcopy(sfc)
            else:
                logging.debug("cannot alloc")
                return 2
        
        result = copy.deepcopy(sfcInput)

        temp = nx.Graph()
        for (itr, sbw) in enumerate(splited_bw):
            """ Split an Original User Request"""
            if itr != 0: print('sub-user:',itr+1)
            sfc_i = copy.deepcopy(sfcInput)

            # split bandwidth for sub-user
            for bw in sfc_i['struct'].edges.data():
                bw[2]['demand'] = round((bw[2]['demand']*sbw)/avr_bw)
            # split CPU demand
            for dm in sfc_i['struct'].nodes.data():
                dm[1]['demand'] = round((dm[1]['demand']*sbw)/avr_bw)

            output = processing(sfc_i)

            if output in [1,2]:
                return output

            # change nodes name
            leng = len(sfc_i['struct'].nodes.data())
            mapping = dict(zip(sfc_i['struct'], range(leng*itr,leng*(itr+1))))
            sfc_i['struct'] = nx.relabel_nodes(sfc_i['struct'], mapping)
            temp = nx.disjoint_union(temp, sfc_i['struct'])

        result["DataCentre"] = DC.id
        result['struct'] = temp
        # print(result['struct'].edges.data())
        # print(result['struct'].nodes.data())
        return copy.deepcopy(result)




class MIX(Selector):
    """
    HRE and HRE splitting
    ===
    
    Mix selector: Firstly, try to use HRE. If deployment not successful, try to use HRE with splitting
    
    Example::

        selector = MIX(30)        # k_sub = 30

    selector HRE algorithm for analysing SFC waxman random topo
    """
    def __init__(self, k_sub):
        super().__init__()
        self.k_sub = k_sub
        self.name = "MIX_" + str(k_sub)

    def analyse(self, DC, sfcInput):
        topo = copy.deepcopy(DC.topo)
        sfc = copy.deepcopy(sfcInput)


        def Placement(serverCap, package):
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            k = round((len(serverCap)*4)**(1/3))
            a,b,a2,b2,onState = [],[],[],[],[]
            for i in serverCap:
                if i==100: onState.append(1)
                else: onState.append(0)
            for i in range(2*len(serverCap)//k):
                a.append(sum(onState[i*k//2:(i+1)*k//2]))
                a2.append(sum(serverCap[i*k//2:(i+1)*k//2]))
            for i in range(4*len(serverCap)//(k**2)):
                b.append(a[i*(k//2):(i+1)*k//2])
                b2.append(a2[i*(k//2):(i+1)*k//2])
            b = np.array(b)
            b2 = np.array(b2)

            def process(b):
                vnf_c = 0
                result = []
                if np.sum(b) == 0:
                    array = np.argsort(np.sum(b,axis=1))[::-1]
                else:
                    array = np.argsort(np.sum(b2,axis=1))
                for j in array:
                    # choose candidate groups with the least number of servers in ON State
                    for i in np.argsort(b2[j]):
                        addr = (k//2)*j+i
                        temp = np.array(serverCap[addr*(k//2):(addr+1)*(k//2)])
                        for l in np.argsort(temp):
                            while temp[l] >= package[vnf_c]:
                                temp[l] -= package[vnf_c]
                                result.append(addr*(k//2)+l)
                                vnf_c += 1
                                # print(temp)
                                if vnf_c >= len(package): return result
                return result

            result = process(b)
            if len(result) < len(package): return False
            alloc = []
            for i in result:
                alloc += [i+arg]
            return alloc

        # normally ...

        serverCap = []
        for node in list(topo.nodes.data()):
            if(node[1]["model"] == "server"):
                serverCap.append(node[1]["capacity"] - node[1]["usage"])
        vnfCap = []
        for vnf in list(sfc["struct"].nodes.data()):
            vnfCap.append(vnf[1]["demand"])
        alloc = Placement(serverCap, vnfCap)

        def allocation(alloc):
            if(alloc):
                for vnf in list(sfc["struct"].nodes.data()):
                    c_server = alloc[vnf[0]] # the choosen server
                    vnf[1]["server"] = c_server

                data = list(sfc["struct"].edges.data())

                demand_bw = []
                for i in data:
                    demand_bw.append(i[2]['demand'])

                for itr in np.argsort(demand_bw)[::-1]:
                    s = sfc["struct"].nodes[data[itr][0]]["server"]
                    d = sfc["struct"].nodes[data[itr][1]]["server"]

                    _topo = copy.deepcopy(topo)
                    
                    v_link = sfc["struct"].edges[data[itr][0], data[itr][1]]
                    for p_link in list(_topo.edges.data()):
                        if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                            _topo.remove_edge(p_link[0], p_link[1])
                    try:
                        route = nx.shortest_path(_topo, s, d)
                        for i in range(len(route) - 1):
                            topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                        if len(route) == 1: route = []
                        sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = route
                    except:
                        logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                        sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = []
                        print(f"Error 1: cannot routing from {s} to {d}, bw = {v_link['demand']}")
                        return 1

                sfc["DataCentre"] = DC.id
                # print(sfc['struct'].edges.data())
                # print(sfc['struct'].nodes.data())
                return copy.deepcopy(sfc)
            else:
                logging.debug("cannot alloc")
                print("Error 2: Cannot alloc")
                return 2

        alct = allocation(alloc)
        if alct not in [1,2]:
            return alct

        ###########################################

        # splitting
        
        print("Try to use node splitting")
        topo = copy.deepcopy(DC.topo)
        sfc = copy.deepcopy(sfcInput)
        avr_bw = 0
        for bw in sfc['struct'].edges.data():
            avr_bw += bw[2]['demand']
        # if len(sfcInput['struct'].edges.data()) == 0: return False
        avr_bw = avr_bw // len(sfc['struct'].edges.data())

        splited_bw = [self.k_sub]*(avr_bw//self.k_sub)
        if avr_bw % self.k_sub != 0:
            splited_bw.append(avr_bw % self.k_sub)

        if len(splited_bw) == 1 and alct in [1,2]:
            print("Can not splitting")
            return alct

        def processing(sfc):
            # alloc vnf to server
            serverCap = []
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])

            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])

            # print("serverCap",serverCap)
            # print("vnfCap",vnfCap)
            alloc = Placement(serverCap, vnfCap)

            if(alloc):
                i = 0
                for vnf in list(sfc["struct"].nodes.data()):
                    c_server = alloc[i] # the choosen server
                    i += 1
                    vnf[1]["server"] = c_server
                    topo.nodes[c_server]['usage'] += vnf[1]["demand"]

                data = list(sfc["struct"].edges.data())
                demand_bw = []
                for i in data:
                    demand_bw.append(i[2]['demand'])

                for itr in np.argsort(demand_bw)[::-1]:
                    s = sfc["struct"].nodes[data[itr][0]]["server"]
                    d = sfc["struct"].nodes[data[itr][1]]["server"]

                    _topo = copy.deepcopy(topo)
                    
                    v_link = sfc["struct"].edges[data[itr][0], data[itr][1]]
                    for p_link in list(_topo.edges.data()):
                        if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                            _topo.remove_edge(p_link[0], p_link[1])
                    try:
                        route = nx.shortest_path(_topo, s, d)
                        for i in range(len(route) - 1):
                            topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                        sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = route
                    except:
                        logging.debug(f"splitting: cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                        sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = []
                        return 1
                sfc["DataCentre"] = DC.id
                # return sfc
                return copy.deepcopy(sfc)
            else:
                print("splitting: cannot alloc")
                logging.debug("splitting: cannot alloc")
                return 2
        
        result = copy.deepcopy(sfcInput)

        temp = nx.Graph()
        for (itr, sbw) in enumerate(splited_bw):
            """ Split an Original User Request"""
            if itr != 0: print('sub-user:',itr+1)
            sfc_i = copy.deepcopy(sfcInput)

            # split bandwidth for sub-user
            for bw in sfc_i['struct'].edges.data():
                bw[2]['demand'] = round((bw[2]['demand']*sbw)/avr_bw)
            # split CPU demand
            for dm in sfc_i['struct'].nodes.data():
                dm[1]['demand'] = round((dm[1]['demand']*sbw)/avr_bw)

            output = processing(sfc_i)

            if output in [1,2]:
                return output

            # change nodes name
            leng = len(sfc_i['struct'].nodes.data())
            mapping = dict(zip(sfc_i['struct'], range(leng*itr,leng*(itr+1))))
            sfc_i['struct'] = nx.relabel_nodes(sfc_i['struct'], mapping)
            temp = nx.disjoint_union(temp, sfc_i['struct'])

        result["DataCentre"] = DC.id
        result['struct'] = temp
        # print(result['struct'].edges.data())
        # print(result['struct'].nodes.data())
        return copy.deepcopy(result)

class MIX_ver2(Selector):
    """
    HRE and HRE splitting
    ===
    
    Mix selector: Firstly, try to use HRE. If deployment not successful, try to use HRE with splitting

    Version 2: With pyramid pointer
    
    Example::

        selector = MIX_ver2(30)        # k_sub = 30

    selector HRE algorithm for analysing SFC waxman random topo
    """
    def __init__(self, k_sub):
        super().__init__()
        self.k_sub = k_sub
        self.name = "MIX_PyP_" + str(k_sub)

    def analyse(self, DC, sfcInput):
        vnfCap = []
        neigh = []
        for vnf in list(sfcInput["struct"].nodes.data()):
            vnfCap.append(vnf[1]["demand"])
            us = 0
            for near in sfcInput["struct"].neighbors(vnf[0]):
                us += sfcInput["struct"][vnf[0]][near]['demand']
            neigh.append(us)
        # print('neigh',neigh)

        """ Sort algorithm in here """
        sorts = []

        # sort mode old
        """
        i = 0
        s = sum(neigh)
        while sum(neigh[:i]) < s//2:
            i += 1
        sorts.append(np.concatenate((np.argsort(np.array(neigh)[:i]),np.argsort(np.array(neigh)[i:])[::-1]+i)))
        """

        # new sort mode
        i = 0
        while i < len(neigh)+1:
            sorts.append(np.concatenate((np.argsort(neigh[:i]),np.argsort(neigh[i:])[::-1]+i)))
            i += 1

        def making_struct(sort):
            sfc = copy.deepcopy(sfcInput)
            mapping = dict(zip(sfcInput['struct'], sort))
            sfc['struct'] = nx.relabel_nodes(sfcInput['struct'], mapping)
            H = nx.Graph()
            H.add_nodes_from(sorted(sfc['struct'].nodes(data=True)))
            H.add_edges_from(sfc['struct'].edges(data=True))
            sfc['struct'] = H
            return sfc

        def Placement(serverCap, package):
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            k = round((len(serverCap)*4)**(1/3))
            a,b,a2,b2,onState = [],[],[],[],[]
            for i in serverCap:
                if i==100: onState.append(1)
                else: onState.append(0)
            for i in range(2*len(serverCap)//k):
                a.append(sum(onState[i*k//2:(i+1)*k//2]))
                a2.append(sum(serverCap[i*k//2:(i+1)*k//2]))
            for i in range(4*len(serverCap)//(k**2)):
                b.append(a[i*(k//2):(i+1)*k//2])
                b2.append(a2[i*(k//2):(i+1)*k//2])
            b = np.array(b)
            b2 = np.array(b2)

            def process(b):
                vnf_c = 0
                result = []
                if np.sum(b) == 0:
                    array = np.argsort(np.sum(b,axis=1))[::-1]
                else:
                    array = np.argsort(np.sum(b2,axis=1))
                for j in array:
                    # choose candidate groups with the least number of servers in ON State
                    for i in np.argsort(b2[j]):
                        addr = (k//2)*j+i
                        temp = np.array(serverCap[addr*(k//2):(addr+1)*(k//2)])
                        for l in np.argsort(temp):
                            while temp[l] >= package[vnf_c]:
                                temp[l] -= package[vnf_c]
                                result.append(addr*(k//2)+l)
                                vnf_c += 1
                                # print(temp)
                                if vnf_c >= len(package): return result
                return result

            result = process(b)
            if len(result) < len(package): return False
            alloc = []
            for i in result:
                alloc += [i+arg]
            return alloc

        alct = 0
        # normally ...
        for sort in sorts:
            sfc = making_struct(sort)
            topo = copy.deepcopy(DC.topo)
            serverCap = []
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])
            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])
            alloc = Placement(serverCap, vnfCap)

            def allocation(alloc):
                if(alloc):
                    i = 0
                    for vnf in list(sfc["struct"].nodes.data()):
                        c_server = alloc[i] # the choosen server
                        i += 1
                        vnf[1]["server"] = c_server
                        topo.nodes[c_server]['usage'] += vnf[1]["demand"]

                    data = list(sfc["struct"].edges.data())

                    demand_bw = []
                    for i in data:
                        demand_bw.append(i[2]['demand'])

                    for itr in np.argsort(demand_bw)[::-1]:
                        s = sfc["struct"].nodes[data[itr][0]]["server"]
                        d = sfc["struct"].nodes[data[itr][1]]["server"]

                        _topo = copy.deepcopy(topo)
                        
                        v_link = sfc["struct"].edges[data[itr][0], data[itr][1]]
                        for p_link in list(_topo.edges.data()):
                            if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                                _topo.remove_edge(p_link[0], p_link[1])
                        try:
                            route = nx.shortest_path(_topo, s, d)
                            for i in range(len(route) - 1):
                                topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                            if len(route) == 1: route = []
                            sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = route
                        except:
                            logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                            sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = []
                            print(f"Error 1: cannot routing from {s} to {d}, bw = {v_link['demand']}")
                            return 1

                    sfc["DataCentre"] = DC.id
                    # print(sfc['struct'].nodes.data())
                    # print(sfc['struct'].edges.data())
                    return copy.deepcopy(sfc)
                else:
                    logging.debug("cannot alloc")
                    print("Error 2: Cannot alloc")
                    return 2

            alct = allocation(alloc)
            if alct not in [1,2]:
                return alct
        
        print("Try to use node splitting")

        avr_bw = 0
        for bw in sfc['struct'].edges.data():
            avr_bw += bw[2]['demand']
        avr_bw = avr_bw // len(sfc['struct'].edges.data())

        splited_bw = [self.k_sub]*(avr_bw//self.k_sub)
        if avr_bw % self.k_sub != 0:
            splited_bw.append(avr_bw % self.k_sub)

        if len(splited_bw) == 1 and alct in [1,2]:
            print("Can not splitting")
            return alct

        topo = copy.deepcopy(DC.topo)

        def processing(sfc):
            # alloc vnf to server
            serverCap = []
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])

            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])

            alloc = Placement(serverCap, vnfCap)
            if(alloc):
                i = 0
                for vnf in list(sfc["struct"].nodes.data()):
                    c_server = alloc[i] # the choosen server
                    i += 1
                    vnf[1]["server"] = c_server
                    topo.nodes[c_server]['usage'] += vnf[1]["demand"]

                data = list(sfc["struct"].edges.data())
                demand_bw = []
                for i in data:
                    demand_bw.append(i[2]['demand'])

                for itr in np.argsort(demand_bw)[::-1]:
                    s = sfc["struct"].nodes[data[itr][0]]["server"]
                    d = sfc["struct"].nodes[data[itr][1]]["server"]

                    _topo = copy.deepcopy(topo)
                    
                    v_link = sfc["struct"].edges[data[itr][0], data[itr][1]]
                    for p_link in list(_topo.edges.data()):
                        if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                            _topo.remove_edge(p_link[0], p_link[1])
                    try:
                        route = nx.shortest_path(_topo, s, d)
                        for i in range(len(route) - 1):
                            topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                        sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = route
                    except:
                        logging.debug(f"splitting: cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                        sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = []
                        return 1
                # sfc["DataCentre"] = DC.id
                # return sfc
                return copy.deepcopy(sfc['struct'])
            else:
                print("splitting: cannot alloc")
                logging.debug("splitting: cannot alloc")
                return 2

        
        result = copy.deepcopy(sfcInput)
        temp = nx.Graph()
        for (itr, sbw) in enumerate(splited_bw):
            """ Split an Original User Request"""
            # if itr != 0: print('sub-user:',itr+1)
            output = 0
            for i in range(len(sorts)):
                print('sub-user:',itr+1,'sort mode:',i+1)
                # sfc_i = copy.deepcopy(sfcInput)
                sfc_i = making_struct(sorts[i])
                for bw in sfc_i['struct'].edges.data():
                    bw[2]['demand'] = round((bw[2]['demand']*sbw)/avr_bw)
                for dm in sfc_i['struct'].nodes.data():
                    dm[1]['demand'] = round((dm[1]['demand']*sbw)/avr_bw)
                output = processing(sfc_i)

                if output in [1,2]:
                    if i == len(sorts) - 1:
                        return output
                else: break

            leng = len(output.nodes.data())
            mapping = dict(zip(output, range(leng*itr,leng*(itr+1))))
            output = nx.relabel_nodes(output, mapping)
            temp = nx.disjoint_union(temp, output)

        result["DataCentre"] = DC.id
        result['struct'] = temp
        # print(result['struct'].edges.data())
        # print(result['struct'].nodes.data())
        return copy.deepcopy(result)


class HRE_ver2(Selector):
    """
    HRE with PyP strategy
    ===
    selector HRE algorithm for analysing SFC waxman random topo
    """
    def __init__(self):
        super().__init__()
        self.name = "HRE_PyP"

    def analyse(self, DC, sfcInput):
        vnfCap = []
        neigh = []
        for vnf in list(sfcInput["struct"].nodes.data()):
            vnfCap.append(vnf[1]["demand"])
            us = 0
            for near in sfcInput["struct"].neighbors(vnf[0]):
                us += sfcInput["struct"][vnf[0]][near]['demand']
            neigh.append(us)
        neigh = np.array(neigh)
        
        # print(list(DC.topo.edges.data()))
        usage = []
        for node in list(DC.topo.nodes.data()):
            if(node[1]["model"] == "server"):
                nei = list(DC.topo.neighbors(node[0]))[0]
                usage.append(DC.topo[node[0]][nei]['usage'])
                # serverCap.append(node[1]["capacity"] - node[1]["usage"])
    
        sorts = []
        arg = np.arange(len(neigh))
        # new sort mode
        i = 0
        while i < len(neigh):
            np.random.shuffle(arg)
            array = np.concatenate((arg[np.argsort(neigh[arg[:i]])],arg[np.argsort(neigh[arg[i:]])[::-1]+i]))
            sorts.append(array)
            array = np.concatenate((arg[np.argsort(neigh[arg[len(neigh)-i:]])+len(neigh)-i],arg[np.argsort(neigh[arg[:len(neigh)-i]])[::-1]]))
            sorts.append(array)
            i += 1

        def making_struct(sort):
            sfc = copy.deepcopy(sfcInput)
            mapping = dict(zip(sfcInput['struct'], sort))
            sfc['struct'] = nx.relabel_nodes(sfcInput['struct'], mapping)
            H = nx.Graph()
            H.add_nodes_from(sorted(sfc['struct'].nodes(data=True)))
            H.add_edges_from(sfc['struct'].edges(data=True))
            sfc['struct'] = H
            return sfc

        def Placement(serverCap, package):
            arg = round(5 / 4 * pow(4 * len(serverCap), 2/3) + 1)
            k = round((len(serverCap)*4)**(1/3))
            a,b,a2,b2,onState = [],[],[],[],[]
            for i in serverCap:
                if i==100: onState.append(1)
                else: onState.append(0)
            for i in range(2*len(serverCap)//k):
                a.append(sum(onState[i*k//2:(i+1)*k//2]))
                a2.append(sum(serverCap[i*k//2:(i+1)*k//2]))
            for i in range(4*len(serverCap)//(k**2)):
                b.append(a[i*(k//2):(i+1)*k//2])
                b2.append(a2[i*(k//2):(i+1)*k//2])
            b = np.array(b)
            b2 = np.array(b2)

            def process(b):
                vnf_c = 0
                result = []
                if np.sum(b) == 0:
                    array = np.argsort(np.sum(b,axis=1))[::-1]
                else:
                    array = np.argsort(np.sum(b2,axis=1))
                for j in array:
                    # choose candidate groups with the least number of servers in ON State
                    for i in np.argsort(b2[j]):
                        addr = (k//2)*j+i
                        temp = np.array(serverCap[addr*(k//2):(addr+1)*(k//2)])
                        for l in np.argsort(temp):
                            while temp[l] >= package[vnf_c]:
                                temp[l] -= package[vnf_c]
                                result.append(addr*(k//2)+l)
                                vnf_c += 1
                                # print(temp)
                                if vnf_c >= len(package): return result
                return result

            result = process(b)
            if len(result) < len(package): return False
            alloc = []
            for i in result:
                alloc += [i+arg]
            return alloc

        alct = 0
        # normally ...
        for (itr,sort) in enumerate(sorts):
            sfc = making_struct(sort)
            topo = copy.deepcopy(DC.topo)
            serverCap = []
            for node in list(topo.nodes.data()):
                if(node[1]["model"] == "server"):
                    serverCap.append(node[1]["capacity"] - node[1]["usage"])
            vnfCap = []
            for vnf in list(sfc["struct"].nodes.data()):
                vnfCap.append(vnf[1]["demand"])
            alloc = Placement(serverCap, vnfCap)

            def allocation(alloc):
                if(alloc):
                    i = 0
                    for vnf in list(sfc["struct"].nodes.data()):
                        c_server = alloc[i] # the choosen server
                        vnf[1]["server"] = c_server
                        i += 1
                        # topo.nodes[c_server]['usage'] += vnf[1]["demand"]

                    data = list(sfc["struct"].edges.data())

                    demand_bw = []
                    for i in data:
                        demand_bw.append(i[2]['demand'])

                    for itr in np.argsort(demand_bw)[::-1]:
                        s = sfc["struct"].nodes[data[itr][0]]["server"]
                        d = sfc["struct"].nodes[data[itr][1]]["server"]

                        _topo = copy.deepcopy(topo)
                        
                        v_link = sfc["struct"].edges[data[itr][0], data[itr][1]]
                        for p_link in list(_topo.edges.data()):
                            if(p_link[2]["capacity"] - p_link[2]['usage'] < v_link["demand"]):
                                _topo.remove_edge(p_link[0], p_link[1])
                        try:
                            route = nx.shortest_path(_topo, s, d)
                            for i in range(len(route) - 1):
                                topo.edges[route[i], route[i+1]]['usage'] += v_link["demand"]
                            if len(route) == 1: route = []
                            sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = route
                        except:
                            logging.debug(f"cannot routing from {s} to {d}, bw = {v_link['demand']} ---------")
                            sfc["struct"].edges[data[itr][0], data[itr][1]]["route"] = []
                            # print(f"Error 1: cannot routing from {s} to {d}, bw = {v_link['demand']}")
                            return 1

                    sfc["DataCentre"] = DC.id
                    # print(sfc['struct'].nodes.data())
                    # print(sfc['struct'].edges.data())
                    return copy.deepcopy(sfc)
                else:
                    logging.debug("cannot alloc")
                    # print("Error 2: Cannot alloc")
                    return 2
            
            alct = allocation(alloc)
            if alct not in [1, 2]:
                print(itr)
                alct["itr"] = itr
                return alct
        
        # if deployment not successful
        return alct