import uuid
from flask import Flask, request, jsonify, render_template, make_response, redirect, send_file
from db import get_db
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from dateutil import parser

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

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

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

# ======================
# API ROUTES (JSON/Auth)
# ======================

@app.get("/events")
def get_all_events():
    response = events_table.scan()
    items = response.get("Items", [])

    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    for item in items:
        # Existing: booked users
        if "booked_users" in item and isinstance(item["booked_users"], set):
            item["booked_users"] = list(item["booked_users"])
        else:
            item["booked_users"] = []

        # waitlist users
        if "waitlist_users" in item and isinstance(item["waitlist_users"], set):
            item["waitlist_users"] = list(item["waitlist_users"])
        else:
            item["waitlist_users"] = []

    return jsonify(items), 200




@app.get("/events/<event_id>")
def get_single_event(event_id):
    response = events_table.get_item(Key={"id": event_id})
    event = response.get("Item")

    if not event:
        return "Event not found", 404

    # Convert DynamoDB sets → lists for JSON
    if "booked_users" in event and isinstance(event["booked_users"], set):
        event["booked_users"] = list(event["booked_users"])

    return jsonify(event), 200


@app.get("/reminders")
def get_reminders():
    user_id = request.cookies.get("user_id")

    if not user_id:
        return "Not logged in", 401

    # Fetch user
    user_res = users_table.get_item(Key={"id": user_id})
    user = user_res.get("Item")

    if not user:
        return "User not found", 404

    booked_event_ids = user.get("booked_events", set())

    if not booked_event_ids:
        return jsonify([]), 200

    reminders = []

    # Fetch each booked event
    for event_id in booked_event_ids:
        event_res = events_table.get_item(Key={"id": event_id})
        event = event_res.get("Item")

        if event:
            reminders.append(event)

    # Sort by soonest upcoming event
    reminders.sort(
        key=lambda e: f"{e.get('event_date', '')} {e.get('event_time', '')}"
    )

    return jsonify(reminders), 200

@app.get("/booking-confirmation/<event_id>")
def download_booking_confirmation(event_id):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return "Not logged in", 401

    user_res = users_table.get_item(Key={"id": user_id})
    event_res = events_table.get_item(Key={"id": event_id})

    user = user_res.get("Item")
    event = event_res.get("Item")

    if not user or not event:
        return "Invalid booking", 404

    # Check user is actually booked
    booked_users = event.get("booked_users", set())
    if user_id not in booked_users:
        return "You are not booked for this event", 403

    pdf_buffer = generate_booking_pdf(user, event)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"booking_{event_id}.pdf",
        mimetype="application/pdf"
    )


# ======================
# Event Login system 
# ======================

@app.post("/login")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return "Missing credentials", 400

    # Scan for user in DynamoDB
    response = users_table.scan(
        FilterExpression=Attr("username").eq(username) & Attr("password").eq(password)
    )
    items = response.get("Items", [])

    if not items:
        return "Invalid username or password", 401

    user = items[0]

    # Create response and store user info in cookies
    response = make_response(redirect("/events-page"))
    response.set_cookie("user_id", user["id"]) 
    response.set_cookie("role", user["role"])
    response.set_cookie("username", user["username"]) 
    return response

@app.route("/logout")
def logout():
    response = make_response(redirect("/"))
    # Clear all auth cookies by expiring them
    response.set_cookie("user_id", "", expires=0)
    response.set_cookie("role", "", expires=0)
    response.set_cookie("username", "", expires=0)
    return response

@app.post("/register")
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not username or not password or not email:
        return "All fields are required", 400

    if not email.endswith("@city.ac.uk"):
        return "Registration restricted to @city.ac.uk emails", 403

    # Check if username already exists
    existing_user = users_table.scan(
        FilterExpression=Attr("username").eq(username)
    )
    if existing_user.get("Items"):
        return "Username already taken", 400

    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "username": username,
        "password": password, 
        "email": email,
        "role": "student",
        "booked_events": []
    }

    try:
        users_table.put_item(Item=new_user)
        return redirect("/login")
    except Exception as e:
        print(f"Registration Error: {e}")
        return "Error saving user", 500

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

    event_res = events_table.get_item(Key={"id": event_id})
    user_res = users_table.get_item(Key={"id": user_id})

    event = event_res.get("Item")
    user = user_res.get("Item")

    if not user or not event:
        return "Invalid user or event", 404

    booked_users = event.get("booked_users", set())
    capacity = int(event.get("event_cap", 0))

    waitlist = event.get("waitlist_users", set())

    # === WAITLIST LOGIC ===
    if len(booked_users) >= capacity:
        if user_id in waitlist:
            return "You are already on the waitlist", 400

        events_table.update_item(
            Key={"id": event_id},
            UpdateExpression="ADD waitlist_users :w",
            ExpressionAttributeValues={":w": {user_id}}
        )

        return "Event is full. You have been added to the waitlist.", 200



    if user_id in booked_users:
        return "You have already booked this event", 400

    # Update using DynamoDB Sets
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
        # === EXISTING FUNCTIONALITY (DO NOT CHANGE) ===
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

        # === NEW: AUTO-PROMOTE FROM WAITLIST ===
        event_res = events_table.get_item(Key={"id": event_id})
        event = event_res.get("Item")

        if not event:
            return "Booking cancelled successfully", 200

        booked_users = event.get("booked_users", set())
        waitlist_users = event.get("waitlist_users", set())
        capacity = int(event.get("event_cap", 0))

        if waitlist_users and len(booked_users) < capacity:
            next_user = next(iter(waitlist_users))

            # Remove user from waitlist
            events_table.update_item(
                Key={"id": event_id},
                UpdateExpression="DELETE waitlist_users :w",
                ExpressionAttributeValues={":w": {next_user}}
            )

            # Add user to booked_users
            events_table.update_item(
                Key={"id": event_id},
                UpdateExpression="ADD booked_users :u",
                ExpressionAttributeValues={":u": {next_user}}
            )

            # Add event to user's booked_events
            users_table.update_item(
                Key={"id": next_user},
                UpdateExpression="ADD booked_events :e",
                ExpressionAttributeValues={":e": {event_id}}
            )

        return "Booking cancelled successfully", 200

    except Exception as e:
        print(f"Cancel error: {e}")
        return "Failed to cancel booking", 500


