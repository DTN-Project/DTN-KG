import re

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
import pickle

from modules.KGDataModeller import KGDataModeller
from modules.MechanismExecutor import MechanismExecutor
from modules.PolicyDeployer import PolicyDeployer

#DTNManager For Defining the Manager Component of the DTN Architecture
class DTNManager:
    def __init__(self):
        self.fr = FlowRules()
        self.sw = Devices()
        self.hosts = Hosts()
        self.links = Links()

        self.relations = {}
        self.mac_port = {}                      #To Store The Flow Rules while we build the flow rule KG
        
        self.kgDataModeller = KGDataModeller(self.links, self.relations)
        self.mechanismExecutor = MechanismExecutor(self.relations)
        self.policyDeployer = PolicyDeployer()

        self.reuse_kg = False

        Logger.log_write("DTN Manager Intializing")
        try:
            Logger.log_write("DTN Manager Initialized")
            
        except Exception as e:
            print(e)
            Logger.log_write("DTN Manager Initialization Failed ["+e+"]")
            Logger.close_log()
            self.graphDB.close()

    def getdata_and_build(self, rebuild_kg=False):
        Logger.log_write("Intial Knowledge Graph Build started")
        try:
            while(True):
                switches = self.sw.get_switches()
                flows = self.fr.getFlowRules()
                hosts = self.hosts.getHosts()

                raw_data = {"switches":switches,"flows":flows,"hosts":hosts}        #RAW DATA FETCHED FROM SDN CONTROLLER THROUGH REST API

                if not self.reuse_kg or rebuild_kg:
                    DBUtil.execute_query("MATCH(n) DETACH DELETE n")
                    Logger.log_write("Old Knowledge Graph cleared")
                    print("[\033[32m"+str(datetime.datetime.now())+"\033[0m]"+"\033[91mDeleted Old Knowledge Graph...Rebuilding\033[00m")

                    DBUtil.execute_query("CREATE(n:" + TempUtil.templateName + ")")
                    if rebuild_kg:
                        self.reuse_kg = False
                

                self.kgDataModeller.build_knowledge_graph(raw_data, self.reuse_kg)                               #This Function dynamically creates the KG based on Template specifications passed as the argument

                print("\n[",colored(str(datetime.datetime.now()),'blue'),"]",colored(" KG updation is completed\n",'green',attrs=['bold']))
                
                self.policyDeployer.deploy_policies()

                Logger.log_write("Attaching Variable nodes to Knowledge Graph")
                DBUtil.execute_query("MATCH(a:Object),(b:" +TempUtil.templateName+") CREATE (b)-[r:hasVariables]->(a)")
                Logger.log_write("Attaching Variable nodes to Knowledge Graph Finished")

                print("\n[",colored(str(datetime.datetime.now()),'blue'),"]",colored(" Executing Deployed Policies\n",'green',attrs=['bold']))
                Logger.log_write("Executing Deployed Policies")
                # self.execute_policies()
                self.mechanismExecutor.execute_mechanisms()
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
        d.reuse_kg = TempUtil.is_shared()
        d.getdata_and_build(True)                   #Initiate the data retrival and KG building process
        
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
