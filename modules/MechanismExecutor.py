from termcolor import colored
from utils.logger import logger as Logger
from utils.TemplateUtils import instance as TempUtil
import datetime

class MechanismExecutor:

    def __init__(self, relations):
        self.relations = relations

    def execute_mechanisms(self):          #This Functions Reads the policies from template and executes them
            Logger.log_write("Executing Template Policies\n")

            mechanisms = TempUtil.get_mechanisms()

            global mechanism_class
            try:
                script=""
                if("shared" in mechanisms["script"]):
                    script = "from templates."+str(mechanisms["script"])+" import Mechanism"
                else:
                    script = "from templates."+str(TempUtil.templateParentDirectory)+"."+str(mechanisms["script"])+" import Mechanism"
                exec(script)
                exec("mechanism_class = Mechanism()")
            except ModuleNotFoundError as e:
                print(e)

            policies = TempUtil.get_policies()

            if policies is None:
                print("[",colored(str(datetime.datetime.now()),'blue'),"]",colored(" No defined polices found in template",'red'))
                Logger.log_write("No defined polices found in template")

            #Executing Policies
            for policy in policies:                     
                print("[",colored(str(datetime.datetime.now()),'blue'),"]",colored(" Executing "+policy["name"]+"\n",'green',attrs=['bold']))
                Logger.log_write("Executing "+policy["name"]+"\n")
                exec("mechanism_class."+policy["deploy"]+"(self.relations)")
