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

    def checkFlowRuleReachability(self,kg_relations):
        #Getting the relations represented in built KG
        host_switch_rel = kg_relations["host_switch_rel"]
        switch_switch_rel = kg_relations["switch_switch_rel"]

        switch_flowtable_rel = kg_relations["switch_flowtable_rel"]
        flowtable_flow_rel = kg_relations["flowtable_flow_rel"]
        flow_match_rel = kg_relations["flow_match_rel"]
        flow_instruction_rel = kg_relations["flow_instruction_rel"]
        match_eth_rel =  kg_relations["match_eth_rel"]
        match_inport_rel = kg_relations["match_inport_rel"]

        # identify the switches to which hosts are connected
        for h1 in self.hosts.getHosts()["hosts"]:
            for h2 in self.hosts.getHosts()["hosts"]:
                q1 = "Match (h1:Host{mac:\'" + h1.get('mac','') + "\'})-[r1:"+host_switch_rel+"]-(s1:Switch) return s1,properties(r1)"
                data1 = DBUtil.execute_query(q1)
                # source mac not found
                if (len(data1) == 0):
                    print(colored("Source Mac-" + h1.get('mac','') + " not found in KG",'red'))

                # store source port, source id

                sourcePort = str(data1[0]['properties(r1)']['port'])
                sourceId = str(data1[0]['s1']['id'])

                q1 = "Match (h2:Host{mac:\'" + h2.get('mac','') + "\'})-[r2:"+host_switch_rel+"]-(s2:Switch) return s2,properties(r2)"
                data1 = DBUtil.execute_query(q1)

                # destination mac not found

                if (len(data1) == 0):
                    print(colored("Destination Mac-" + h2.get('mac','') + " not found in KG",'red'))

                # store destination port, destination id
                destPort = str(data1[0]['properties(r2)']['port'])
                destId = str(data1[0]['s2']['id'])

                switchId = sourceId

                # traverse the KG until
                # 1. We reach the destination switch from source switch or we can not reach the destination switch
                # 2. The flow rules block the packets from source switch
                while (True):
                    # find whether there is a flow rule matching source id and destination id in the current switch's flow table
                    q2 = "MATCH (s1:Switch{id:" + switchId + "})-[hc:"+switch_flowtable_rel+"*]->(f:FlowTable)-[:"+flowtable_flow_rel+"]->(f1:Flow)-[:"+flow_match_rel+"]->(m1:Match)-[:"+match_eth_rel+"]->(e1:EthAddress) where e1.dst="+"\'"+ h2.get('mac','') +"\'"+ " and e1.src="+"\'"+h1.get('mac','')+"\'"+" return f1,m1,e1"
                    data2 = DBUtil.execute_query(q2)
                    # if there is no flow rule in the flow table in the current switch under consideration, return false
                    if (len(data2) == 0):
                        print(colored("No matching flow rule in Switch" + switchId,'red'))
                        break

                    m1_id = str(data2[0]['m1']['id'])
                    # if flow rule exists in the flow table, check the ingress port of the matching entry
                    q3 = "MATCH (m1:Match{id:" + m1_id + "})-[:"+match_inport_rel+"]->(in_port:In_Port{in_port:" + sourcePort + "}) return in_port"
                    data3 = DBUtil.execute_query(q3)
                    # if the ingress port information is missing, return False
                    if (len(data3) == 0):
                        print(colored("For Source:"+h1.get('mac','')+"and Desrination"+h2.get('mac','')+" No matching flow rule in Switch" + switchId,'red'))
                        break

                    # else check the flow rule for matching ingress port, source id and destination id
                    flowId = str(data2[0]['f1']['id'])
                    q4 = "MATCH (f1:Flow{id:" + flowId + "})-[hc:"+flow_instruction_rel+"]->(i1:Instruction) return i1"
                    data4 = DBUtil.execute_query(q4)
                    # if there is no entry available in the flow table, return false
                    if (len(data4) == 0):
                        print(colored("For Source:"+h1.get('mac','')+"and Desrination"+h2.get('mac','')+" No forwarding instruction available in Switch" + switchId,'red'))
                        break

                    # else check the action(type) and the forwarding port
                    out_port = str(data4[0]['i1']['port'])
                    out_type = str(data4[0]['i1']['type'])

                    # if the action is not 'OUTPUT'(forward), then return false
                    if (not (out_type == 'OUTPUT')):
                        print(colored("For Source:"+h1.get('mac','')+"and Desrination"+h2.get('mac','')+" Flow rule instruction in Switch" + switchId + " blocks the packet",'red'))
                        break

                    # stopping condition
                    # 1. when the current switch id is the destination switch id  AND
                    # 2. the output port matches the port to which destination host is connected
                    if (switchId == destId and out_port == destPort):
                        print(colored("Success "+h1.get('mac','')+" reachability with "+h2.get('mac',''),'green'))

                    # since the current switch id is not the destination switch id, check whether there is a link to another switch from
                    # the current switch originating from the OUT_PORT
                    q5 = "MATCH (s1:Switch{id:" + switchId + "})-[r:"+switch_switch_rel+"{sourcePort:" + out_port + "}]-(s2:Switch) return s2,properties(r)"
                    data5 = DBUtil.execute_query(q5)

                    # since the relation is directed, we need to check in the other direction as well
                    if (len(data5) == 0):
                        q5 = "MATCH (s1:Switch{id:" + switchId + "})-[r:"+switch_switch_rel+"{destinationPort:" + out_port + "}]-(s2:Switch) return s2,properties(r)"
                        data5 = DBUtil.execute_query(q5)

                        # there exists no link originating from the current switch from OUT_PORT.
                        # in this case, return false
                        if (len(data5) == 0):
                            print(colored("For Source:"+h1.get('mac','')+"and Desrination"+h2.get('mac','')+"No link origination from Switch" + switchId + " from port " + out_port,'red'))
                            break

                        sourcePort = str(data5[0]['properties(r)']['sourcePort'])

                    else:
                        sourcePort = str(data5[0]['properties(r)']['destinationPort'])

                    # repeat the above steps for the current switch
                    switchId = str(data5[0]['s2']['id'])
