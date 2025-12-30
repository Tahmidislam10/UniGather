from flask import Flask, request, jsonify, render_template
from db import get_db
from datetime import datetime
from flask import jsonify
from flask import send_from_directory

app = Flask(__name__)
db = get_db()
events = db["events"]



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
    docs = list(events.find().sort("created_at", -1))
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(docs), 200



@app.post("/create/submit-event")
def create_event():
    host_name = request.form.get("host_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    event_name = request.form.get("event_name", "").strip()

    location = request.form.get("location", "").strip()
    capacity = request.form.get("capacity", "").strip()

    if not location or not capacity:
        return "Missing required fields", 400

    if not host_name or not email or not event_name:
        return "Missing required fields", 400

    events.insert_one({
        "host_name": host_name,
        "email": email,
        "event_name": event_name,
        "location": location,
        "capacity": capacity,
        "created_at": datetime.utcnow()
    })

    return f"Event created: {event_name}", 201




if __name__ == "__main__":
    app.run(debug=True, port=5000)



