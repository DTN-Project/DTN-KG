from utils.RestUtil import instance as RESTUtil

class FlowRules:
    def __init__(self):
        self.rest_path = "/onos/v1/flows"
    
    def getFlowRules(self):
        response = RESTUtil.invoke_rest_api(self.rest_path)
        return response


