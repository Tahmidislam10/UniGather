import uuid
from flask import Flask, request, jsonify, render_template, make_response, redirect
from db import get_db 
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)

# Initialise connection
db = get_db()
events_table = db.Table("events")
users_table = db.Table("users")

# ======================
# PAGE ROUTES (HTML)
# ======================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/events-page")
def events_page():
    return render_template("events.html")

@app.route("/create")
def create_page():
    return render_template("create.html")

@app.route("/about")
def about_page():
    return render_template("about.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.get("/events")
def get_all_events():
    response = events_table.scan()
    items = response.get("Items", [])

    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    for item in items:
        # Use .get() with an empty list as a fallback
        if "booked_users" in item and isinstance(item["booked_users"], set):
            item["booked_users"] = list(item["booked_users"])
        else:
            item["booked_users"] = [] # Return empty list to frontend if no one booked yet
            
    return jsonify(items), 200

@app.post("/login")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return "Missing credentials", 400

    # Scan for user (Note: For production, use a Global Secondary Index on username)
    response = users_table.scan(
        FilterExpression=Attr("username").eq(username) & Attr("password").eq(password)
    )
    users = response.get("Items", [])

    if not users:
        return "Invalid username or password", 401

    user = users[0]

    # Create response and store user_id + role in cookies
    response = make_response(redirect("/events-page"))
    response.set_cookie("user_id", user["id"]) # DynamoDB uses 'id' string, not '_id' ObjectId
    response.set_cookie("role", user["role"])
    response.set_cookie("username", user["username"]) # Added this
    return response

@app.route("/logout")
def logout():
    response = make_response(redirect("/"))
    # Clear all auth cookies
    response.set_cookie("user_id", "", expires=0)
    response.set_cookie("role", "", expires=0)
    response.set_cookie("username", "", expires=0)
    return response

# ======================
# Event Booking system
# ======================

@app.post("/book-event")
def book_event():
    user_id = request.cookies.get("user_id")
    role = request.cookies.get("role")

    if not user_id:
        return "You must be logged in to book events", 401

    if role not in ["student", "staff"]:
        return "Not allowed", 403

    data = request.get_json()
    event_id = data.get("eventId")

    if not event_id:
        return "Missing event ID", 400

    # Fetch event and user
    event_res = events_table.get_item(Key={"id": event_id})
    user_res = users_table.get_item(Key={"id": user_id})

    event = event_res.get("Item")
    user = user_res.get("Item")

    if not user or not event:
        return "Invalid user or event", 404

    # Capacity check
    booked_users = event.get("booked_users", set())
    capacity = int(event.get("event_cap", 0))

    if len(booked_users) >= capacity:
        return "Event is full", 400

    if user_id in booked_users:
        return "You have already booked this event", 400

    # Update User and Event using "ADD" (DynamoDB Set behaviour)
    users_table.update_item(
        Key={"id": user_id},
        UpdateExpression="ADD booked_events :e",
        ExpressionAttributeValues={":e": {event_id}}
    )

    events_table.update_item(
        Key={"id": event_id},
        UpdateExpression="ADD booked_users :u",
        ExpressionAttributeValues={":u": {user_id}}
    )

    return "Event booked successfully", 200

@app.post("/cancel-booking")
def cancel_booking():
    user_id = request.cookies.get("user_id")
    data = request.get_json()
    event_id = data.get("eventId")

    if not user_id or not event_id:
        return "Missing user or event", 400

    try:
        # Use "DELETE" to remove the specific ID from the String Set (SS)
        # Note: We provide the value inside a set literal {event_id}
        users_table.update_item(
            Key={"id": user_id},
            UpdateExpression="DELETE booked_events :e",
            ExpressionAttributeValues={":e": {event_id}}
        )

        events_table.update_item(
            Key={"id": event_id},
            UpdateExpression="DELETE booked_users :u",
            ExpressionAttributeValues={":u": {user_id}}
        )

        return "Booking cancelled successfully", 200
    except Exception as e:
        print(f"Cancel error: {e}")
        return "Failed to cancel booking", 500

# ======================
# FORM SUBMISSION
# ======================

@app.post("/create/submit-event")
def create_event():
    user_id = request.cookies.get("user_id")

    if not user_id:
        return "Unauthorised User: you must be logged in.", 401
    
    user_res = users_table.get_item(Key={"id": user_id})
    user = user_res.get("Item")
    
    if not user or user.get("role") != "staff":
        return "Unauthorised User: permissions insufficient", 403

    event_id = str(uuid.uuid4())

    # Create the event object WITHOUT an empty set
    event = {
        "id": event_id,
        "host_name": request.form.get("host_name", "").strip(),
        "host_email": request.form.get("host_email", "").strip().lower(),
        "event_name": request.form.get("event_name", "").strip(),
        "event_loc": request.form.get("event_loc", "").strip(),
        "event_date": request.form.get("event_date", "").strip(),
        "event_time": request.form.get("event_time", "").strip(),
        "event_cap": int(request.form.get("event_cap", 0)),
        "event_desc": request.form.get("event_desc", "").strip(),
        "created_at": datetime.utcnow().isoformat()
        # REMOVED: "booked_users": set() <- This was causing the error
    }

    # Validation...
    required_fields = ["host_name", "host_email", "event_name", "event_loc", "event_date", "event_time"]
    for field in required_fields:
        if not event[field]:
            return f"Missing field: {field}", 400

    # Insert into DynamoDB
    events_table.put_item(Item=event)

    return {
        "message": "Event created successfully",
        "event_id": event_id
    }, 201

import uuid

# --- Page Route ---
@app.route("/register")
def register_page():
    return render_template("register.html")

# --- API Route: Register ---
@app.post("/register")
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    email = request.form.get("email", "").strip().lower()

    # 1. Validation: Required fields
    if not username or not password or not email:
        return "All fields are required", 400

    # 2. Validation: Email domain check
    if not email.endswith("@city.ac.uk"):
        return "Registration restricted to @city.ac.uk emails", 403

    # 3. Check if username already exists
    existing_user = users_table.scan(
        FilterExpression=Attr("username").eq(username)
    )
    if existing_user.get("Items"):
        return "Username already taken", 400

    # 4. Save new user to DynamoDB
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "username": username,
        "password": password, # Keeping plain text as previously agreed
        "email": email,
        "role": "student",    # Default role
        "booked_events": []
    }

    try:
        users_table.put_item(Item=new_user)
        return redirect("/login")
    except Exception as e:
        print(f"Registration Error: {e}")
        return "Error saving user", 500

# --- API Route: Promote to Staff ---
@app.post("/promote-user")
def promote_user():
    # Only staff can promote others
    requester_role = request.cookies.get("role")
    if requester_role != "staff":
        return "Unauthorized: Only staff can promote users", 403

    data = request.get_json()
    target_user_id = data.get("userId")

    if not target_user_id:
        return "Missing User ID", 400

    try:
        users_table.update_item(
            Key={"id": target_user_id},
            UpdateExpression="SET #r = :s",
            ExpressionAttributeNames={"#r": "role"},
            ExpressionAttributeValues={":s": "staff"}
        )
        return "User promoted to staff successfully", 200
    except Exception as e:
        print(f"Promotion Error: {e}")
        return "Failed to promote user", 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)