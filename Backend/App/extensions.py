
"""
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

jwt = JWTManager()

def init_mongo(app):
    client = MongoClient(app.config["MONGO_URI"])
    app.mongo = client.get_default_database()
"""

# TEMP Mongo stub — DB disabled

class FakeMongo:
    def get_default_database(self):
        raise RuntimeError("MongoDB disabled for frontend testing")

mongo_client = FakeMongo()

def init_mongo(app):
    pass



from flask_jwt_extended import JWTManager

# JWT still needed
jwt = JWTManager()

# TEMP Mongo stub — DB disabled
class FakeMongo:
    def get_default_database(self):
        raise RuntimeError("MongoDB disabled for frontend testing")

mongo_client = FakeMongo()

def init_mongo(app):
    pass

