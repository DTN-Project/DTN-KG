import requests

class Hosts:
    def __init__(self,auth):
        self.rest_url = "http://localhost:8181/onos/v1/hosts"
        self.auth = auth

    def getHosts(self):
        response = requests.get(self.rest_url,auth=self.auth)
        response = response.json()

        return response