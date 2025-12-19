import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-change-me")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/cloud_events")
