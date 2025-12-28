from flask_jwt_extended import JWTManager
from pymongo import MongoClient

jwt = JWTManager()

def init_mongo(app):
    client = MongoClient(app.config["MONGO_URI"])
    app.mongo = client.get_default_database()
