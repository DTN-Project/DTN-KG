import requests
from requests.auth import HTTPBasicAuth
from utils.Configs import Config

class RestUtil:

    REST_AUTH = None

    def authenticate_rest_api(self):
        try:
            self.REST_AUTH = HTTPBasicAuth(Config.sdn_user,Config.sdn_password)
            print("REST authentication successful..")
            return True
        except Exception:
            raise Exception

    def get_auth_session(self):
        try:
            if not self.REST_AUTH:
                self.authenticate_rest_api()
            return self.REST_AUTH
        
        except Exception:
            raise Exception
    
    def invoke_rest_api(self, rest_path):
        try:
            auth = self.get_auth_session()
            rest_url = "http://"+Config.sdn_host+":"+Config.sdn_port+rest_path
            response = requests.get(rest_url, auth=auth)
            return response.json()
        
        except Exception:
            raise Exception

instance = RestUtil()