from db import get_db

db = get_db()
users_table = db.Table("users")

# Helper function to check if the user has the correct permissions
def has_permission(user_id, allowed):
    if not user_id:
        return False

    try:
        user = users_table.get_item(Key={"id": user_id}).get("Item")
        if not user:
            return False
        return user.get("role") in allowed
    except Exception:
        return False
