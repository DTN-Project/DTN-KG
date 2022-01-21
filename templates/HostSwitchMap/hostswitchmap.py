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
