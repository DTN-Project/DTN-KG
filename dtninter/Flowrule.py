import requests
from requests.auth import HTTPBasicAuth
import json
import datetime
import time
import os

class Flowrule:
    def __init__(self,auth):
        self.rest_url = "http://localhost:8181/onos/v1/flows"
        self.auth = auth

    def getFlowRules(self):
        response = requests.get(self.rest_url,auth=self.auth)
        response = response.json()

        return response


