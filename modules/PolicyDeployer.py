from utils.logger import logger as Logger
from utils.TemplateUtils import instance as TempUtil
from utils.DBUtil import instance as  DBUtil

class PolicyDeployer:

    def __init__(self):
        pass
        # self.reuse_kg = TempUtil.is_shared()

    def deploy_policies(self):
        Logger.log_write("Creating and attaching Policies nodes to Knowledge Graph")

        for policy in TempUtil.get_policies():
            DBUtil.execute_query("CREATE(n:"+policy["name"]+")")
            DBUtil.execute_query("CREATE(n:"+policy["deploy"]+")")
            DBUtil.execute_query("MATCH(a:"+policy["name"]+"),(b:"+policy["deploy"]+") CREATE (a)-[r:hasMechanism]->(b)")
            DBUtil.execute_query("MATCH(a:"+TempUtil.templateName+"),(b:"+policy["name"]+") CREATE (a)-[r:hasPolicy]->(b)")

        Logger.log_write("Attaching Policy nodes to Knowledge Graph Finished")