import requests

class Links:
    def __init__(self,auth):
        self.rest_url = "http://localhost:8181/onos/v1/links"
        self.auth = auth

    def getLinks(self):
        response = requests.get(self.rest_url,auth=self.auth)
        response = response.json()

        return response
    
    def getLinksOriginating(self, sourceId):
        response = requests.get(self.rest_url+"?device="+sourceId,auth=self.auth)
        response = response.json()

        return response