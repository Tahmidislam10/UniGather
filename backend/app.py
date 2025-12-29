from flask import Flask, request
from db import get_db
from datetime import datetime

app = Flask(__name__)
db = get_db()
events = db["events"]

@app.post("/create/submit-event")
def create_event():
    host_name = request.form.get("host_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    event_name = request.form.get("event_name", "").strip()

    if not host_name or not email or not event_name:
        return "Missing required fields", 400

    events.insert_one({
        "host_name": host_name,
        "email": email,
        "event_name": event_name,
        "created_at": datetime.utcnow()
    })

    return f"Event created: {event_name}", 201

if __name__ == "__main__":
    app.run(debug=True, port=5000)
