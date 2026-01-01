from flask import Flask, request, jsonify, render_template, make_response, redirect
from db import get_db
from datetime import datetime
from bson.objectid import ObjectId
from bson import ObjectId


# Initialise Flask app, Connect to MongoDB database, Reference the "events" collection
app = Flask(__name__)
db = get_db()
events = db["events"]
users = db["users"]




# ======================
# PAGE ROUTES (HTML)
# ======================

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Events listing page
@app.route("/events-page")
def events_page():
    return render_template("events.html")

# Event creation page

@app.route("/create")
def create_page():
    return render_template("create.html")



# About page
@app.route("/about")
def about_page():
    return render_template("about.html")

# Login / Register page
@app.route("/login")
def login_page():
    return render_template("login.html")


# ======================
# API ROUTES (JSON)
# ======================



# Get all events (used by frontend via fetch)
@app.get("/events")
def get_all_events():
    docs = list(events.find().sort("created_at", -1))

    for d in docs:
        # Convert main event ID
        d["_id"] = str(d["_id"])

        # Convert booked user IDs if they exist
        if "booked_users" in d:
            d["booked_users"] = [str(uid) for uid in d["booked_users"]]

    return jsonify(docs), 200



@app.post("/login")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return "Missing credentials", 400

    user = users.find_one({
        "username": username,
        "password": password  # plain text (as agreed)
    })

    if not user:
        return "Invalid username or password", 401

    # Create response and store user_id + role in cookies
    response = make_response(redirect("/events-page"))
    response.set_cookie("user_id", str(user["_id"]))
    response.set_cookie("role", user["role"])

    return response

# ======================
# Event Booking system 
# ======================

@app.post("/book-event")
def book_event():
    # Read user info from cookies
    user_id = request.cookies.get("user_id")
    role = request.cookies.get("role")

    if not user_id:
        return "You must be logged in to book events", 401

    # Optional: allow both staff & students to book
    if role not in ["student", "staff"]:
        return "Not allowed", 403

    data = request.get_json()
    event_id = data.get("eventId")

    if not event_id:
        return "Missing event ID", 400

    user_oid = ObjectId(user_id)
    event_oid = ObjectId(event_id)

    user = users.find_one({"_id": user_oid})
    event = events.find_one({"_id": event_oid})

    if not user or not event:
        return "Invalid user or event", 404

    # Capacity check
    booked_users = event.get("booked_users", [])
    capacity = int(event.get("event_cap", 0))

    if len(booked_users) >= capacity:
        return "Event is full", 400

    # Prevent duplicate booking
    if user_oid in booked_users:
        return "You have already booked this event", 400

    # Update user (HashSet behaviour)
    users.update_one(
        {"_id": user_oid},
        {"$addToSet": {"booked_events": event_oid}}
    )

    # Update event (HashSet behaviour)
    events.update_one(
        {"_id": event_oid},
        {"$addToSet": {"booked_users": user_oid}}
    )

    return "Event booked successfully", 200

# ======================
# Event Cancel system
# ======================


@app.post("/cancel-booking")
def cancel_booking():
    user_id = request.cookies.get("user_id")
    data = request.get_json()
    event_id = data.get("eventId")

    if not user_id or not event_id:
        return "Missing user or event", 400

    # Remove event from user's bookings
    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"booked_events": event_id}}
    )

    # Remove user from event's booked users
    events.update_one(
        {"_id": ObjectId(event_id)},
        {"$pull": {"booked_users": user_id}}
    )

    return "Booking cancelled", 200



# ======================
# FORM SUBMISSION
# ======================

# Handle event creation form submission
@app.post("/create/submit-event")
def create_event():
    user_id = request.cookies.get("user_id")

    # 400 = bad request: client error in request
    # 401 = unauthorised: authentication failed or insufficient info provided
    # 403 = forbidden: request was valid but user's permissions insufficient

    if not user_id:
        return "Unauthorised User: you must be logged in.", 401
    
    try:
        user = users.find_one({"_id": ObjectId(user_id)})
    except:
        return "Unauthorised User: your user does not exist.", 400
    
    if not user or user.get("role") != "staff":
        return "Unauthorised User: you do not have the required permissions", 403

    # Read form inputs (MATCH form field names)
    event = {
        "host_name": request.form.get("host_name", "").strip(),
        "host_email": request.form.get("host_email", "").strip().lower(),
        "event_name": request.form.get("event_name", "").strip(),
        "event_loc": request.form.get("event_loc", "").strip(),
        "event_date": request.form.get("event_date", "").strip(),
        "event_time": request.form.get("event_time", "").strip(),
        "event_cap": int(request.form.get("event_cap", 0)),
        "event_desc": request.form.get("event_desc", "").strip(),
        "booked_users":[], 
        "created_at": datetime.utcnow()
    }

    # Required field validation
    required_fields = [
        "host_name",
        "host_email",
        "event_name",
        "event_loc",
        "event_date",
        "event_time"
    ]

    for field in required_fields:
        if not event[field]:
            return f"Missing field: {field}", 400

    # Insert into MongoDB
    result = events.insert_one(event)

    # MongoDB auto-generated unique event ID
    event_id = str(result.inserted_id)

    return {
        "message": "Event created successfully",
        "event_id": event_id
    }, 201




# ======================
# APP ENTRY POINT
# ======================

# Run Flask development server
if __name__ == "__main__":
    app.run(debug=True, port=5000)
