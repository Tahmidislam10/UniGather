import os
from dotenv import load_dotenv

# Load variables from .env into environment
load_dotenv()

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI")


print("MONGO_URI loaded:", bool(os.getenv("MONGO_URI")))
