from utils.DBUtil import instance as DBUtil
from interfaces.Devices import Devices
from interfaces.Hosts import Hosts
from termcolor import colored
import networkx as nx
from tabulate import tabulate

class Mechanism:
    def __init__(self):
        self.table = [['Host','Switch','Connected through Port']]
    def getMappings(self,kg_relations):

        results = DBUtil.execute_query("MATCH (h:Host)-[:"+kg_relations["host_switch_rel"]+"]->(s:Switch) RETURN h,s")

        for hs_map in results:
            self.table.append([hs_map['h']['mac'],hs_map['s']['id'],hs_map['h']['port']])

        print(colored("The Following are the Host-Switch Mappings in the current network\n",'yellow',attrs=['bold']))
        print(colored(tabulate(self.table,headers="firstrow",tablefmt="fancy_grid",numalign="center"),'cyan',attrs=['bold']))

    def getSwitchMappings(self,kg_relations):
        results = DBUtil.execute_query("MATCH (s1:Switch)-[r:"+kg_relations["switch_switch_rel"]+"]->(s2:Switch) RETURN s1,s2,properties(r)")

        self.table = [["Switch 1","Switch 2","Egress Port","Ingress Port"]]
        for switch_map in results:
            self.table.append([switch_map['s1']['id'],switch_map['s2']['id'],
                               switch_map['properties(r)']['sourcePort'],switch_map['properties(r)']['destinationPort']])

        print(colored("The Following are the Switch-Switch Mappings in the current network\n", 'magenta', attrs=['bold']))
        print(colored(tabulate(self.table, headers="firstrow", tablefmt="fancy_grid", numalign="center"), 'white',
                      attrs=['bold']))