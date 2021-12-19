from interfaces.FlowRules import FlowRules
from interfaces.Hosts import Hosts
from interfaces.Links import Links
import time
from os import system
from utils.DBUtil import instance as DBUtil

#DTNManager For Defining the Manager Component of the DTN Architecture
class DTNManager:
    def __init__(self):
        self.fr = FlowRules()
        self.hosts = Hosts()
        self.links = Links()
        self.mac_port = {}                      #To Store The Flow Rules while we build the flow rule KG
        try:
            self.create_head_nodes()

        except Exception as e:
            print(e)


    def create_head_nodes(self):
        #Creates the main Object and Forwarding Device Nodes in DB
        if(len(DBUtil.execute_query("MATCH(n:Object) RETURN n")) == 0):
            DBUtil.execute_query("CREATE(n:Object)")
            DBUtil.execute_query("CREATE(n:ForwardingDevice)")
            DBUtil.execute_query("MATCH(a:ForwardingDevice),(b:Object) CREATE (a)-[r:isA]->(b)")
            DBUtil.execute_query("CREATE(n:Service)")
            DBUtil.execute_query("CREATE(n:FlowRuleReachability)")
            DBUtil.execute_query("MATCH(a:FlowRuleReachability),(b:Service) CREATE (a)-[r:isA]->(b)")
            DBUtil.execute_query("CREATE(n:FlowRulePath)")
            DBUtil.execute_query("MATCH(a:FlowRuleReachability),(b:FlowRulePath) CREATE (a)-[r:hasComponent]->(b)")
                    
        
    def connect_hosts_to_switches(self):
        hosts = self.hosts.getHosts()

        for host in hosts['hosts']:
            locations = host['locations']
            hostId = host['id']
            macId = host['mac']
            print("Locations of " + hostId + " ....")
            for location in locations:
                switchId = str(location["elementId"][len(location["elementId"])-1])
                port = str(location['port'])
                print(switchId + "-" + port)
                if(len(DBUtil.execute_query("MATCH(n:Host{id:\""+macId+"\"}) RETURN n")) == 0):
                    DBUtil.execute_query("CREATE(n:Host{id:\""+macId+"\"})")
                    DBUtil.execute_query("CREATE(n:FRHost{id:\""+macId+"\"})")
                    
                DBUtil.execute_query("MATCH(a:FRSwitch{id:"+switchId+"}),(b:FRHost{id:\""+macId+"\"}) CREATE (b)-[r:isConnected{Port:"+port+"}]->(a)")
                DBUtil.execute_query("MATCH(a:Switch{id:"+switchId+"}),(b:Host{id:\""+macId+"\"}) CREATE (b)-[r:isConnected{Port:"+port+"}]->(a)")
        
    def connect_switches(self):
        links = self.links.getLinks()

        for link in links['links']:
            sourceSwitchId = str(link['src']['device'][len(link['src']['device'])-1])
            sourcePort = str(link['src']['port'])
            destinationSwitchId = str(link['dst']['device'][len(link['dst']['device'])-1])
            destinationPort = str(link['dst']['port'])
            if(len(DBUtil.execute_query("MATCH (a:Switch{id:"+sourceSwitchId+"})-[r:isConnected]-(b:Switch{id:"+destinationSwitchId+"}) return r")) == 0):
                DBUtil.execute_query("MATCH (a:Switch{id:"+sourceSwitchId+"}),(b:Switch{id:"+destinationSwitchId+"}) CREATE (a)-[r:isConnected{SrcPort:"+sourcePort+",DstPort:"+destinationPort+"}]->(b)")

    def build_flowrule_reachability(self):
        links = self.links.getLinks()

        #We iterate through each link and check the corresponding flow rule in the FlowRule KG constructed, then we add an edge between the switches for all the matching source and destination mac addresses as link properties
        #To store the flow rules we use a dictionary called mac_port which we use to store the flow rules for each switch ID
        
        for link in links['links']:
            sourceSwitchId = str(link['src']['device'][len(link['src']['device'])-1])
            sourcePort = str(link['src']['port'])
            destinationSwitchId = str(link['dst']['device'][len(link['dst']['device'])-1])
            destinationPort = str(link['dst']['port'])

            if(len(DBUtil.execute_query("MATCH(n:FRSwitch{id:"+sourceSwitchId+"}) return n"))==0):
                DBUtil.execute_query("CREATE(n:FRSwitch{id:"+sourceSwitchId+"})")
                DBUtil.execute_query("MATCH(a:FlowRulePath),(b:FRSwitch{id:"+sourceSwitchId+"}) CREATE (a)-[r:hasPath]->(b)")

            if(len(DBUtil.execute_query("MATCH(n:FRSwitch{id:"+destinationSwitchId+"}) return n"))==0):
                DBUtil.execute_query("CREATE(n:FRSwitch{id:"+destinationSwitchId+"})")

            edge_flag = False
            if sourceSwitchId in self.mac_port:
                for sfr in self.mac_port[sourceSwitchId]:
                    if sfr["out_port"] == sourcePort and sfr["out_type"] == "OUTPUT":
                        if destinationSwitchId in self.mac_port:
                            for dfr in self.mac_port[destinationSwitchId]:
                                if dfr["in_port"] == destinationPort:
                                    edge_flag = True

                                    if(len(DBUtil.execute_query("MATCH path = (a:FRSwitch{id:"+sourceSwitchId+"})-[r:hasPath{in_port:"+destinationPort+",src_mac:\""+dfr["dst_mac"]+"\",dst_mac:\""+sfr["src_mac"]+"\",out_port:"+sourcePort+"}]-(b:FRSwitch{id:"+destinationSwitchId+"}) RETURN path"))== 0 and len(DBUtil.execute_query("MATCH path = (a:FRSwitch{id:"+sourceSwitchId+"})-[r:hasPath{in_port:"+sourcePort+",src_mac:\""+sfr["src_mac"]+"\",dst_mac:\""+dfr["dst_mac"]+"\",out_port:"+destinationPort+"}]-(b:FRSwitch{id:"+destinationSwitchId+"}) RETURN path"))== 0):
                                        DBUtil.execute_query("MATCH(a:FRSwitch{id:"+sourceSwitchId+"}),(b:FRSwitch{id:"+destinationSwitchId+"}) CREATE (a)-[r:hasPath{in_port:"+sourcePort+",src_mac:\""+sfr["src_mac"]+"\",dst_mac:\""+dfr["dst_mac"]+"\",out_port:"+destinationPort+"}]->(b)")
                                                
                                 
    def getdata_and_build(self):
        #Trying to get flowrules from SDN and building the KG
        try:
            while(True):
                flow_rules = self.fr.getFlowRules()
                #print(flow_rules)

                #with self.graphDB.session(database="dtnkg") as graphDB_Session:
                DBUtil.execute_query("MATCH(n) DETACH DELETE n")
                print("\033[91m Deleted Old Graph...Rebuilding\033[00m")

                self.create_head_nodes()
                for flows in flow_rules['flows']:
                    switchId = str(flows["deviceId"][len(flows["deviceId"])-1])
                    if(len(DBUtil.execute_query("MATCH(n:Switch{id:"+switchId+"}) RETURN n")) == 0):
                        DBUtil.execute_query("CREATE(n:Switch{id:"+switchId+"})") # Switch Node with Switch ID
                        deviceId = str(flows["deviceId"][len(flows["deviceId"])-1])
                        tableId = str(flows["tableId"])
                        DBUtil.execute_query("CREATE(n:FlowTable{id:"+tableId+deviceId+"})")      #Flow Table Node
                        DBUtil.execute_query("MATCH(a:Switch{id:"+switchId+"}),(b:ForwardingDevice) CREATE (a)-[r:isA]->(b)")
                        DBUtil.execute_query("MATCH(a:Switch{id:"+switchId+"}),(b:FlowTable{id:"+tableId+deviceId+"}) CREATE (a)-[r:hasComponent]->(b)")

                    flowId = str(flows["id"])
                    DBUtil.execute_query("CREATE(n:Flow{id:"+flowId+"})")                     #Flow Node to represent the flow
                    DBUtil.execute_query("CREATE(n:Match{id:"+flowId+"})")                                        # Match node for Match fields
                    DBUtil.execute_query("MATCH(a:Flow{id:"+flowId+"}),(b:Match{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")

                    out_port = str(flows["treatment"]["instructions"][0]["port"])
                    out_type = str(flows["treatment"]["instructions"][0]["type"])
                    
                    if(len(flows["selector"]["criteria"])>=2):
                        src = str(flows["selector"]["criteria"][2]["mac"])
                        dst = str(flows["selector"]["criteria"][1]["mac"])
                        in_port = str(flows["selector"]["criteria"][0]["port"])
                        
                        DBUtil.execute_query("CREATE(n:EthAddress{id:"+flowId+",src:\""+src+"\",dst:\""+dst+"\"})")
                        DBUtil.execute_query("CREATE(n:In_Port{id:"+flowId+",in_port:"+in_port+"})")
                        DBUtil.execute_query("MATCH(a:Match{id:"+flowId+"}),(b:EthAddress{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")     #Node for Ethernet MatchField
                        DBUtil.execute_query("MATCH(a:Match{id:"+flowId+"}),(b:In_Port{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")#Input Port Node
                        if switchId not in self.mac_port:
                            self.mac_port[switchId] = []

                        self.mac_port[switchId].append({"in_port":in_port,"src_mac":src,"dst_mac":dst,"out_type":out_type,"out_port":out_port})
                    
                    DBUtil.execute_query("CREATE(n:Instruction{id:"+flowId+",type:\""+out_type+"\",port:\""+out_port+"\"})")
                    DBUtil.execute_query("MATCH(a:Flow{id:"+flowId+"}),(b:Instruction{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")
                            
                    DBUtil.execute_query("CREATE(n:Priority{id:"+flowId+",value:"+str(flows["priority"])+"})")                     #Flow Priority Node
                    DBUtil.execute_query("CREATE(n:Timeout{id:"+flowId+",timeout_value:" + str(flows['timeout']) + "})")           #Flow Timeout Node
                    
                    DBUtil.execute_query("MATCH(a:Flow{id:" + flowId + "}),(b:Priority{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")
                    DBUtil.execute_query("MATCH(a:Flow{id:" + flowId + "}),(b:Timeout{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")
                    DBUtil.execute_query("MATCH(a:Flow{id:"+flowId+"}),(b:FlowTable{id:"+tableId+deviceId+"}) CREATE (b)-[r:hasComponent]->(a)")

                

                self.connect_switches()
                self.build_flowrule_reachability()
                self.connect_hosts_to_switches() #Connecting the hosts to the FlowRule Switches for the Flow Rule Reachability Graph
                
                print("\033[92m KG Building Finished\033[00m\n")
                time.sleep(5)
                system('clear')
                print("\033[91m Clearing Graph....Refreshing\033[00m\n")

        except Exception:
            print(traceback.format_exc())
            print("\033[91m Closing\033[00m\n")
            self.graphDB.close()


            
d = DTNManager()
d.getdata_and_build()
