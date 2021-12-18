from neo4j import GraphDatabase
from utils.Configs import Config

class DBUtil:

    GRAPH_DB_SESSION = None

    def connect_to_db(self):
        try:
            connection_string = "bolt://"+Config.db_host+":"+Config.db_port
            self.GRAPH_DB_SESSION = GraphDatabase.driver(connection_string, auth=(Config.db_user, Config.db_paswword))
            print("DB connected..")
            return True
        
        except Exception:
            raise Exception
    
    def get_db_connection(self):
        try:
            if not self.GRAPH_DB_SESSION:
                self.connect_to_db()
            return self.GRAPH_DB_SESSION
        except Exception:
            raise Exception
    
    def close_db_connection(self):
        try:
            if self.GRAPH_DB_SESSION:
                self.GRAPH_DB_SESSION.close()
                self.GRAPH_DB_SESSION = None
        except Exception:
            raise Exception
        
    def execute_query(self, query):
        try:
            graph_db = self.get_db_connection()
            with graph_db.session(database=Config.db_database) as graphDB_Session:
                return graphDB_Session.run(query).data()
        
        except Exception:
            raise Exception

instance = DBUtil()