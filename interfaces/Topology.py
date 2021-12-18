from utils.RestUtil import instance as RESTUtil

class Topology:
    def __init__(self,auth):
        self.rest_url = "/onos/v1/topology"
        self.auth = auth

    def getTopology(self):
        response = requests.get(self.rest_url,auth=self.auth)
        response = response.json()

        return response


