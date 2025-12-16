from flask_jwt_extended import JWTManager
from pymongo import MongoClient

jwt = JWTManager()
mongo_client: MongoClient | None = None

def init_mongo(app):
    global mongo_client
    mongo_client = MongoClient(app.config["MONGO_URI"])
    return mongo_client
