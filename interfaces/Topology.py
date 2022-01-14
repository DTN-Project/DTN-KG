from utils.RestUtil import instance as RESTUtil

class Topology:
    def __init__(self):
        self.rest_path = "/onos/v1/topology"

    def getTopology(self):
        response = RESTUtil.invoke_rest_api(self.rest_url)
        return response


