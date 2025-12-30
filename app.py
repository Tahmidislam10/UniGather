from flask import Flask, request, jsonify, render_template
from db import get_db
from datetime import datetime

# Initialise Flask app, Connect to MongoDB database, Reference the "events" collection
app = Flask(__name__)
db = get_db()
events = db["events"]


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
    # Fetch all events sorted by newest first
    docs = list(events.find().sort("created_at", -1))

    # Convert MongoDB ObjectId to string for JSON compatibility
    for d in docs:
        d["_id"] = str(d["_id"])

    return jsonify(docs), 200


# ======================
# FORM SUBMISSION
# ======================

# Handle event creation form submission
@app.post("/create/submit-event")
def create_event():
    # Read form inputs
    host_name = request.form.get("host_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    event_name = request.form.get("event_name", "").strip()
    location = request.form.get("location", "").strip()
    capacity = request.form.get("capacity", "").strip()

    # Basic validation: ensure required fields are present
    if not host_name or not email or not event_name:
        return "Missing required fields", 400

    if not location or not capacity:
        return "Missing required fields", 400

    # Insert new event into MongoDB
    events.insert_one({
        "host_name": host_name,
        "email": email,
        "event_name": event_name,
        "location": location,
        "capacity": capacity,
        "created_at": datetime.utcnow()
    })

    return f"Event created: {event_name}", 201


# ======================
# APP ENTRY POINT
# ======================

# Run Flask development server
if __name__ == "__main__":
    app.run(debug=True, port=5000)
