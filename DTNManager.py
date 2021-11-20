from dtninter.Flowrule import Flowrule
from requests.auth import HTTPBasicAuth
import json
import datetime
import time
import os
from neo4j import GraphDatabase

class DTNManager:
    def __init__(self,user,pwd):
        self.auth = HTTPBasicAuth(user,pwd)
        self.fr = Flowrule(self.auth)
        try:
            self.graphDB = GraphDatabase.driver("bolt://localhost:7687", auth=("dtn_user", "password"))
            print("DB Intialized")

            with self.graphDB.session(database="dtnkg") as graphDB_Session:
                if(len(graphDB_Session.run("MATCH(n:Object) RETURN n").data()) == 0):
                    graphDB_Session.run("CREATE(n:Object)")
                    graphDB_Session.run("CREATE(n:ForwardingDevice)")
                    graphDB_Session.run("MATCH(a:ForwardingDevice),(b:Object) CREATE (a)-[r:isA]->(b)")

        except Exception as e:
            print(e)


    def getdata_and_build(self):
        #Trying to get flowrules from SDN and building the KG
        flow_rules = self.fr.getFlowRules()
        print(flow_rules)

        with self.graphDB.session(database="dtnkg") as graphDB_Session:
            for flows in flow_rules['flows']:
                if(len(graphDB_Session.run("MATCH(n:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+") RETURN n").data()) == 0):
                    graphDB_Session.run("CREATE(n:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+")")
                    graphDB_Session.run("CREATE(n:FlowTable"+str(flows["tableId"])+")")
                    graphDB_Session.run("MATCH(a:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+"),(b:ForwardingDevice) CREATE (a)-[r:isA]->(b)")
                    graphDB_Session.run("MATCH(a:Switch"+str(flows["deviceId"][len(flows["deviceId"])-1])+"),(b:FlowTable"+str(flows["tableId"])+") CREATE (a)-[r:hasComponent]->(b)")
                        
                graphDB_Session.run("CREATE(n:Flow"+str(flows["id"])+")")
                graphDB_Session.run("CREATE(n:Match)")
                graphDB_Session.run("MATCH(a:Flow" +str(flows["id"])+ "),(b:Match) CREATE (a)-[r:hasComponent]->(b)")

                if(len(flows["treatment"]["instructions"])>=2):
                    graphDB_Session.run("CREATE(EthAddress:EthAddress{src:"+flows["selector"]["criteria"][2]+",dst:"+flows["selector"]["criteria"][1]+"})")
                #graphDB_Session.run("CREATE(Instruction:Instruction{type:"+str(flows["treatment"]["instructions"][0]["type"])+",port:"+str(flows["treatment"]["instructions"][0]["port"])+"})")
                graphDB_Session.run("CREATE(n:Priority{value:"+str(flows["priority"])+"})")
                graphDB_Session.run("CREATE(n:Timeout{timeout_value:" + str(flows['timeout']) + "})")
                graphDB_Session.run("MATCH(Flow:Flow" + str(flows["id"])+"),(EthAddress:EthAddress) CREATE (Flow)-[r:hasComponent]->(EthAddress)")
                #graphDB_Session.run("MATCH(Flow:Flow" + str(flows["id"]) + "),(Instruction:Instruction) CREATE (Flow)-[r:hasComponent]->(Instruction)")
                graphDB_Session.run("MATCH(a:Flow" + str(flows["id"]) + "),(b:Priority) CREATE (a)-[r:hasComponent]->(b)")
                graphDB_Session.run("MATCH(a:Flow" + str(flows["id"]) + "),(b:Timeout) CREATE (a)-[r:hasComponent]->(b)")

                graphDB_Session.run("MATCH(a:Flow"+str(flows["id"])+"),(b:FlowTable"+str(flows["tableId"])+") CREATE (b)-[r:hasComponent]->(a)")
                                    
        print("KG Building Finished\n")
        self.graphDB.close()

d = DTNManager("onos","rocks")
d.getdata_and_build()
