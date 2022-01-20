from utils.RestUtil import instance as RESTUtil

class Devices:
    def __init__(self):
        self.rest_path = "/onos/v1/devices"

    def get_switches(self):
        response = RESTUtil.invoke_rest_api(self.rest_path)
        return response