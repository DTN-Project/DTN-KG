#SAMPLE POLICY MECHANISM DEFINITION FOR REACHABILITY CHECKING BETWEEN HOSTS

from utils.DBUtil import instance as DBUtil
from interfaces.Devices import Devices
from interfaces.Hosts import Hosts
from termcolor import colored
import time

class Mechanism:        # Class for defining Mechanism Should be named Mechanism, must follow naming conventions
    def __init__(self):
        self.switches = Devices()
        self.hosts = Hosts()

    def checkReachability(self,kg_relations):        #Mechanism Function to be deployed, this name must be passed in template policy deploy key

        # Getting the relations represented in built KG
        host_switch_rel = kg_relations["host_switch_rel"]
        switch_switch_rel = kg_relations["switch_switch_rel"]

        avg = []
        for h1 in self.hosts.getHosts()["hosts"]:
            for h2 in self.hosts.getHosts()["hosts"]:

                if(h2.get("mac",'') != h1.get("mac",'')):
                    s1 = time.time()
                    d1 = DBUtil.execute_query("MATCH(n:Host{mac:"+"\'"+h1.get("mac",'')+"\'"+"}) RETURN n")
                    e1 = time.time() - s1
                    #print(f"E1 = {e1}")
                    avg.append(e1)

                    if(len(d1) == 0):
                        print(colored(h1+" Not present in KG\n",'red'))

                    s1 = time.time()
                    d2 = DBUtil.execute_query("MATCH(n:Host{mac:"+"\'"+ h2.get("mac",'')+"\'"+"}) RETURN n")
                    e1 = time.time() - s1
                    #print(f"E2 = {e1}")
                    avg.append(e1)
                    if(len(d2) == 0):
                        print(colored(h2+" Not present in KG\n",'red'))

                    s1 = time.time()
                    d3 = DBUtil.execute_query("Match (h1:Host{mac:"+"\'"+h1.get("mac",'')+"\'"+"})-[r1:"+host_switch_rel+"]-(s1:Switch) return s1")
                    e1 = time.time() - s1
                    #print(f"E3 = {e1}")
                    avg.append(e1)
                    
                    s1 = time.time()
                    d4 = DBUtil.execute_query("Match (s2:Switch)-[r3:"+host_switch_rel+"]-(h2:Host{mac:"+"\'"+h2.get("mac",'')+"\'"+"}) RETURN s2")
                    e1 = time.time() - s1
                    #print(f"E4 = {e1}")
                    avg.append(e1)

                    sourceId = d3[0]['s1']['id']
                    destId = d4[0]['s2']['id']
                    s1 = time.time()
                    query1 = "Match path=(s1:Switch{id:\'"+ sourceId +"'})-[r2:"+switch_switch_rel+"*]->(s2:Switch{id:\'"+ destId +"'}) RETURN path"
                    #print(f"{query1}")
                    d5 = DBUtil.execute_query(query1)
                    e1 = time.time() - s1
                    #print(f"E5 = {e1}")
                    avg.append(e1)

                    if(len(d5) !=0):
                        print(colored(h1.get("mac",'')+" has reachability to "+h2.get("mac",''),'green'))

                    else:
                        s1 = time.time()
                        query1 = "Match path=(s1:Switch{id:\'"+ destId +"'})-[r2:"+switch_switch_rel+"*]->(s2:Switch{id:\'"+ sourceId +"'}) RETURN path"
                        #print(f"{query1}")
                        d5 = DBUtil.execute_query(query1)
                        e1 = time.time() - s1
                        #print(f"E6 = {e1}")
                        avg.append(e1)
                        if(len(d5) !=0):
                            print(colored(h1.get("mac",'')+" has reachability to "+h2.get("mac",''),'green'))
                        else:
                            print(colored("No reachability between "+h1.get("mac",'')+" and "+h2.get("mac",'')+"\n",'red'))

                    print(f"Avg response time - {sum(avg)/len(avg)}")
