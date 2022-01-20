from interfaces.FlowRules import FlowRules
from interfaces.Hosts import Hosts
from interfaces.Links import Links
from interfaces.Devices import Devices
import time
from os import system
from utils.DBUtil import instance as DBUtil
from pyfiglet import Figlet
from termcolor import colored
from utils.logger import logger as Logger
import datetime
from utils.Configs import Config
from utils.TemplateUtils import instance as TempUtil
import requests
import argparse

#DTNManager For Defining the Manager Component of the DTN Architecture
class DTNManager:
    def __init__(self):
        self.fr = FlowRules()
        self.sw = Devices()
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

    def connect_switches(self,relation):
        links = self.links.getLinks()

        for link in links['links']:
            sourceSwitchId = str(link['src']['device'][len(link['src']['device'])-1])
            sourcePort = str(link['src']['port'])
            destinationSwitchId = str(link['dst']['device'][len(link['dst']['device'])-1])
            destinationPort = str(link['dst']['port'])
            if(len(DBUtil.execute_query("MATCH (a:Switch{id:"+sourceSwitchId+"})-[r:isConnected]-(b:Switch{id:"+destinationSwitchId+"}) return r")) == 0):
                DBUtil.execute_query("MATCH (a:Switch{id:"+sourceSwitchId+"}),(b:Switch{id:"+destinationSwitchId+"}) CREATE (a)-[r:"+relation+"{sourcePort:"+sourcePort+",destinationPort:"+destinationPort+"}]->(b)")
    """
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
    """

    def build_knowledge_graph(self,data):
        Logger.log_write("Entity Node creation started")

        entities = TempUtil.get_entities()
        relations = TempUtil.get_relations()

        for entity in entities:

            if (entity=="Switch"):
                for sw in data["switches"]["devices"]:
                    all_props = {"id":str(sw["id"][len(sw["id"])-1]),"type":sw["type"],"available":sw["available"],"role":sw["role"],"mfr":"\'"+sw["mfr"]+"\'","hw":"\'"+sw["hw"]+"\'","sw":"\'"+sw["sw"]+"\'","serial":str(sw["serial"]),"driver":sw["driver"],"chassisId":str(sw["chassisId"]),"lastUpdate":str(sw["lastUpdate"]),"humanReadableLastUpdate":sw["humanReadableLastUpdate"],"protocol":"\'"+sw["annotations"]["protocol"]+"\'"}
                    
                    props = TempUtil.get_properties(entity)

                    prop_string=""
                    for p in props:
                        prop_string += p+":"+all_props[p]+","

                    prop_string = prop_string[:-1]

                    DBUtil.execute_query("CREATE(n:Switch{"+prop_string+"})")

                    Logger.log_write("Switch Node with properties {"+prop_string+"} created")

                for rel_map in relations:
                    if rel_map["map"][0] == "Switch" and rel_map["map"][1] == "Switch":
                        self.connect_switches(rel_map["map"][2])
                        break

            elif (entity == "Flow" or entity == "FlowTable" or entity == "Match" or entity == "Instruction" or entity == "EthAddress" or entity == "In_Port" or entity == "Timeout" or entity == "Priority"):
                
                for flow in data["flows"]["flows"]:

                    try:
                        all_props = {"groupId": str(flow["groupId"]), "state": flow["state"], "life": str(flow["life"]),
                                     "liveType": flow["liveType"], "lastSeen": str(flow["lastSeen"]),
                                     "packets": str(flow["packets"]), "bytes": str(flow["bytes"]), "id": str(flow["id"]),
                                     "appId": flow["appId"], "priority": str(flow["priority"]), "timeout": str(flow["timeout"]),
                                     "isPermanent": flow["isPermanent"], "deviceId": str(flow["deviceId"][len(flow["deviceId"])-1]),
                                     "tableId": str(flow["tableId"]), "tableName": str(flow["tableName"]),
                                     "instruction_type": "\'"+flow["treatment"]["instructions"][0]["type"]+"\'",
                                     "out_port": "\'"+flow["treatment"]["instructions"][0]["port"]+"\'",
                                     "in_port": str(flow.get("selector", "").get("criteria")[0].get("port")),
                                     "eth_src": "\'"+flow.get("selector").get("criteria")[1].get("mac")+"\'",
                                     "eth_dst": "\'"+flow.get("selector", "").get("criteria")[2].get("mac")+"\'"}

                    except Exception:
                        all_props = {"groupId": str(flow["groupId"]), "state": flow["state"], "life": str(flow["life"]),
                                     "liveType": flow["liveType"], "lastSeen": str(flow["lastSeen"]),
                                     "packets": str(flow["packets"]), "bytes": str(flow["bytes"]),
                                     "id": str(flow["id"]),
                                     "appId": flow["appId"], "priority": str(flow["priority"]),
                                     "timeout": str(flow["timeout"]),
                                     "isPermanent": flow["isPermanent"], "deviceId": str(flow["deviceId"][len(flow["deviceId"])-1]),
                                     "tableId": str(flow["tableId"]), "tableName": str(flow["tableName"]),
                                     "instruction_type": "\'"+flow["treatment"]["instructions"][0]["type"]+"\'",
                                     "out_port": "\'" + flow["treatment"]["instructions"][0]["port"] + "\'",
                                     "in_port": str(flow.get("selector", "").get("criteria")[0].get("ethType"))}

                    props = TempUtil.get_properties(entity)

                    prop_string=""

                    for p in props:
                        if entity == "FlowTable" and p == "tableId":
                            prop_string += p+":"+str(all_props[p])+str(all_props["deviceId"])+","
                            continue

                        prop_string += p+":"+all_props[p]+","

                    prop_string = prop_string[:-1]

                    if (entity == "FlowTable"):
                        if(len(DBUtil.execute_query("MATCH(n:FlowTable{"+prop_string+"}) RETURN n"))==0):
                            DBUtil.execute_query("CREATE(n:FlowTable{"+prop_string+"})")
                            Logger.log_write("FlowTable Node with properties {"+prop_string+"} created")

                            relation = ""
                            for rel_map in relations:
                                if rel_map["map"][0] == "Switch" and rel_map["map"][1] == "FlowTable":
                                    relation += rel_map["map"][2]
                                    if "Properties" in rel_map.keys():
                                        relation += "{"
                                        for p in rel_map["Properties"]:
                                            relation += p + ":" + all_props[p] + ","

                                        relation = relation[:-1]
                                        relation += "}"

                                    DBUtil.execute_query("MATCH(a:Switch{id:" + all_props["deviceId"] + "}),(b:FlowTable{"+prop_string + "}) CREATE (a)-[r:" + relation + "]->(b)")
                                    break

                    elif (entity == "Flow"):
                        DBUtil.execute_query("CREATE(n:Flow{"+prop_string+"})")
                        Logger.log_write("Flow with properties {"+prop_string+"} created")

                        relation = ""
                        for rel_map in relations:
                            if rel_map["map"][0] == "FlowTable" and rel_map["map"][1] == "Flow":
                                relation += rel_map["map"][2]
                                if "Properties" in rel_map.keys():
                                    relation += "{"
                                    for p in rel_map["Properties"]:
                                        relation += p +":"+all_props[p]+","

                                    relation = relation[:-1]
                                    relation += "}"

                                DBUtil.execute_query("MATCH(a:FlowTable{tableId:"+str(all_props["tableId"])+str(all_props["deviceId"])+"}),(b:Flow{id:"+all_props["id"] +"}) CREATE (a)-[r:" + relation + "]->(b)")
                                break

                    elif (entity == "Instruction"):
                        DBUtil.execute_query("CREATE(n:Instruction{"+prop_string+"})")
                        Logger.log_write("Instruction with properties {"+prop_string+"} created")

                        relation = ""
                        for rel_map in relations:
                            if rel_map["map"][0] == "Flow" and rel_map["map"][1] == "Instruction":
                                relation += rel_map["map"][2]
                                if "Properties" in rel_map.keys():
                                    relation += "{"
                                    for p in rel_map["Properties"]:
                                        relation += p +":"+all_props[p]+","

                                    relation = relation[:-1]
                                    relation += "}"

                                DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Instruction{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
                                break

                        
                    elif (entity == "Match"):
                        DBUtil.execute_query("CREATE(n:Match{"+prop_string+"})")
                        Logger.log_write("Match with properties {"+prop_string+"} created")

                        relation = ""
                        for rel_map in relations:
                            if rel_map["map"][0] == "Flow" and rel_map["map"][1] == "Match":
                                relation += rel_map["map"][2]
                                if "Properties" in rel_map.keys():
                                    relation += "{"
                                    for p in rel_map["Properties"]:
                                        relation += p +":"+all_props[p]+","

                                    relation = relation[:-1]
                                    relation += "}"

                                DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Match{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
                                break

                    elif (entity == "EthAddress"):
                        DBUtil.execute_query("CREATE(n:EthAddress{"+prop_string+"})")
                        Logger.log_write("EthAddress Node with properties {"+prop_string+"} created")

                        relation = ""
                        for rel_map in relations:
                            if rel_map["map"][0] == "Match" and rel_map["map"][1] == "EthAddress":
                                relation += rel_map["map"][2]
                                if "Properties" in rel_map.keys():
                                    relation += "{"
                                    for p in rel_map["Properties"]:
                                        relation += p + ":" + all_props[p] + ","

                                    relation = relation[:-1]
                                    relation += "}"

                                DBUtil.execute_query("MATCH(a:Match{id:"+ all_props["id"] + "}),(b:EthAddress{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
                                break

                    elif (entity == "In_Port"):
                        DBUtil.execute_query("CREATE(n:In_Port{"+prop_string+"})")
                        Logger.log_write("In_Port Node with properties {"+prop_string+"} created")

                        relation = ""
                        for rel_map in relations:
                            if rel_map["map"][0] == "Match" and rel_map["map"][1] == "In_Port":
                                relation += rel_map["map"][2]
                                if "Properties" in rel_map.keys():
                                    relation += "{"
                                    for p in rel_map["Properties"]:
                                        relation += p +":"+all_props[p]+","

                                    relation = relation[:-1]
                                    relation += "}"

                                DBUtil.execute_query("MATCH(a:Match{id:"+ all_props["id"] + "}),(b:In_Port{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
                                break

                    elif (entity == "Timeout"):
                        DBUtil.execute_query("CREATE(n:Timeout{"+prop_string+"})")
                        Logger.log_write("Timeout Node with properties {"+prop_string+"} created")

                        relation = ""
                        for rel_map in relations:
                            if rel_map["map"][0] == "Flow" and rel_map["map"][1] == "Timeout":
                                relation += rel_map["map"][2]
                                if "Properties" in rel_map.keys():
                                    relation += "{"
                                    for p in rel_map["Properties"]:
                                        relation += p +":"+all_props[p]+","

                                    relation = relation[:-1]
                                    relation += "}"

                                DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Timeout{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
                                break

                    elif (entity == "Priority"):
                        DBUtil.execute_query("CREATE(n:Priority{"+prop_string+"})")
                        Logger.log_write("Priority Node with properties {"+prop_string+"} created")

                        relation = ""
                        for rel_map in relations:
                            if rel_map["map"][0] == "Flow" and rel_map["map"][1] == "Priority":
                                relation += rel_map["map"][2]
                                if "Properties" in rel_map.keys():
                                    relation += "{"
                                    for p in rel_map["Properties"]:
                                        relation += p +":"+all_props[p]+","

                                    relation = relation[:-1]
                                    relation += "}"

                                DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Priority{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
                                break

            elif(entity == "Host"):

                props = TempUtil.get_properties(entity)

                for host in data["hosts"]["hosts"]:
                    all_props = {"mac":"\'"+host["mac"]+"\'","vlan":"\'"+host["vlan"]+"\'","innerVlan":"\'"+host["innerVlan"]+"\'","outerTpid":str(host["outerTpid"]),"configured":host["configured"],"suspended":host["suspended"],"connected_switch":str(host["locations"][0]["elementId"][len(host["locations"][0]["elementId"])-1]),"connected_port":host["locations"][0]["port"]}

                    prop_string=""
                    for p in props:
                        prop_string += p +":"+all_props[p]+","

                    prop_string = prop_string[:-1]

                    DBUtil.execute_query("CREATE(n:Host{"+prop_string+"})")
                    Logger.log_write("Host Node with properties {"+prop_string+"} created")

                    relation = ""
                    for rel_map in relations:
                        if rel_map["map"][0] == "Host" and rel_map["map"][1] == "Switch":
                            relation += rel_map["map"][2]
                            if "Properties" in rel_map.keys():
                                relation += "{"
                                for p in rel_map["Properties"]:
                                    relation += p + ":" + all_props[p] + ","

                                relation = relation[:-1]
                                relation += "}"

                            DBUtil.execute_query("MATCH(a:Host{"+prop_string+"}),(b:Switch{id:"+all_props["connected_switch"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
                            break
            else:
                DBUtil.execute_query("CREATE(n:"+entity+")")
                Logger.log_write(entity+" Node created")

                for rel_map in relations:
                    if rel_map["map"][0] == entity:
                        DBUtil.execute_query("MATCH(a:"+entity+"),(b:"+rel_map["map"][1]+") CREATE (a)-[r:" + rel_map["map"][2] + "]->(b)")

                    elif rel_map["map"][1] == entity:
                        DBUtil.execute_query("MATCH(a:"+entity+"),(b:"+rel_map["map"][0]+") CREATE (b)-[r:" + rel_map["map"][2] + "]->(a)")

    def execute_policies(self):               #This Functions Reads the policies from template and executes them
        Logger.log_write("Executing Template Policices\n")

        mechanisms = TempUtil.get_mechanisms()

        global mechanism_class
        try:
            exec("from templates."+str(TempUtil.templateParentDirectory)+"."+str(mechanisms["script"])+" import Mechanism")
            exec("mechanism_class = Mechanism()")
        except ModuleNotFoundError as e:
            print(e)

        policies = TempUtil.get_policies()

        if policies is None:
            print(colored("No defined polices found in template",'red'))
            Logger.log_write("No defined polices found in template")

        for policy in policies:                     #Executing Policies
            print("Executing "+policy["name"]+"\n")
            Logger.log_write("Executing "+policy["name"]+"\n")
            exec("mechanism_class."+policy["deploy"]+"()")

    def getdata_and_build(self):
        Logger.log_write("Intial KG Build started")
    
        try:
            while(True):
                switches = self.sw.get_switches()
                flows = self.fr.getFlowRules()
                hosts = self.hosts.getHosts()

                raw_data = {"switches":switches,"flows":flows,"hosts":hosts}        #RAW DATA FETCHED FROM SDN CONTROLLER THROUGH REST API

                DBUtil.execute_query("MATCH(n) DETACH DELETE n")
                Logger.log_write("Old graph cleared")
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mDeleted Old Graph...Rebuilding\033[00m")

                print("Tempname:", TempUtil.templateName)
                DBUtil.execute_query("CREATE(n:" + TempUtil.templateName + ")")

                self.build_knowledge_graph(raw_data)                               #This Function dynamically creates the KG based on Template specifications passed as the argument

                Logger.log_write("Creating and attaching Policies nodes to KG")

                for policy in TempUtil.get_policies():
                    DBUtil.execute_query("CREATE(n:"+policy["name"]+")")
                    DBUtil.execute_query("CREATE(n:"+policy["deploy"]+")")
                    DBUtil.execute_query("MATCH(a:"+policy["name"]+"),(b:"+policy["deploy"]+") CREATE (a)-[r:hasMechanism]->(b)")
                    DBUtil.execute_query("MATCH(a:"+TempUtil.templateName+"),(b:"+policy["name"]+") CREATE (a)-[r:hasPolicy]->(b)")

                Logger.log_write("Attaching Policiy nodes to KG Finished")

                Logger.log_write("Attaching Variable nodes to KG")
                DBUtil.execute_query("MATCH(a:Object),(b:" +TempUtil.templateName+") CREATE (b)-[r:hasVariables]->(a)")
                Logger.log_write("Attaching Variable nodes to KG Finished")

                print(colored("Executing Deployed Policies\n",'green'))
                self.execute_policies()
                print(colored("Finshed Executing Deployed Policies\n", 'red'))

                #self.build_flowrule_reachability()
                
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[92mKG Building Finished...Press Ctrl+C to exit\033[00m\n")
                
                Logger.log_write("KG building completed")
                time.sleep(5)
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mClearing Graph....Refreshing\033[00m\n")
                Logger.log_write("KG clearing and refreshing")
                system('clear')
        except Exception as e:
            print(e)
            print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mClosing\033[00m\n")
            Logger.log_write("Closing connections")
            Logger.close_log()
            self.graphDB.close()


template_file = None

parser = argparse.ArgumentParser()

parser.add_argument("--template", "-t", help="set the Knowledge Graph template")  #Option for specifying the template file

args = parser.parse_args()

if args.template:
    template_file = args.template

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
        TempUtil.load(template_file)            #Initialize the template file and load teh data using helper util class
        d.getdata_and_build()                   #Initiate the data retrival and KG building process
        
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
