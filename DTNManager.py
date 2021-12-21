from interfaces.FlowRules import FlowRules
from interfaces.Hosts import Hosts
from interfaces.Links import Links
import time
from os import system
from utils.DBUtil import instance as DBUtil
from pyfiglet import Figlet
from termcolor import colored
from utils.logger import logger as Logger
import datetime
from utils.Configs import Config
import requests

#DTNManager For Defining the Manager Component of the DTN Architecture
class DTNManager:
    def __init__(self):
        self.fr = FlowRules()
        self.hosts = Hosts()
        self.links = Links()
        self.mac_port = {}                      #To Store The Flow Rules while we build the flow rule KG
        Logger.log_write("DTN Manager Intializing")
        try:
            self.create_head_nodes()
            Logger.log_write("DTN Manager Initialized")
            
        except Exception as e:
            print(e)
            Logger.log_write("DTN Manager Initialization Failed ["+e+"]")
            Logger.close_log()
            self.graphDB.close()           

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
        Logger.log_write("KG Head Nodes Created") 
                    
        
    def connect_hosts_to_switches(self):
        hosts = self.hosts.getHosts()
        Logger.log_write("Hosts information retrieved from REST API call")
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
                Logger.log_write("Hosts Connected to Flow Rule KG")
                DBUtil.execute_query("MATCH(a:Switch{id:"+switchId+"}),(b:Host{id:\""+macId+"\"}) CREATE (b)-[r:isConnected{Port:"+port+"}]->(a)")
                Logger.log_write("Hosts connected to KG")
        
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
        Logger.log_write("Link information retrieved from REST API call to /links")
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
                Logger.log_write("FRSwitch Node created for source switch and appended to FlowRulePath")

            if(len(DBUtil.execute_query("MATCH(n:FRSwitch{id:"+destinationSwitchId+"}) return n"))==0):
                DBUtil.execute_query("CREATE(n:FRSwitch{id:"+destinationSwitchId+"})")
                Logger.log_write("FRSwitch for destination switch created")

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
                                        Logger.log_write("FlowRule edge established between source and destination nodes in FlowRule KG")
                                                
                                 
    def getdata_and_build(self):
        Logger.log_write("Intial KG Build started")
        #Trying to get flowrules from SDN and building the KG
        try:
            while(True):
                flow_rules = self.fr.getFlowRules()
                Logger.log_write("Flow rules retired using REST API call to /flows")
                #print(flow_rules)

                #with self.graphDB.session(database="dtnkg") as graphDB_Session:
                DBUtil.execute_query("MATCH(n) DETACH DELETE n")
                Logger.log_write("Old graph cleared")
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mDeleted Old Graph...Rebuilding\033[00m")

                self.create_head_nodes()
                for flows in flow_rules['flows']:
                    Logger.log_write("Creating a flow node for a flow")
                    switchId = str(flows["deviceId"][len(flows["deviceId"])-1])
                    if(len(DBUtil.execute_query("MATCH(n:Switch{id:"+switchId+"}) RETURN n")) == 0):
                        DBUtil.execute_query("CREATE(n:Switch{id:"+switchId+"})") # Switch Node with Switch ID
                        Logger.log_write("Switch node created for flow rule KG")
                        deviceId = str(flows["deviceId"][len(flows["deviceId"])-1])
                        tableId = str(flows["tableId"])
                        DBUtil.execute_query("CREATE(n:FlowTable{id:"+tableId+deviceId+"})")      #Flow Table Node
                        Logger.log_write("Flow table node created")
                        DBUtil.execute_query("MATCH(a:Switch{id:"+switchId+"}),(b:ForwardingDevice) CREATE (a)-[r:isA]->(b)")
                        Logger.log_write("Switch connected to ForwardingDeice node")
                        DBUtil.execute_query("MATCH(a:Switch{id:"+switchId+"}),(b:FlowTable{id:"+tableId+deviceId+"}) CREATE (a)-[r:hasComponent]->(b)")
                        Logger.log_write("Switch node connected to flow table node")

                    flowId = str(flows["id"])
                    DBUtil.execute_query("CREATE(n:Flow{id:"+flowId+"})")                     #Flow Node to represent the flow
                    Logger.log_write("Flow node created")
                    DBUtil.execute_query("CREATE(n:Match{id:"+flowId+"})")                                        # Match node for Match fields
                    Logger.log_write("Match node created")
                    DBUtil.execute_query("MATCH(a:Flow{id:"+flowId+"}),(b:Match{id:"+flowId+"}) CREATE (a)-[r:hasComponent]->(b)")
                    Logger.log_write("Match node connected to flow node")

                    out_port = str(flows["treatment"]["instructions"][0]["port"])
                    out_type = str(flows["treatment"]["instructions"][0]["type"])
                    
                    if(len(flows["selector"]["criteria"])>=2):
                        src = str(flows["selector"]["criteria"][2]["mac"])
                        dst = str(flows["selector"]["criteria"][1]["mac"])
                        in_port = str(flows["selector"]["criteria"][0]["port"])
                        
                        DBUtil.execute_query("CREATE(n:EthAddress{id:"+flowId+",src:\""+src+"\",dst:\""+dst+"\"})")
                        Logger.log_write("Ethernet node created")
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
                    Logger.log_write("Flow node connected to priority,timeout and flowtable nodes")

                self.connect_switches()
                self.build_flowrule_reachability()
                self.connect_hosts_to_switches() #Connecting the hosts to the FlowRule Switches for the Flow Rule Reachability Graph
                
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[92mKG Building Finished...Press Ctrl+C to exit\033[00m\n")
                
                Logger.log_write("KG building completed")
                time.sleep(5)
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mClearing Graph....Refreshing\033[00m\n")
                Logger.log_write("KG clearing and refreshing")
                system('clear')
        except Exception:
            print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mClosing\033[00m\n")
            Logger.log_write("Closing connections")
            Logger.close_log()
            self.graphDB.close()


#Helper Function to check if the REST Endpoints are up and running for the DB and SDN instances            
def stat_checker(endpoint):
    try:
        response = requests.get(endpoint)
        return True
    
    except Exception:
        return False


DB_running = stat_checker("http://"+Config.db_host+":"+Config.db_port)
SDN_running = stat_checker("http://"+Config.sdn_host+":"+Config.sdn_port)


d = DTNManager()
fig = Figlet(font="standard")
    
    
while(True):
    system("clear")
    print(colored(fig.renderText("Digital Twin Network"),"cyan"))
    print("Database Instance: ",colored("Running","green") if DB_running else colored("Not Running","red"),end="\t\t")
    print("SDN Instance: ",colored("Running","green") if SDN_running else colored("Not Running","red"))
    print(colored("\n[h]-Help\t[s]-Start KG Build\t[e]-Exit\t[c]-Configure","white","on_grey",attrs=["bold","blink"]))
    inp = input()
    if(inp =="s"):
        d.getdata_and_build()
    elif(inp == "h"):
        while(True):
            system("clear")
            print(colored("DTN HELP PAGE","yellow",attrs=["bold"])+"\n")
            print("The DTN is a digital twin platform for the SDN controller managing the openflow devices. The DTN is platform aimed at providing users the capability to map intentions to automatic configurations, providing behavioural analysis grounds for running \"what-if\" scenarios for different network changes and configurations before physical deployment.\n\n")
            print("configurations.txt- The configuration files for different configuration parameters.\n\n")
            print("log.txt- The log file containing the log level information of the DTN runtime.\n\n")
            print("Configuration Settings - Press C on main menu to view and edit the configuration parameters\n\n")
            print(colored("--------------------------------------------","yellow")+"\n")
            print(colored("Congifuration Parameters (Configuration.txt)","yellow")+"\n")
            print(colored("--------------------------------------------","yellow")+"\n")
            print("1.db_host : The hostname of the neo4j database instance on the system(default localhost)\n")
            print("2.db_port : The port no of the neo4j database instance on the system(default 7687)\n")
            print("3.db_username: The username of the neo4j database\n")
            print("4.db_password : The password of the neo4j database\n")
            print("5.db_database : The name of the neo4j database on the system\n")
            print("6.sdn_host : The hostname where the SDN controller is running(default localhost)\n")
            print("7.sdn_port : The port no of the SDN controller running  on the system(default 8181)\n")
            print("8.sdn_user : The login username of the SDN controller on the system(default onos)\n")
            print("9.sdn_password : The login password of the SDN controller running on the system(default localhost)\n")
            print("10.log_file: The path to save the log file of the DTN.\n")
            print("Press X to go back\n")
            inp = input()
            if(inp == "x"):
                system("clear")
                break
            
    elif(inp == "c"):
        system("vi configurations.txt")
    elif(inp =="e"):
        Logger.close_log()
        exit()
