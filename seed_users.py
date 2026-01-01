import boto3
from db import get_db

def seed_data():
    db = get_db()
    users_table = db.Table("users")

    # Your MongoDB data mapped to DynamoDB format
    # Note: We use 'id' instead of '_id' to match your Terraform/App logic
    users_to_add = [
        {
            "id": "69542821a693dbefb3433533",
            "username": "staff1",
            "password": "staff123",
            "role": "staff"
            # booked_events is omitted; DynamoDB will create the set 
            # automatically the first time they book an event.
        },
        {
            "id": "69542834a693dbefb3433535",
            "username": "student1",
            "password": "student123",
            "role": "student"
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