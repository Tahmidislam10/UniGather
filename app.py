import uuid
from flask import Flask, request, jsonify, render_template, make_response, redirect
from db import get_db  # Assuming get_db now returns boto3.resource('dynamodb')
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

# Initialise Flask app
app = Flask(__name__)

# Connect to DynamoDB tables
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

# ======================
# API ROUTES (JSON)
# ======================

@app.get("/events")
def get_all_events():
    # DynamoDB scan (returns all items)
    response = events_table.scan()
    items = response.get("Items", [])

    # DynamoDB doesn't support built-in sorting on scan, so we sort in Python
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # Convert sets to lists for JSON serialization (DynamoDB uses sets for 'booked_users')
    for item in items:
        if "booked_users" in item and isinstance(item["booked_users"], set):
            item["booked_users"] = list(item["booked_users"])
            
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

    # Use "DELETE" to remove from a set in DynamoDB
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

    return "Booking cancelled", 200

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

    # Generate a unique string ID for the new event
    event_id = str(uuid.uuid4())

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
        "created_at": datetime.utcnow().isoformat(), # DynamoDB prefers ISO strings for dates
        "booked_users": set() # Initialise empty set
    }

    # Validation... (kept same as your code)
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)