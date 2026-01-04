from flask import Blueprint, request, jsonify, render_template
from db import get_db
from routes.permissions import has_permission

admin = Blueprint("admin", __name__)

db = get_db()
users_table = db.Table("users")
events_table = db.Table("events")


# ADMIN PAGE
@admin.route("/admin")
def admin_page():
    # Renders the admin dashboard page (admin-only access)
    user_id = request.cookies.get("user_id")

    # Ensure the user has admin permissions
    if not has_permission(user_id, ["admin"]):
        return "Unauthorised: only admins allowed.", 403

    return render_template("admin.html")


# ADMIN APIs
@admin.get("/api/users")
def get_all_users():
    # Returns a list of all users (admin-only API)
    user_id = request.cookies.get("user_id")

    # Check admin permission
    if not has_permission(user_id, ["admin"]):
        return "Unauthorised: only admins allowed.", 403

    # Fetch all users from DynamoDB
    items = users_table.scan().get("Items", [])

    # Format user data for frontend consumption
    users_list = [
        {
            "id": u["id"],
            "full_name": u.get("full_name", "N/A"),
            "email": u.get("email", "N/A"),
            "role": u.get("role", "student")
        }
        for u in items
    ]

    return jsonify(users_list), 200


@admin.post("/update-role")
def update_role():
    # Updates a user's role (admin-only action)
    user_id = request.cookies.get("user_id")

    # Verify admin permissions
    if not has_permission(user_id, ["admin"]):
        return "Unauthorised: only admins allowed.", 403

    # Read role update data from request body
    data = request.get_json()

    try:
        # Update the user's role in DynamoDB
        users_table.update_item(
            Key={"id": data.get("userId")},
            UpdateExpression="SET #r = :s",
            ExpressionAttributeNames={"#r": "role"},
            ExpressionAttributeValues={":s": data.get("newRole")}
        )
        return "Role updated", 200
    except Exception:
        return "Failed", 500


@admin.post("/view-attendees")
def view_attendees():
    # Returns the list of attendee names for a specific event
    user_id = request.cookies.get("user_id")

    # Allow only staff or admin users
    if not has_permission(user_id, ["staff", "admin"]):
        return "Unauthorised: only staff and admins can view event attendees.", 403

    # Get event ID from request body
    data = request.get_json()
    event_id = data.get("eventId")

    # Fetch the event from DynamoDB
    event = events_table.get_item(Key={"id": event_id}).get("Item")
    if not event:
        return "Event not found", 404

    # Get booked user IDs
    booked_ids = event.get("booked_users", [])
    if not booked_ids:
        return "No attendees yet.", 200

    # Resolve user IDs to display names
    attendee_names = []
    for uid in booked_ids:
        u_item = users_table.get_item(Key={"id": uid}).get("Item")
        if u_item:
            attendee_names.append(
                u_item.get("full_name", u_item.get("username", "Unknown"))
            )

    return f"Attendees: {', '.join(attendee_names)}", 200
