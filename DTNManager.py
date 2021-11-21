from dtninter.Flowrule import Flowrule
from requests.auth import HTTPBasicAuth
import json
import datetime
import time
import os
from neo4j import GraphDatabase
import re
from os import system

#DTNManager For Defining the Manager Component of the DTN Architecture
class DTNManager:
    def __init__(self,user,pwd):
        self.auth = HTTPBasicAuth(user,pwd)
        self.fr = Flowrule(self.auth)
        try:
            self.graphDB = GraphDatabase.driver("bolt://localhost:7687", auth=("dtn_user", "password"))
            print("DB Intialized")
            self.create_head_nodes()
            
        except Exception as e:
            print(e)


    def create_head_nodes(self):
        #Creates the main Object and Forwarding Device Nodes in DB
        with self.graphDB.session(database="dtnkg") as graphDB_Session:
                if(len(graphDB_Session.run("MATCH(n:Object) RETURN n").data()) == 0):
                    graphDB_Session.run("CREATE(n:Object)")
                    graphDB_Session.run("CREATE(n:ForwardingDevice)")
                    graphDB_Session.run("MATCH(a:ForwardingDevice),(b:Object) CREATE (a)-[r:isA]->(b)")
        

    def getdata_and_build(self):
        #Trying to get flowrules from SDN and building the KG
        try:
            while(True):
                flow_rules = self.fr.getFlowRules()
                print(flow_rules)

                with self.graphDB.session(database="dtnkg") as graphDB_Session:
                    graphDB_Session.run("MATCH(n) DETACH DELETE n")
                    print("\033[91m Deleted Old Graph...Rebuilding\033[00m")

                    self.create_head_nodes()
                    for flows in flow_rules['flows']:
                        if(len(graphDB_Session.run("MATCH(n:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+") RETURN n").data()) == 0):
                            graphDB_Session.run("CREATE(n:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+")") # Switch Node with Switch ID
                            graphDB_Session.run("CREATE(n:FlowTable"+str(flows["tableId"])+str(flows["deviceId"][len(flows["deviceId"])-1])+")")      #Flow Table Node
                            graphDB_Session.run("MATCH(a:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+"),(b:ForwardingDevice) CREATE (a)-[r:isA]->(b)")
                            graphDB_Session.run("MATCH(a:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+"),(b:FlowTable"+str(flows["tableId"])+str(flows["deviceId"][len(flows["deviceId"])-1])+") CREATE (a)-[r:hasComponent]->(b)")

                        graphDB_Session.run("CREATE(n:Flow"+str(flows["id"])+")")                     #Flow Node to represent the flow
                        graphDB_Session.run("CREATE(n:Match"+str(flows["id"])+")")                                        # Match node for Match fields
                        graphDB_Session.run("MATCH(a:Flow"+str(flows["id"])+ "),(b:Match"+str(flows["id"])+") CREATE (a)-[r:hasComponent]->(b)")

                        if(len(flows["selector"]["criteria"])>=2):
                            src = ''.join(x for x in re.split(":",str(flows["selector"]["criteria"][2]["mac"])))
                            dst = ''.join(x for x in re.split(":",str(flows["selector"]["criteria"][1]["mac"])))
                            
                            graphDB_Session.run("CREATE(n:EthAddress"+str(flows["id"])+"{src:\""+src+"\",dst:\""+dst+"\"})")
                            graphDB_Session.run("CREATE(n:In_Port"+str(flows["id"])+"{in_port:"+str(flows["selector"]["criteria"][0]["port"])+"})")
                            graphDB_Session.run("MATCH(a:Match"+str(flows["id"])+"),(b:EthAddress"+str(flows["id"])+") CREATE (a)-[r:hasComponent]->(b)")     #Node for Ethernet MatchField
                            graphDB_Session.run("MATCH(a:Match"+str(flows["id"])+"),(b:In_Port"+str(flows["id"])+") CREATE (a)-[r:hasComponent]->(b)")        #Input Port Node

                        graphDB_Session.run("CREATE(n:Instruction"+str(flows["id"])+"{type:\""+str(flows["treatment"]["instructions"][0]["type"])+"\",port:\""+str(flows["treatment"]["instructions"][0]["port"])+"\"})")
                        graphDB_Session.run("MATCH(a:Flow"+str(flows["id"])+"),(b:Instruction"+str(flows["id"])+") CREATE (a)-[r:hasComponent]->(b)")
                             
                        graphDB_Session.run("CREATE(n:Priority"+str(flows["id"])+"{value:"+str(flows["priority"])+"})")                     #Flow Priority Node
                        graphDB_Session.run("CREATE(n:Timeout"+str(flows["id"])+"{timeout_value:" + str(flows['timeout']) + "})")           #Flow Timeout Node
                       
                        graphDB_Session.run("MATCH(a:Flow" + str(flows["id"]) + "),(b:Priority"+str(flows["id"])+") CREATE (a)-[r:hasComponent]->(b)")
                        graphDB_Session.run("MATCH(a:Flow" + str(flows["id"]) + "),(b:Timeout"+str(flows["id"])+") CREATE (a)-[r:hasComponent]->(b)")
                        graphDB_Session.run("MATCH(a:Flow"+str(flows["id"])+"),(b:FlowTable"+str(flows["tableId"])+str(flows["deviceId"][len(flows["deviceId"])-1])+") CREATE (b)-[r:hasComponent]->(a)")
                        
                    print("\033[92m KG Building Finished\033[00m\n")
                time.sleep(5)
                system('clear')
                print("\033[91m Clearing Graph....Refreshing\033[00m\n")

        except Exception:
            print(traceback.format_exc())
            print("\033[91m Closing\033[00m\n")
            self.graphDB.close()


            
d = DTNManager("onos","rocks")
d.getdata_and_build()
