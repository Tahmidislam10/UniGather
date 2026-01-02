import boto3
from db import get_db
from werkzeug.security import generate_password_hash

def seed_data():
    db = get_db()
    users_table = db.Table("users")

    users_to_add = [
        {
            "id": "15322711a693dbefb3433533",
            "username": "admin1",
            "password": generate_password_hash("admin123"),
            "role": "admin"
            # booked_events is omitted; DynamoDB will create the set 
            # automatically the first time they book an event.
        }
    ]

    print("Starting to seed users into DynamoDB...")

    for user in users_to_add:
        try:
            users_table.put_item(Item=user)
            print(f"Successfully added: {user['username']}")
        except Exception as e:
            print(f"Error adding {user['username']}: {e}")

    print("Seeding complete!")

if __name__ == "__main__":
    seed_data()
