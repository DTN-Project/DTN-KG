from neo4j import GraphDatabase

class HostReachability:
    def __init__(self,user,pwd):
        try:
            self.graphDB = GraphDatabase.driver("bolt://localhost:7687", auth=(user, pwd))
            print("DB Intialized")
            
        except Exception as e:
            print(e)
    
    def check_reachability(self, source_mac, dest_mac):
        with self.graphDB.session(database="dtnkg") as graphDB_Session:
            #identify the switches to which hosts are connected
            q1 = "Match (h1:Host{id:\""+source_mac+"\"})-[r1:isConnected]-(s1:Switch) return s1,properties(r1)"
            data1 = graphDB_Session.run(q1).data()
            #source mac not found
            if(len(data1)==0):
                return False, "Source Mac-"+source_mac+" not found in KG"

            #store source port, source id
            sourcePort = str(data1[0]['properties(r1)']['Port'])
            sourceId = str(data1[0]['s1']['id'])

            q1 = "Match (h2:Host{id:\""+dest_mac+"\"})-[r2:isConnected]-(s2:Switch) return s2,properties(r2)"
            data1 = graphDB_Session.run(q1).data()
            #destination mac not found
            if(len(data1)==0):
                return False, "Destination Mac-"+dest_mac+" not found in KG"
            
            #store destination port, destination id
            destPort = str(data1[0]['properties(r2)']['Port'])
            destId = str(data1[0]['s2']['id'])
            
            switchId = sourceId
            # traverse the KG until 
            # 1. We reach the destination switch from source switch or we can not reach the destination switch
            # 2. The flow rules block the packets from source switch
            while(True):
                # find whether there is a flow rule matching source id and destination id in the current switch's flow table
                q2 = "MATCH (s1:Switch{id:"+switchId+"})-[hc:hasComponent*]->(f1:Flow)-[:hasComponent]->(m1:Match)-[:hasComponent]->(e1:EthAddress) where e1.dst='00000000000"+destId+"' and e1.src='00000000000"+sourceId+"' return f1,m1,e1"
                data2 = graphDB_Session.run(q2).data()
                #if there is no flow rule in the flow table in the current switch under consideration, return false
                if(len(data2) == 0):
                    return False, "No matching flow rule in Switch"+switchId
                m1_id = str(data2[0]['m1']['id'])
                #if flow rule exists in the flow table, check the ingress port of the matching entry
                q3 = "MATCH (m1:Match{id:"+m1_id+"})-[:hasComponent]->(in_port:In_Port{in_port:"+sourcePort+"}) return in_port"
                data3 = graphDB_Session.run(q3).data()
                #if the ingress port information is missing, return False
                if(len(data3) == 0):
                    return False, "No matching flow rule in Switch"+switchId
                
                #else check the flow rule for matching ingress port, source id and destination id
                flowId = str(data2[0]['f1']['id'])
                q4 = "MATCH (f1:Flow{id:"+flowId+"})-[hc:hasComponent]->(i1:Instruction) return i1"
                data4 = graphDB_Session.run(q4).data()
                #if there is no entry available in the flow table, return false
                if(len(data4) == 0):
                    return False, "No forwarding instruction available in Switch"+switchId

                #else check the action(type) and the forwarding port
                out_port = str(data4[0]['i1']['port'])
                out_type = str(data4[0]['i1']['type'])
                
                #if the action is not 'OUTPUT'(forward), then return false
                if(not(out_type == 'OUTPUT')):
                    return False, "Flow rule instruction in Switch"+switchId+" blocks the packet"

                # stopping condition 
                # 1. when the current switch id is the destination switch id  AND
                # 2. the output port matches the port to which destination host is connected
                if(switchId == destId and out_port == destPort):
                    return True, "Success"
                
                # since the current switch id is not the destination switch id, check whether there is a link to another switch from 
                # the current switch originating from the OUT_PORT
                q5 = "MATCH (s1:Switch{id:"+switchId+"})-[r:isConnected{SrcPort:"+out_port+"}]-(s2:Switch) return s2,properties(r)"
                data5 = graphDB_Session.run(q5).data()

                #since the relation is directed, we need to check in the other direction as well
                if(len(data5)==0):
                    q5 = "MATCH (s1:Switch{id:"+switchId+"})-[r:isConnected{DstPort:"+out_port+"}]-(s2:Switch) return s2,properties(r)"
                    data5 = graphDB_Session.run(q5).data()

                    # there exists no link originating from the current switch from OUT_PORT.
                    # in this case, return false
                    if(len(data5) == 0):
                        return False, "No link origination from Switch"+switchId+" from port "+out_port
                    
                    sourcePort = str(data5[0]['properties(r)']['SrcPort'])
                
                else:
                    sourcePort = str(data5[0]['properties(r)']['DstPort'])
                
                #repeat the above steps for the current switch
                switchId = str(data5[0]['s2']['id'])


hr = HostReachability("neo4j","password")
is_reachable,reason = hr.check_reachability("00:00:00:00:00:03","00:00:00:00:00:01")
if(is_reachable):
    print(f"Is reachable - {is_reachable}")
else:
    print(f"Is reachable - {is_reachable} - Reason - {reason}")

is_reachable,reason = hr.check_reachability("00:00:00:00:00:01","00:00:00:00:00:03")
if(is_reachable):
    print(f"Is reachable - {is_reachable}")
else:
    print(f"Is reachable - {is_reachable} - Reason - {reason}")

is_reachable,reason = hr.check_reachability("00:00:00:00:00:04","00:00:00:00:00:01")
if(is_reachable):
    print(f"Is reachable - {is_reachable}")
else:
    print(f"Is reachable - {is_reachable} - Reason - {reason}")