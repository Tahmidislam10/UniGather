from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/cloud_events")
client = MongoClient(MONGO_URI)
db = client.get_default_database()

db["users"].create_index("email", unique=True)

db["events"].create_index("title")      # helps regex search a bit
db["events"].create_index("category")
db["events"].create_index("date")

db["bookings"].create_index([("userId", 1), ("eventId", 1), ("status", 1)])
db["waitlists"].create_index([("eventId", 1), ("status", 1), ("position", 1)])

print("Indexes created.")