#create PDF  genertion system 

def generate_booking_pdf(user, event):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # === LOGO (BIGGER) ===
    logo_path = "static/logo.png"
    logo = ImageReader(logo_path)

    logo_width = 180
    logo_height = 180

    c.drawImage(
        logo,
        (width - logo_width) / 2,   # center horizontally
        height - 220,               # move up for larger logo
        width=logo_width,
        height=logo_height,
        mask="auto"
    )

    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(
        width / 2,
        height - 280,
        "UniGather Booking Confirmation"
    )

    # Divider
    c.setLineWidth(1)
    c.line(50, height - 300, width - 50, height - 300)

    # Event details
    y = height - 350
    c.setFont("Helvetica", 12)

    details = [
        ("Event Name", event["event_name"]),
        ("Date", event["event_date"]),
        ("Time", event["event_time"]),
        ("Location", event["event_loc"]),
        ("Booked By", user["username"]),
        ("Booking ID", event["id"]),
    ]

    for label, value in details:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y, f"{label}:")
        c.setFont("Helvetica", 12)
        c.drawString(200, y, str(value))
        y -= 30

    # Footer message
    c.setFont("Helvetica-Oblique", 11)
    c.drawString(
        70,
        y - 20,
        "Please present this confirmation at the event entrance."
    )

    # Footer text
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        width / 2,
        40,
        "Generated by UniGather • IN3046 Cloud Computing Project"
    )

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer




# ======================
# FORM SUBMISSION
# ======================

@app.post("/create/submit-event")
def create_event():
    user_id = request.cookies.get("user_id")
    role = request.cookies.get("role")

    if not user_id:
        return "Unauthorised User: you must be logged in.", 401
    
    # Permission Check: Both staff and admin can create events
    if role not in ["staff", "admin"]:
        return "Unauthorised User: permissions insufficient", 403

    event_id = str(uuid.uuid4())
    
    try:
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
            "created_at": datetime.utcnow().isoformat() # Use datetime.now(timezone.utc) if on 3.12+
        }
    except ValueError:
        return "Invalid Capacity: Please enter a number.", 400

    # Validation
    required_fields = ["host_name", "host_email", "event_name", "event_loc", "event_date", "event_time"]
    for field in required_fields:
        if not event[field]:
            return f"Missing field: {field}", 400

    events_table.put_item(Item=event)

    return {
        "message": "Event created successfully",
        "event_id": event_id
    }, 201


# ======================
# Admin Portal Logic
# ======================

@app.route("/admin")
def admin_page():
    """Serves the admin portal only to users with the 'admin' role."""
    role = request.cookies.get("role")
    if role != "admin":
        return redirect("/events-page")
    return render_template("admin.html")

@app.get("/api/users")
def get_all_users():
    """Fetches all users for the admin dashboard."""
    role = request.cookies.get("role")
    if role != "admin":
        return "Unauthorized", 403

    response = users_table.scan()
    items = response.get("Items", [])
    
    # Map to clean list (exclude sensitive data)
    users_list = [{
        "id": u["id"],
        "username": u.get("username", "N/A"),
        "email": u.get("email", "N/A"),
        "role": u.get("role", "student")
    } for u in items]
    
    return jsonify(users_list), 200

@app.post("/update-role")
def update_role():
    """Allows Admins to promote or demote users."""
    requester_role = request.cookies.get("role")
    if requester_role != "admin":
        return "Unauthorized: Only Admins can modify roles", 403

    data = request.get_json()
    target_user_id = data.get("userId")
    new_role = data.get("newRole")

    if not target_user_id or new_role not in ["student", "staff", "admin"]:
        return "Invalid request data", 400

    try:
        # Use #r because 'role' is a reserved keyword in DynamoDB
        users_table.update_item(
            Key={"id": target_user_id},
            UpdateExpression="SET #r = :s",
            ExpressionAttributeNames={"#r": "role"},
            ExpressionAttributeValues={":s": new_role}
        )
        return f"User role updated to {new_role} successfully", 200
    except Exception as e:
        print(f"Role Update Error: {e}")
        return "Failed to update user role", 500
     
if __name__ == "__main__":
    app.run(debug=True, port=5000)