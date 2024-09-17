from pymongo import MongoClient
 
class db_connection_manage():
    def __init__(self):
        self.MONGO_DB_NAME = 'cms'
        self.MONGO_HOST = 'localhost'
        self.MONGO_PORT = 27017
 
    def get_conn(self,env_type):
        client = MongoClient(self.MONGO_HOST, self.MONGO_PORT)
        db = client[f"{self.MONGO_DB_NAME}{env_type}"]
        return {"client":client,"db":db}
 
    def close_connection(self,client):
        client.close()