from interfaces.FlowRules import FlowRules
from interfaces.Hosts import Hosts
from interfaces.Links import Links
from interfaces.Devices import Devices
import time
from os import system
from utils.DBUtil import instance as  DBUtil
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
        self.relations = {}
        self.mac_port = {}                      #To Store The Flow Rules while we build the flow rule KG
        Logger.log_write("DTN Manager Intializing")
        try:
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

    def build_knowledge_graph(self,data):
        Logger.log_write("Entity Node creation started")
        entities = TempUtil.get_entities()

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

                    relation = self.process_relations("Switch", "Switch", all_props)

                    Logger.log_write("Switch Node with properties {"+prop_string+"} created")

            elif (entity == "Flow" or entity == "FlowTable" or entity == "Match" or entity == "Instruction" or entity == "EthAddress" or entity == "In_Port" or entity == "Timeout" or entity == "Priority"):
                
                for flow in data["flows"]["flows"]:
                    if(len(flow["selector"]["criteria"])>=2):
                        all_props = {"groupId": str(flow["groupId"]), "state": flow["state"], "life": str(flow["life"]),
                                     "liveType": flow["liveType"], "lastSeen": str(flow["lastSeen"]),
                                     "packets": str(flow["packets"]), "bytes": str(flow["bytes"]), "id": str(flow["id"]),
                                     "appId": flow["appId"], "priority": str(flow["priority"]), "timeout": str(flow["timeout"]),
                                     "isPermanent": flow["isPermanent"], "deviceId": str(flow["deviceId"][len(flow["deviceId"])-1]),
                                     "tableId": str(flow["tableId"]), "tableName": str(flow["tableName"]),
                                     "type": "\'"+flow["treatment"]["instructions"][0]["type"]+"\'",
                                     "port": "\'"+flow["treatment"]["instructions"][0]["port"]+"\'",
                                     "in_port": str(flow.get("selector",'').get("criteria")[0].get("port")),
                                     "dst": "\'"+flow.get("selector",'').get("criteria")[1].get("mac")+"\'",
                                     "src": "\'"+flow.get("selector",'').get("criteria")[2].get("mac")+"\'"}

                    else:
                        all_props = {"groupId": str(flow["groupId"]), "state": flow["state"], "life": str(flow["life"]),
                                     "liveType": flow["liveType"], "lastSeen": str(flow["lastSeen"]),
                                     "packets": str(flow["packets"]), "bytes": str(flow["bytes"]), "id": str(flow["id"]),
                                     "appId": flow["appId"], "priority": str(flow["priority"]), "timeout": str(flow["timeout"]),
                                     "isPermanent": flow["isPermanent"], "deviceId": str(flow["deviceId"][len(flow["deviceId"])-1]),
                                     "tableId": str(flow["tableId"]), "tableName": str(flow["tableName"]),
                                     "type": "\'"+flow["treatment"]["instructions"][0]["type"]+"\'",
                                     "port": "\'"+flow["treatment"]["instructions"][0]["port"]+"\'",
                                     "in_port": str(flow.get("selector",'').get("criteria")[0].get("ethType")),
                                     "dst": "","src": ""}

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

                            relation = self.process_relations("Switch","FlowTable",all_props)

                            DBUtil.execute_query("MATCH(a:Switch{id:" + all_props["deviceId"] + "}),(b:FlowTable{"+prop_string + "}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Flow"):
                        DBUtil.execute_query("CREATE(n:Flow{"+prop_string+"})")
                        Logger.log_write("Flow with properties {"+prop_string+"} created")

                        relation = self.process_relations("FlowTable", "Flow", all_props)

                        DBUtil.execute_query("MATCH(a:FlowTable{tableId:"+str(all_props["tableId"])+str(all_props["deviceId"])+"}),(b:Flow{id:"+all_props["id"] +"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Instruction"):
                        DBUtil.execute_query("CREATE(n:Instruction{"+prop_string+"})")
                        Logger.log_write("Instruction with properties {"+prop_string+"} created")

                        relation = self.process_relations("Flow","Instruction", all_props)

                        DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Instruction{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                        
                    elif (entity == "Match"):
                        DBUtil.execute_query("CREATE(n:Match{"+prop_string+"})")
                        Logger.log_write("Match with properties {"+prop_string+"} created")

                        relation = self.process_relations("Flow", "Match", all_props)

                        DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Match{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "EthAddress"):
                        if (len(flow["selector"]["criteria"]) >= 2):
                            DBUtil.execute_query("CREATE(n:EthAddress{"+prop_string+"})")
                            Logger.log_write("EthAddress Node with properties {"+prop_string+"} created")

                            relation = self.process_relations("Match", "EthAddress", all_props)
                            DBUtil.execute_query("MATCH(a:Match{id:" + all_props["id"] + "}),(b:EthAddress{id:" + all_props["id"] + "}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "In_Port"):
                        DBUtil.execute_query("CREATE(n:In_Port{"+prop_string+"})")
                        Logger.log_write("In_Port Node with properties {"+prop_string+"} created")

                        relation = self.process_relations("Match", "In_Port", all_props)

                        DBUtil.execute_query("MATCH(a:Match{id:"+ all_props["id"] + "}),(b:In_Port{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Timeout"):
                        DBUtil.execute_query("CREATE(n:Timeout{"+prop_string+"})")
                        Logger.log_write("Timeout Node with properties {"+prop_string+"} created")
                        relation = self.process_relations("Flow", "Timeout", all_props)

                        DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Timeout{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Priority"):
                        DBUtil.execute_query("CREATE(n:Priority{"+prop_string+"})")
                        Logger.log_write("Priority Node with properties {"+prop_string+"} created")
                        relation = self.process_relations("Flow", "Priority", all_props)

                        DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Priority{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

            elif(entity == "Host"):

                props = TempUtil.get_properties(entity)

                for host in data["hosts"]["hosts"]:
                    all_props = {"mac":"\'"+host["mac"]+"\'","vlan":"\'"+host["vlan"]+"\'","innerVlan":"\'"+host["innerVlan"]+"\'","outerTpid":str(host["outerTpid"]),"configured":host["configured"],"suspended":host["suspended"],"switch":str(host["locations"][0]["elementId"][len(host["locations"][0]["elementId"])-1]),"port":host["locations"][0]["port"]}

                    prop_string=""
                    for p in props:
                        prop_string += p +":"+all_props[p]+","

                    prop_string = prop_string[:-1]

                    DBUtil.execute_query("CREATE(n:Host{"+prop_string+"})")
                    Logger.log_write("Host Node with properties {"+prop_string+"} created")

                    relation = self.process_relations("Host", "Switch", all_props)

                    DBUtil.execute_query("MATCH(a:Host{"+prop_string+"}),(b:Switch{id:"+all_props["switch"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
            else:
                DBUtil.execute_query("CREATE(n:"+entity+")")
                relation = self.process_relations(entity,None, all_props)

                Logger.log_write(entity+" Node created")

    def process_relations(self,entity1,entity2,props):
        relations = TempUtil.get_relations()

        relation = ""

        if entity2 is None:
            for rel_map in relations:
                if rel_map["map"][0] == entity1:
                    if entity1 + "_" + rel_map["map"][1] + "_rel" not in self.relations.keys():
                        self.relations[entity1 + "_" + rel_map["map"][1] + "_rel"] = rel_map["map"][2]

                    DBUtil.execute_query("MATCH(a:" + entity1 + "),(b:" + rel_map["map"][1] + ") CREATE (a)-[r:" + rel_map["map"][2] + "]->(b)")

                elif rel_map["map"][1] == entity1:
                    if entity1 + "_" + rel_map["map"][0] + "_rel" not in self.relations.keys():
                        self.relations[entity1 + "_" + rel_map["map"][0] + "_rel"] = rel_map["map"][2]

                    DBUtil.execute_query("MATCH(a:" + entity1 + "),(b:" + rel_map["map"][0] + ") CREATE (b)-[r:" + rel_map["map"][2] + "]->(a)")

        else:
            for rel_map in relations:
                if rel_map["map"][0] == entity1 and rel_map["map"][1] == entity2:
                    relation += rel_map["map"][2]
                    if "Properties" in rel_map.keys():
                        relation += "{"
                        for p in rel_map["Properties"]:
                            relation += p + ":" + props[p] + ","

                        relation = relation[:-1]
                        relation += "}"

                    if (entity1 == "Switch" and entity2 == "Switch"):
                        self.connect_switches(relation)

                        if "switch_switch_rel" not in self.relations.keys():
                            self.relations["switch_switch_rel"] = rel_map["map"][2]

                    if (entity1 == "Switch" and entity2 == "FlowTable"):
                        if "switch_flowtable_rel" not in self.relations.keys():
                            self.relations["switch_flowtable_rel"] = rel_map["map"][2]

                    if (entity1 == "FlowTable" and entity2 == "Flow"):
                        if "flowtable_flow_rel" not in self.relations.keys():
                            self.relations["flowtable_flow_rel"] = rel_map["map"][2]

                    if (entity1 == "Flow" and entity2 == "Instruction"):
                        if "flow_insruction_rel" not in self.relations.keys():
                            self.relations["flow_instruction_rel"] = rel_map["map"][2]

                    if (entity1 == "Flow" and entity2 == "Match"):
                        if "flow_match_rel" not in self.relations.keys():
                            self.relations["flow_match_rel"] = rel_map["map"][2]

                    if (entity1 == "Match" and entity2 == "In_Port"):
                        if "match_inport_rel" not in self.relations.keys():
                            self.relations["match_inport_rel"] = rel_map["map"][2]

                    if (entity1 == "Match" and entity2 == "EthAddress"):
                        if "match_eth_rel" not in self.relations.keys():
                            self.relations["match_eth_rel"] = rel_map["map"][2]

                    if (entity1 == "Flow" and entity2 == "Timeout"):
                        if "flow_timeout_rel" not in self.relations.keys():
                            self.relations["flow_timeout_rel"] = rel_map["map"][2]

                    if (entity1 == "Flow" and entity2 == "Priority"):
                        if "flow_priority_rel" not in self.relations.keys():
                            self.relations["flow_priority_rel"] = rel_map["map"][2]

                    if (entity1 == "Host" and entity2 == "Switch"):
                        if "host_switch_rel" not in self.relations.keys():
                            self.relations["host_switch_rel"] = rel_map["map"][2]

                    break
        return relation


    def execute_policies(self):          #This Functions Reads the policies from template and executes them
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
            print("[",colored(str(datetime.datetime.now()),'blue'),"]",colored(" No defined polices found in template",'red'))
            Logger.log_write("No defined polices found in template")

        for policy in policies:                     #Executing Policies
            print("[",colored(str(datetime.datetime.now()),'blue'),"]",colored(" Executing "+policy["name"]+"\n",'green',attrs=['bold']))
            Logger.log_write("Executing "+policy["name"]+"\n")
            exec("mechanism_class."+policy["deploy"]+"(self.relations)")

    def getdata_and_build(self):
        Logger.log_write("Intial Knowledge Graph Build started")
    
        try:
            while(True):
                switches = self.sw.get_switches()
                flows = self.fr.getFlowRules()
                hosts = self.hosts.getHosts()

                raw_data = {"switches":switches,"flows":flows,"hosts":hosts}        #RAW DATA FETCHED FROM SDN CONTROLLER THROUGH REST API

                DBUtil.execute_query("MATCH(n) DETACH DELETE n")
                Logger.log_write("Old Knowledge Graph cleared")
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mDeleted Old Knowledge Graph...Rebuilding\033[00m")

                DBUtil.execute_query("CREATE(n:" + TempUtil.templateName + ")")

                self.build_knowledge_graph(raw_data)                               #This Function dynamically creates the KG based on Template specifications passed as the argument

                Logger.log_write("Creating and attaching Policies nodes to Knowledge Graph")

                for policy in TempUtil.get_policies():
                    DBUtil.execute_query("CREATE(n:"+policy["name"]+")")
                    DBUtil.execute_query("CREATE(n:"+policy["deploy"]+")")
                    DBUtil.execute_query("MATCH(a:"+policy["name"]+"),(b:"+policy["deploy"]+") CREATE (a)-[r:hasMechanism]->(b)")
                    DBUtil.execute_query("MATCH(a:"+TempUtil.templateName+"),(b:"+policy["name"]+") CREATE (a)-[r:hasPolicy]->(b)")

                Logger.log_write("Attaching Policiy nodes to Knowledge Graph Finished")

                Logger.log_write("Attaching Variable nodes to Knowledge Graph")
                DBUtil.execute_query("MATCH(a:Object),(b:" +TempUtil.templateName+") CREATE (b)-[r:hasVariables]->(a)")
                Logger.log_write("Attaching Variable nodes to Knowledge Graph Finished")

                print("\n[",colored(str(datetime.datetime.now()),'blue'),"]",colored(" Executing Deployed Policies\n",'green',attrs=['bold']))
                Logger.log_write("Executing Deployed Policies")
                self.execute_policies()
                Logger.log_write("Finshed Executing Deployed Policies")
                print("\n[",colored(str(datetime.datetime.now()),'blue'),"]",colored("Finshed Executing Deployed Policies\n",'red',attrs=['bold']))
                
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[92mKnowledge Graph Building Finished...Press Ctrl+C to exit\033[00m\n")
                
                Logger.log_write("KG building completed")
                time.sleep(5)
                print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mClearing Graph....Refreshing\033[00m\n")
                Logger.log_write("Knowledge Graph clearing and refreshing")
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
    print(colored("\n>",attrs=['bold']),end='')
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
