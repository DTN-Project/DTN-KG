#SAMPLE POLICY MECHANISM DEFINITION FOR REACHABILITY CHECKING BETWEEN HOSTS

from utils.DBUtil import instance as DBUtil
from interfaces.Devices import Devices
from interfaces.Hosts import Hosts
from termcolor import colored

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
                    if(len(DBUtil.execute_query("MATCH(n:Host{mac:"+"\'"+h1.get("mac",'')+"\'"+"}) RETURN n")) == 0):
                        print(colored(h1+" Not present in KG\n",'red'))

                    if(len(DBUtil.execute_query("MATCH(n:Host{mac:"+"\'"+ h2.get("mac",'')+"\'"+"}) RETURN n")) == 0):
                        print(colored(h2+" Not present in KG\n",'red'))

                    if(len(DBUtil.execute_query("Match path=(h1:Host{mac:"+"\'"+h1.get("mac",'')+"\'"+"})-[r1:"+host_switch_rel+"*]-(s1:Switch)-[r2:"+switch_switch_rel+"*]-(s2:Switch)-[r3:"+host_switch_rel+"*]-(h2:Host{mac:"+"\'"+h2.get("mac",'')+"\'"+"}) RETURN path")) !=0):
                        print(colored(h1.get("mac",'')+" has reachability to "+h2.get("mac",''),'green'))

                    else:
                        print(colored("No reachability between "+h1.get("mac",'')+" and "+h2.get("mac",'')+"\n",'red'))

