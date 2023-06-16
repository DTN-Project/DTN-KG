#SAMPLE POLICY MECHANISM DEFINITION FOR REACHABILITY CHECKING BETWEEN HOSTS

from utils.DBUtil import instance as DBUtil
from interfaces.Devices import Devices
from interfaces.Hosts import Hosts
from termcolor import colored
from tabulate import tabulate

class Mechanism:        # Class for defining Mechanism Should be named Mechanism, must follow naming conventions
    def __init__(self):
        self.switches = Devices()
        self.hosts = Hosts()

    def checkReachability(self,kg_relations):        #Mechanism Function to be deployed, this name must be passed in template policy deploy key

        # Getting the relations represented in built KG
        host_switch_rel = kg_relations["host_switch_rel"]
        switch_switch_rel = kg_relations["switch_switch_rel"]

        for h1 in self.hosts.getHosts()["hosts"]:
            for h2 in self.hosts.getHosts()["hosts"]:

                if(h2.get("mac",'') != h1.get("mac",'')):
                    d1 = DBUtil.execute_query("MATCH(n:Host{mac:"+"\'"+h1.get("mac",'')+"\'"+"}) RETURN n")
                    
                    if(len(d1) == 0):
                        print(colored(h1+" Not present in KG\n",'red'))

                    d2 = DBUtil.execute_query("MATCH(n:Host{mac:"+"\'"+ h2.get("mac",'')+"\'"+"}) RETURN n")
                    if(len(d2) == 0):
                        print(colored(h2+" Not present in KG\n",'red'))

                    d3 = DBUtil.execute_query("Match (h1:Host{mac:"+"\'"+h1.get("mac",'')+"\'"+"})-[r1:"+host_switch_rel+"]-(s1:Switch) return s1")
                    
                    d4 = DBUtil.execute_query("Match (s2:Switch)-[r3:"+host_switch_rel+"]-(h2:Host{mac:"+"\'"+h2.get("mac",'')+"\'"+"}) RETURN s2")
                    
                    sourceId = d3[0]['s1']['id']
                    destId = d4[0]['s2']['id']
                    query1 = "Match path=(s1:Switch{id:\'"+ sourceId +"'})-[r2:"+switch_switch_rel+"*]->(s2:Switch{id:\'"+ destId +"'}) RETURN path"
                    d5 = DBUtil.execute_query(query1)
                    
                    if(len(d5) !=0):
                        print(colored(h1.get("mac",'')+" has reachability to "+h2.get("mac",''),'green'))

                    else:
                        query1 = "Match path=(s1:Switch{id:\'"+ destId +"'})-[r2:"+switch_switch_rel+"*]->(s2:Switch{id:\'"+ sourceId +"'}) RETURN path"
                        d5 = DBUtil.execute_query(query1)
                        if(len(d5) !=0):
                            print(colored(h1.get("mac",'')+" has reachability to "+h2.get("mac",''),'green'))
                        else:
                            print(colored("No reachability between "+h1.get("mac",'')+" and "+h2.get("mac",'')+"\n",'red'))


    def getHopCounts(self,kg_relations):
        host_switch_rel = kg_relations["host_switch_rel"]
        switch_switch_rel = kg_relations["switch_switch_rel"]

        for h1 in self.hosts.getHosts()["hosts"]:
            for h2 in self.hosts.getHosts()["hosts"]:

                if(h2.get("mac",'') != h1.get("mac",'')):
                    if (len(DBUtil.execute_query(
                            "MATCH(n:Host{mac:" + "\'" + h1.get("mac", '') + "\'" + "}) RETURN n")) == 0):
                        continue

                    if (len(DBUtil.execute_query(
                            "MATCH(n:Host{mac:" + "\'" + h2.get("mac", '') + "\'" + "}) RETURN n")) == 0):
                        continue
                    
                    d3 = DBUtil.execute_query("Match (h1:Host{mac:"+"\'"+h1.get("mac",'')+"\'"+"})-[r1:"+host_switch_rel+"]-(s1:Switch) return s1")
                    
                    d4 = DBUtil.execute_query("Match (s2:Switch)-[r3:"+host_switch_rel+"]-(h2:Host{mac:"+"\'"+h2.get("mac",'')+"\'"+"}) RETURN s2")
                    
                    sourceId = d3[0]['s1']['id']
                    destId = d4[0]['s2']['id']
                    
                    query1 = "Match path=(s1:Switch{id:\'"+ sourceId +"'})-[r2:"+switch_switch_rel+"*]->(s2:Switch{id:\'"+ destId +"'}) RETURN path"
                    result = DBUtil.execute_query(query1)
                    
                    if(len(result) == 0):
                        query1 = "Match path=(s1:Switch{id:\'"+ destId +"'})-[r2:"+switch_switch_rel+"*]->(s2:Switch{id:\'"+ sourceId +"'}) RETURN path"
                        result = DBUtil.execute_query(query1)
                        
                    if (len(result) != 0):

                        hop_count = 0
                        for data in result:
                            if(type(data) == dict and 'mac' not in data):
                                hop_count +=1

                        print(colored(h1.get("mac", '') + " takes "+str(hop_count)+" hop to reach "+ h2.get("mac", ''), 'yellow'))
                    else:
                        continue

    
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