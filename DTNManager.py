from dtninter.Flowrule import Flowrule
from dtninter.Hosts import Hosts
from dtninter.Links import Links
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
        self.hosts = Hosts(self.auth)
        self.links = Links(self.auth)
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
        
    def connect_hosts_to_switches(self):
        hosts = self.hosts.getHosts()

        with self.graphDB.session(database="dtnkg") as graphDB_Session:
            for host in hosts['hosts']:
                locations = host['locations']
                hostId = host['id']
                macId = host['mac']
                print("Locations of " + hostId + " ....")
                for location in locations:
                    switchId = str(location["elementId"][len(location["elementId"])-1])
                    port = str(location['port'])
                    print(switchId + "-" + port)
                    if(len(graphDB_Session.run("MATCH(n:Host{id:\""+macId+"\"}) RETURN n").data()) == 0):
                        graphDB_Session.run("CREATE(n:Host{id:\""+macId+"\"})")
                    graphDB_Session.run("MATCH(a:Switch{id:"+switchId+"}),(b:Host{id:\""+macId+"\"}) CREATE (b)-[r:isConnected{Port:"+port+"}]->(a)")
        
    def connect_switches(self):
        links = self.links.getLinks()

        with self.graphDB.session(database="dtnkg") as graphDB_Session:
            for link in links['links']:
                sourceSwitchId = str(link['src']['device'][len(link['src']['device'])-1])
                sourcePort = str(link['src']['port'])
                destinationSwitchId = str(link['dst']['device'][len(link['dst']['device'])-1])
                destinationPort = str(link['dst']['port'])
                if(len(graphDB_Session.run("MATCH (a:Switch{id:"+sourceSwitchId+"})-[r:isConnected]-(b:Switch{id:"+destinationSwitchId+"}) return r").data()) == 0):
                    graphDB_Session.run("MATCH (a:Switch{id:"+sourceSwitchId+"}),(b:Switch{id:"+destinationSwitchId+"}) CREATE (a)-[r:isConnected{SrcPort:"+sourcePort+",DstPort:"+destinationPort+"}]->(b)")



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
                        switchId = str(flows["deviceId"][len(flows["deviceId"])-1])
                        if(len(graphDB_Session.run("MATCH(n:Switch{id:"+switchId+"}) RETURN n").data()) == 0):
                            graphDB_Session.run("CREATE(n:Switch{id:"+switchId+"})") # Switch Node with Switch ID
                            deviceId = str(flows["deviceId"][len(flows["deviceId"])-1])
                            tableId = str(flows["tableId"])
                            graphDB_Session.run("CREATE(n:FlowTable{id:"+tableId+deviceId+"})")      #Flow Table Node
                            graphDB_Session.run("MATCH(a:Switch{id:"+switchId+"}),(b:ForwardingDevice) CREATE (a)-[r:isA]->(b)")
                            graphDB_Session.run("MATCH(a:Switch{id:"+switchId+"}),(b:FlowTable{id:"+tableId+deviceId+"}) CREATE (a)-[r:hasComponent]->(b)")

                        flowId = str(flows["id"])
                        graphDB_Session.run("CREATE(n:Flow{id:"+flowId+"})")                     #Flow Node to represent the flow
                        graphDB_Session.run("CREATE(n:Match{id:"+flowId+"})")                                        # Match node for Match fields
                        graphDB_Session.run("MATCH(a:Flow{id:"+flowId+"}),(b:Match{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")

                        if(len(flows["selector"]["criteria"])>=2):
                            src = ''.join(x for x in re.split(":",str(flows["selector"]["criteria"][2]["mac"])))
                            dst = ''.join(x for x in re.split(":",str(flows["selector"]["criteria"][1]["mac"])))
                            
                            graphDB_Session.run("CREATE(n:EthAddress{id:"+flowId+",src:\""+src+"\",dst:\""+dst+"\"})")
                            graphDB_Session.run("CREATE(n:In_Port{id:"+flowId+",in_port:"+str(flows["selector"]["criteria"][0]["port"])+"})")
                            graphDB_Session.run("MATCH(a:Match{id:"+flowId+"}),(b:EthAddress{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")     #Node for Ethernet MatchField
                            graphDB_Session.run("MATCH(a:Match{id:"+flowId+"}),(b:In_Port{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")        #Input Port Node

                        graphDB_Session.run("CREATE(n:Instruction{id:"+flowId+",type:\""+str(flows["treatment"]["instructions"][0]["type"])+"\",port:\""+str(flows["treatment"]["instructions"][0]["port"])+"\"})")
                        graphDB_Session.run("MATCH(a:Flow{id:"+flowId+"}),(b:Instruction{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")
                             
                        graphDB_Session.run("CREATE(n:Priority{id:"+flowId+",value:"+str(flows["priority"])+"})")                     #Flow Priority Node
                        graphDB_Session.run("CREATE(n:Timeout{id:"+flowId+",timeout_value:" + str(flows['timeout']) + "})")           #Flow Timeout Node
                       
                        graphDB_Session.run("MATCH(a:Flow{id:" + flowId + "}),(b:Priority{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")
                        graphDB_Session.run("MATCH(a:Flow{id:" + flowId + "}),(b:Timeout{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")
                        graphDB_Session.run("MATCH(a:Flow{id:"+flowId+"}),(b:FlowTable{id:"+tableId+deviceId+"}) CREATE (b)-[r:hasComponent]->(a)")
                        
                
                self.connect_switches()
                self.connect_hosts_to_switches()
                
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
