from utils.DBUtil import instance as DBUtil

class HostReachability_KG:

    def __init__(self):
        self.query = ""

    def checkReachability(self,src_mac,dst_mac,h1_mac,h2_mac):
        self.query = "MATCH frpath = (h1:FRHost)-[:isConnected]-(s1:FRSwitch)-[r:hasPath*{src_mac:\""+src_mac+"\",dst_mac:\""+dst_mac+"\"}]-(s2:FRSwitch)-[:isConnected]-(h2:FRHost) WHERE h1.id=\""+h1_mac+"\" AND h2.id=\""+h2_mac+"\" RETURN frpath"

        response = DBUtil.execute_query(self.query)

        if(len(response)==0):
            return False

        else:
            return True


hr_kg = HostReachability_KG()

src_mac = input("Enter Source MAC Address")
dst_mac = input("Enter Destination MAC Address")

h1_mac = src_mac
h2_mac = dst_mac

if(hr_kg.checkReachability(src_mac,dst_mac,h1_mac,h2_mac) or hr_kg.checkReachability(dst_mac,src_mac,h1_mac,h2_mac)):
    print("\33[42m[OK]\33[0m \33[4m"+dst_mac+" is reachable from "+src_mac+" based on the flow rules in switches\33[0m\n")
else:
    print("\33[41m[FAIL]\33[0m \33[91m"+dst_mac+" is not reachable from "+src_mac+" based on the flow rules in switches\33[0m\n")
        
