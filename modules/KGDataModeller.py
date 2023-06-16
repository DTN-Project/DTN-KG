from utils.logger import logger as Logger
from utils.TemplateUtils import instance as TempUtil
from utils.DBUtil import instance as  DBUtil
import re
from interfaces.Links import Links
from termcolor import colored
import datetime

class KGDataModeller:

    def __init__(self, links, relations):
        self.links = links
        self.relations = relations

    
    def build_knowledge_graph(self, data, reuse_kg=False):
        Logger.log_write("Entity Node creation started")
        entities = TempUtil.get_entities()

        for entity in entities:
            if (entity=="Switch"):
                for sw in data["switches"]["devices"]:
                    id = "\'"+str(re.split("of:",sw["id"])[1])+"\'"
                    all_props = {"id":id,"type":sw["type"],"available":sw["available"],"role":sw["role"],"mfr":"\'"+sw["mfr"]+"\'","hw":"\'"+sw["hw"]+"\'","sw":"\'"+sw["sw"]+"\'","serial":str(sw["serial"]),"driver":sw["driver"],"chassisId":str(sw["chassisId"]),"lastUpdate":str(sw["lastUpdate"]),"humanReadableLastUpdate":sw["humanReadableLastUpdate"],"protocol":"\'"+sw["annotations"]["protocol"]+"\'"}
                    
                    props = TempUtil.get_properties(entity)

                    prop_string=""
                    for p in props:
                        prop_string += p+":"+all_props[p]+","

                    prop_string = prop_string[:-1]
                    
                    if not reuse_kg:
                        DBUtil.execute_query("CREATE(n:Switch{"+prop_string+"})")
                        Logger.log_write("Switch Node with properties {"+prop_string+"} created")

                    else:
                        properties = ""
                        for p in props:
                            properties += "n."+p+"="+all_props[p]+","
                        properties = properties[:-1]
                        DBUtil.execute_query("MATCH(n:Switch{id:"+ id +"}) set "+ properties + " return n")
                        Logger.log_write("Switch Node with properties {"+properties+"} updated")

                    relation = self.process_relations("Switch", "Switch", all_props, reuse_kg)

                    

            elif (entity == "Flow" or entity == "FlowTable" or entity == "Match" or entity == "Instruction" or entity == "EthAddress" or entity == "In_Port" or entity == "Timeout" or entity == "Priority"):
                
                for flow in data["flows"]["flows"]:
                    if(len(flow["selector"]["criteria"])>=2):
                        all_props = {"groupId": str(flow["groupId"]), "state": flow["state"], "life": str(flow["life"]),
                                     "liveType": flow["liveType"], "lastSeen": str(flow["lastSeen"]),
                                     "packets": str(flow["packets"]), "bytes": str(flow["bytes"]), "id": str(flow["id"]),
                                     "appId": flow["appId"], "priority": str(flow["priority"]), "timeout": str(flow["timeout"]),
                                     "isPermanent": flow["isPermanent"], "deviceId":str(re.split("of:",flow["deviceId"])[1]),
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
                                     "isPermanent": flow["isPermanent"], "deviceId": str(re.split("of:",flow["deviceId"])[1]),
                                     "tableId": str(flow["tableId"]), "tableName": str(flow["tableName"]),
                                     "type": "\'"+flow["treatment"]["instructions"][0]["type"]+"\'",
                                     "port": "\'"+flow["treatment"]["instructions"][0]["port"]+"\'",
                                     "in_port": str(flow.get("selector",'').get("criteria")[0].get("ethType")),
                                     "dst": "","src": ""}

                    props = TempUtil.get_properties(entity)

                    prop_string=""

                    for p in props:
                        if entity == "FlowTable" and p == "tableId":
                            prop_string += p+":"+"\'"+str(all_props[p])+str(all_props["deviceId"])+"\'"+","
                            continue

                        prop_string += p+":"+all_props[p]+","

                    prop_string = prop_string[:-1]

                    if (entity == "FlowTable"):
                        if(len(DBUtil.execute_query("MATCH(n:FlowTable{"+prop_string+"}) RETURN n"))==0):
                            if not reuse_kg:
                                DBUtil.execute_query("CREATE(n:FlowTable{"+prop_string+"})")
                                Logger.log_write("FlowTable Node with properties {"+prop_string+"} created")
                            
                            else:
                                properties = ""
                                for p in props:
                                    properties += "n."+p+"="+all_props[p]+","
                                properties = properties[:-1]
                                DBUtil.execute_query("MATCH(n:FlowTable{id:"+ id +"}) set "+ properties + " return n")
                                Logger.log_write("FlowTable node with properties {"+properties+"} updated")

                            relation = self.process_relations("Switch","FlowTable",all_props, reuse_kg)
                            
                            if not reuse_kg:
                                DBUtil.execute_query("MATCH(a:Switch{id:"+"\'"+all_props["deviceId"]+"\'"+"}),(b:FlowTable{"+prop_string+"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Flow"):
                        if not reuse_kg:
                            DBUtil.execute_query("CREATE(n:Flow{"+prop_string+"})")
                            Logger.log_write("Flow with properties {"+prop_string+"} created")
                        
                        else:
                            properties = ""
                            for p in props:
                                properties += "n."+p+"="+all_props[p]+","
                            properties = properties[:-1]
                            DBUtil.execute_query("MATCH(n:Flow{id:"+ id +"}) set "+ properties + " return n")
                            Logger.log_write("Flow node with properties {"+properties+"} updated")

                        relation = self.process_relations("FlowTable", "Flow", all_props, reuse_kg)
                        
                        if not reuse_kg:
                            DBUtil.execute_query("MATCH(a:FlowTable{tableId:"+"\'"+str(all_props["tableId"])+str(all_props["deviceId"])+"\'"+"}),(b:Flow{id:"+all_props["id"] +"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Instruction"):
                        if not reuse_kg:
                            DBUtil.execute_query("CREATE(n:Instruction{"+prop_string+"})")
                            Logger.log_write("Instruction with properties {"+prop_string+"} created")
                        else:
                            properties = ""
                            for p in props:
                                properties += "n."+p+"="+all_props[p]+","
                            properties = properties[:-1]
                            DBUtil.execute_query("MATCH(n:Instruction{id:"+ id +"}) set "+ properties + " return n")
                            Logger.log_write("Instruction node with properties {"+properties+"} updated")

                        relation = self.process_relations("Flow","Instruction", all_props, reuse_kg)

                        if not reuse_kg:
                            DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Instruction{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                        
                    elif (entity == "Match"):
                        if not reuse_kg:
                            DBUtil.execute_query("CREATE(n:Match{"+prop_string+"})")
                            Logger.log_write("Match with properties {"+prop_string+"} created")
                        else:
                            properties = ""
                            for p in props:
                                properties += "n."+p+"="+all_props[p]+","
                            properties = properties[:-1]
                            DBUtil.execute_query("MATCH(n:Match{id:"+ id +"}) set "+ properties + " return n")
                            Logger.log_write("Match node with properties {"+properties+"} updated")

                        relation = self.process_relations("Flow", "Match", all_props, reuse_kg)

                        if not reuse_kg:
                            DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Match{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "EthAddress"):
                        if (len(flow["selector"]["criteria"]) >= 2):
                            if not reuse_kg:
                                DBUtil.execute_query("CREATE(n:EthAddress{"+prop_string+"})")
                                Logger.log_write("EthAddress Node with properties {"+prop_string+"} created")
                            else:
                                properties = ""
                                for p in props:
                                    properties += "n."+p+"="+all_props[p]+","
                                properties = properties[:-1]
                                DBUtil.execute_query("MATCH(n:EthAddress{id:"+ id +"}) set "+ properties + " return n")
                                Logger.log_write("EthAddress node with properties {"+properties+"} updated")

                            relation = self.process_relations("Match","EthAddress", all_props, reuse_kg)

                            if not reuse_kg:
                                DBUtil.execute_query("MATCH(a:Match{id:" + all_props["id"] + "}),(b:EthAddress{id:" + all_props["id"] + "}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "In_Port"):
                        if not reuse_kg:
                            DBUtil.execute_query("CREATE(n:In_Port{"+prop_string+"})")
                            Logger.log_write("In_Port Node with properties {"+prop_string+"} created")
                        else:
                            properties = ""
                            for p in props:
                                properties += "n."+p+"="+all_props[p]+","
                            properties = properties[:-1]
                            DBUtil.execute_query("MATCH(n:In_Port{id:"+ id +"}) set "+ properties + " return n")
                            Logger.log_write("In_Port node with properties {"+properties+"} updated")

                        relation = self.process_relations("Match", "In_Port", all_props, reuse_kg)
                        
                        if not reuse_kg:
                            DBUtil.execute_query("MATCH(a:Match{id:"+ all_props["id"] + "}),(b:In_Port{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Timeout"):
                        if not reuse_kg:
                            DBUtil.execute_query("CREATE(n:Timeout{"+prop_string+"})")
                            Logger.log_write("Timeout Node with properties {"+prop_string+"} created")
                        else:
                            properties = ""
                            for p in props:
                                properties += "n."+p+"="+all_props[p]+","
                            properties = properties[:-1]
                            DBUtil.execute_query("MATCH(n:Timeout{id:"+ id +"}) set "+ properties + " return n")
                            Logger.log_write("Timeout node with properties {"+properties+"} updated")
                        
                        relation = self.process_relations("Flow", "Timeout", all_props, reuse_kg)

                        if not reuse_kg:
                            DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Timeout{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

                    elif (entity == "Priority"):
                        if not reuse_kg:
                            DBUtil.execute_query("CREATE(n:Priority{"+prop_string+"})")
                            Logger.log_write("Priority Node with properties {"+prop_string+"} created")
                        else:
                            properties = ""
                            for p in props:
                                properties += "n."+p+"="+all_props[p]+","
                            properties = properties[:-1]
                            DBUtil.execute_query("MATCH(n:Priority{id:"+ id +"}) set "+ properties + " return n")
                            Logger.log_write("Priority node with properties {"+properties+"} updated")
                        
                        relation = self.process_relations("Flow", "Priority", all_props, reuse_kg)

                        if not reuse_kg:
                            DBUtil.execute_query("MATCH(a:Flow{id:"+ all_props["id"] + "}),(b:Priority{id:" +all_props["id"]+"}) CREATE (a)-[r:" + relation + "]->(b)")

            elif(entity == "Host"):

                props = TempUtil.get_properties(entity)

                for host in data["hosts"]["hosts"]:
                    switch_id = "\'" + str(re.split("of:", host["locations"][0]["elementId"])[1])+ "\'"
                    all_props = {"mac":"\'"+host["mac"]+"\'","vlan":"\'"+host["vlan"]+"\'","innerVlan":"\'"+host["innerVlan"]+"\'","outerTpid":str(host["outerTpid"]),"configured":host["configured"],"suspended":host["suspended"],"switch":switch_id,"port":host["locations"][0]["port"]}

                    prop_string=""
                    for p in props:
                        prop_string += p +":"+all_props[p]+","

                    prop_string = prop_string[:-1]

                    if not reuse_kg:
                        DBUtil.execute_query("CREATE(n:Host{"+prop_string+"})")
                        Logger.log_write("Host Node with properties {"+prop_string+"} created")
                    else:
                        properties = ""
                        for p in props:
                            properties += "n."+p+"="+all_props[p]+","
                        properties = properties[:-1]
                        DBUtil.execute_query("MATCH(n:Host{id:"+ id +"}) set "+ properties + " return n")
                        Logger.log_write("Host node with properties {"+properties+"} updated")
                        
                    relation = self.process_relations("Host", "Switch", all_props, reuse_kg)

                    if not reuse_kg:
                        DBUtil.execute_query("MATCH(a:Host{"+prop_string+"}),(b:Switch{id:"+all_props["switch"]+"}) CREATE (a)-[r:" + relation + "]->(b)")
            else:
                if not reuse_kg:
                    DBUtil.execute_query("CREATE(n:"+entity+")")
                    Logger.log_write(entity+" Node created")

                relation = self.process_relations(entity,None, all_props, reuse_kg)
            

    def connect_switches(self,relation):
        links = self.links.getLinks()

        for link in links['links']:
            sourceSwitchId = "\'" + str(re.split("of:", link['src']['device'])[1])+ "\'"
            sourcePort = str(link['src']['port'])
            destinationSwitchId = "\'" + str(re.split("of:", link['dst']['device'])[1])+ "\'"
            destinationPort = str(link['dst']['port'])
            if(len(DBUtil.execute_query("MATCH (a:Switch{id:"+sourceSwitchId+"})-[r:isConnected]-(b:Switch{id:"+destinationSwitchId+"}) return r")) == 0):
                DBUtil.execute_query("MATCH (a:Switch{id:"+sourceSwitchId+"}),(b:Switch{id:"+destinationSwitchId+"}) CREATE (a)-[r:"+relation+"{sourcePort:"+sourcePort+",destinationPort:"+destinationPort+"}]->(b)")
    
    def process_relations(self,entity1,entity2,props, reuse_kg):
        relations = TempUtil.get_relations()

        relation = ""

        if entity2 is None:
            for rel_map in relations:
                if rel_map["map"][0] == entity1:
                    if entity1 + "_" + rel_map["map"][1] + "_rel" not in self.relations.keys():
                        self.relations[entity1 + "_" + rel_map["map"][1] + "_rel"] = rel_map["map"][2]

                    if not reuse_kg:
                        DBUtil.execute_query("MATCH(a:" + entity1 + "),(b:" + rel_map["map"][1] + ") CREATE (a)-[r:" + rel_map["map"][2] + "]->(b)")

                elif rel_map["map"][1] == entity1:
                    if entity1 + "_" + rel_map["map"][0] + "_rel" not in self.relations.keys():
                        self.relations[entity1 + "_" + rel_map["map"][0] + "_rel"] = rel_map["map"][2]

                    if not reuse_kg:
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