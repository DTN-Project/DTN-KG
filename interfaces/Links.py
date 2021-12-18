from utils.RestUtil import instance as RESTUtil

class Links:
    def __init__(self):
        self.rest_path = "/onos/v1/links"

    def getLinks(self):
        response = RESTUtil.invoke_rest_api(self.rest_path)
        return response
    
    def getLinksOriginating(self, sourceId):
        response = RESTUtil.invoke_rest_api(self.rest_path+"?device="+sourceId)
        return response