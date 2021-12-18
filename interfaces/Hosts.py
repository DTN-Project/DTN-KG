from utils.RestUtil import instance as RESTUtil

class Hosts:
    def __init__(self):
        self.rest_path = "/onos/v1/hosts"

    def getHosts(self):
        response = RESTUtil.invoke_rest_api(self.rest_path)
        return response