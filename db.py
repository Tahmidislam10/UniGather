import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def get_db():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "unigather")
    client = MongoClient(mongo_uri)
    return client[db_name]
