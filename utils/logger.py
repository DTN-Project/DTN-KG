import datetime
from utils.Configs import Config

class Logger:
    def __init__(self):
        self.log_file = open(Config.log_file,"a")
        
    def log_write(self,msg):
        self.log_file.write("["+str(datetime.datetime.now())+"]"+msg+"\n")

    def log_clear(self):
        self.log_file.truncate(0)

    def close_log(self):
        self.log_file.close()

logger = Logger()
