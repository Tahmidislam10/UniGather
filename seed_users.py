import uuid
from db import get_db
from werkzeug.security import generate_password_hash

def seed_data():
    db = get_db()
    # Access the table using the name defined in your database config
    users_table = db.Table("users")

    # Defined users: 1 Admin, 2 Staff, 1 Student
    users_to_add = [
        {
            "id": str(uuid.uuid4()),
            "full_name": "System Administrator",
            "email": "admin@university.ac.uk",
            # Explicitly use pbkdf2:sha256 to avoid the scrypt error on macOS
            "password": generate_password_hash("admin123", method='pbkdf2:sha256'),
            "role": "admin",
            "booked_events": []
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Alice Staff",
            "email": "alice.staff@university.ac.uk",
            "password": generate_password_hash("staff123", method='pbkdf2:sha256'),
            "role": "staff",
            "booked_events": []
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Bob Staff",
            "email": "bob.staff@university.ac.uk",
            "password": generate_password_hash("staff456", method='pbkdf2:sha256'),
            "role": "staff",
            "booked_events": []
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Charlie Student",
            "email": "charlie@university.ac.uk",
            "password": generate_password_hash("student123", method='pbkdf2:sha256'),
            "role": "student",
            "booked_events": []
        }
    ]

    print("Pushing data to DynamoDB...")

    for user in users_to_add:
        try:
            # Use put_item to insert the user record
            users_table.put_item(Item=user)
            print(f"Success: Added {user['role']} - {user['full_name']}")
        except Exception as e:
            print(f"Failed to add {user['full_name']}: {e}")

    print("All data pushed successfully!")

if __name__ == "__main__":
    seed_data()