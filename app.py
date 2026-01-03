import uuid
from flask import Flask, request, jsonify, render_template, make_response, redirect, send_file
from db import get_db
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from dateutil import parser
from collections import defaultdict
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from werkzeug.security import generate_password_hash, check_password_hash

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
        # Standardize to lists to prevent booking errors
        if "booked_users" not in item or not isinstance(item["booked_users"], list):
            item["booked_users"] = list(item["booked_users"]) if isinstance(item.get("booked_users"), set) else []
        
        if "waitlist_users" not in item or not isinstance(item["waitlist_users"], list):
            item["waitlist_users"] = list(item["waitlist_users"]) if isinstance(item.get("waitlist_users"), set) else []

    return jsonify(items), 200

@app.get("/events/<event_id>")
def get_single_event(event_id):
    response = events_table.get_item(Key={"id": event_id})
    event = response.get("Item")

    if not event:
        return "Event not found", 404

    # Convert DynamoDB sets/types → lists for JSON
    if "booked_users" in event and not isinstance(event["booked_users"], list):
        event["booked_users"] = list(event["booked_users"])

    return jsonify(event), 200

@app.get("/reminders")
def get_reminders():
    user_id = request.cookies.get("user_id")

    if not user_id:
        return "Not logged in", 401

    user_res = users_table.get_item(Key={"id": user_id})
    user = user_res.get("Item")

    if not user:
        return "User not found", 404

    booked_event_ids = user.get("booked_events", [])

    if not booked_event_ids:
        return jsonify([]), 200

    reminders = []
    for event_id in booked_event_ids:
        event_res = events_table.get_item(Key={"id": event_id})
        event = event_res.get("Item")
        if event:
            # Ensure lists for frontend compatibility
            event["booked_users"] = list(event.get("booked_users", []))
            reminders.append(event)

    reminders.sort(key=lambda e: f"{e.get('event_date', '')} {e.get('event_time', '')}")
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

    # Check user is actually booked (supports both list and set check)
    booked_users = event.get("booked_users", [])
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
# AUTHENTICATION SYSTEM
# ======================

@app.post("/login")
def login():
    # 1. Get the plain text email and password from the form
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    # 2. Find the user in DynamoDB by their email
    # We don't include password in the scan because it's now hashed
    response = users_table.scan(
        FilterExpression=Attr("email").eq(email)
    )
    items = response.get("Items", [])

    # 3. If no user found with that email
    if not items:
        return "Invalid email or password", 401

    user = items[0]
    stored_hashed_password = user.get("password")

    # 4. SECURITY CHECK: Compare the plain password with the stored hash
    # check_password_hash handles the decryption/comparison logic for you
    if not check_password_hash(stored_hashed_password, password):
        return "Invalid email or password", 401

    # 5. Success: Set cookies and redirect
    # We use Full Name for the 'username' cookie so the header looks nice
    display_name = user.get("full_name", user.get("username", "User"))
    
    response = make_response(redirect("/events-page"))
    response.set_cookie("user_id", user["id"]) 
    response.set_cookie("role", user["role"])
    response.set_cookie("username", display_name) 
    
    return response

@app.route("/logout")
def logout():
    response = make_response(redirect("/"))
    response.set_cookie("user_id", "", expires=0)
    response.set_cookie("role", "", expires=0)
    response.set_cookie("username", "", expires=0)
    return response

@app.post("/register")
def register():
    # 1. Retrieve and clean form data
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    # 2. Basic validation
    if not full_name or not email or not password:
        return "All fields are required", 400

    # 3. Academic email restriction (.ac.uk)
    if not email.endswith(".ac.uk"):
        return "Registration is restricted to .ac.uk academic emails", 403

    # 4. Check if the email is already in use
    existing_user = users_table.scan(
        FilterExpression=Attr("email").eq(email)
    )
    if existing_user.get("Items"):
        return "An account with this email already exists", 400

    # 5. Security: Hash the password
    # Using pbkdf2:sha256 to ensure compatibility with your Mac environment
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # 6. Prepare the user object for DynamoDB
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "full_name": full_name,
        "email": email,
        "password": hashed_password, # Storing the protected hash
        "role": "student",           # Default role
        "booked_events": []          # Initialised as a list to prevent "ValidationException"
    }

    # 7. Save to database
    try:
        users_table.put_item(Item=new_user)
        return redirect("/login")
    except Exception as e:
        print(f"Registration Error: {e}")
        return "Failed to create account. Please try again later.", 500

# ======================
# BOOKING SYSTEM
# ======================

@app.post("/book-event")
def book_event():
    user_id = request.cookies.get("user_id")
    if not user_id:
        return "You must be logged in to book events", 401

    role = request.cookies.get("role")
    if role not in ["student", "staff", "admin"]:
        return "Not allowed", 403

    data = request.get_json()
    event_id = data.get("eventId")

    event = events_table.get_item(Key={"id": event_id}).get("Item")
    if not event:
        return "Event not found", 404

    booked_users = event.get("booked_users", [])
    waitlist_users = event.get("waitlist_users", [])
    capacity = int(event.get("event_cap", 0))

    # Already booked
    if user_id in booked_users:
        return "You already booked this event", 400

    # Already on waitlist
    if user_id in waitlist_users:
        return "You are already on the waitlist", 400

    # Event full → add to waitlist
    if len(booked_users) >= capacity:
        events_table.update_item(
            Key={"id": event_id},
            UpdateExpression="SET waitlist_users = list_append(if_not_exists(waitlist_users, :e), :u)",
            ExpressionAttributeValues={
                ":u": [user_id],
                ":e": []
            }
        )
        return "Event full. You have been added to the waitlist.", 200

    # Otherwise → book normally
    users_table.update_item(
        Key={"id": user_id},
        UpdateExpression="SET booked_events = list_append(if_not_exists(booked_events, :e), :b)",
        ExpressionAttributeValues={
            ":b": [event_id],
            ":e": []
        }
    )

    events_table.update_item(
        Key={"id": event_id},
        UpdateExpression="SET booked_users = list_append(if_not_exists(booked_users, :e), :u)",
        ExpressionAttributeValues={
            ":u": [user_id],
            ":e": []
        }
    )

    return "Event booked successfully", 200

@app.post("/cancel-waitlist")
def cancel_waitlist():
    user_id = request.cookies.get("user_id")
    data = request.get_json()
    event_id = data.get("eventId")

    if not user_id or not event_id:
        return "Missing data", 400

    event = events_table.get_item(Key={"id": event_id}).get("Item")
    if not event:
        return "Event not found", 404

    new_waitlist = [u for u in event.get("waitlist_users", []) if u != user_id]

    events_table.update_item(
        Key={"id": event_id},
        UpdateExpression="SET waitlist_users = :w",
        ExpressionAttributeValues={":w": new_waitlist}
    )

    return "You have left the waitlist", 200


@app.post("/cancel-booking")
def cancel_booking():
    requester_id = request.cookies.get("user_id")
    role = request.cookies.get("role")
    data = request.get_json()
    
    event_id = data.get("eventId")
    target_user_id = data.get("targetUserId", requester_id)

    # Permission Check: Both Staff and Admin can cancel for anyone
    if requester_id != target_user_id and role not in ["staff", "admin"]:
        return "Unauthorised", 403

    try:
        # User side removal
        user_res = users_table.get_item(Key={"id": target_user_id})
        user = user_res.get("Item")
        if user:
            new_booked = [e for e in user.get("booked_events", []) if e != event_id]
            users_table.update_item(
                Key={"id": target_user_id},
                UpdateExpression="SET booked_events = :b",
                ExpressionAttributeValues={":b": new_booked}
            )

        # Event side removal
        event_res = events_table.get_item(Key={"id": event_id})
        event = event_res.get("Item")
        if event:
            new_attendees = [u for u in event.get("booked_users", []) if u != target_user_id]
            events_table.update_item(
                Key={"id": event_id},
                UpdateExpression="SET booked_users = :u",
                ExpressionAttributeValues={":u": new_attendees}
            )

        return "Booking cancelled successfully", 200
    except Exception as e:
        return f"Cancel error: {str(e)}", 500

# ======================
# PDF GENERATION
# ======================

def generate_booking_pdf(user, event):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    logo_path = "static/logo.png"
    logo = ImageReader(logo_path)
    c.drawImage(logo, (width - 180) / 2, height - 220, width=180, height=180, mask="auto")

    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 280, "UniGather Booking Confirmation")
    c.line(50, height - 300, width - 50, height - 300)

    y = height - 350
    details = [
        ("Event Name", event["event_name"]),
        ("Date", event["event_date"]),
        ("Time", event["event_time"]),
        ("Location", event["event_loc"]),
        ("Booked By", user.get("full_name", user.get("username", "User"))),
        ("Booking ID", event["id"]),
    ]

    for label, value in details:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y, f"{label}:")
        c.setFont("Helvetica", 12)
        c.drawString(200, y, str(value))
        y -= 30

    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 40, "Generated by UniGather • IN3046 Cloud Computing Project")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ======================
# EVENT MANAGEMENT
# ======================

@app.post("/create/submit-event")
def create_event():
    user_id = request.cookies.get("user_id")
    role = request.cookies.get("role")

    if not user_id or role not in ["staff", "admin"]:
        return "Unauthorised User", 403

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
            "created_at": datetime.utcnow().isoformat(),
            "booked_users": [],
            "waitlist_users": []
        }
        events_table.put_item(Item=event)
        return {"message": "Event created", "event_id": event_id}, 201
    except Exception as e:
        return f"Error: {str(e)}", 400

@app.post("/delete-event")
def delete_event():
    role = request.cookies.get("role")
    # FIX: Allow both 'staff' and 'admin' to delete
    if role not in ["staff", "admin"]:
        return "Unauthorised: Only Staff and Admins can delete events", 403

    data = request.get_json()
    event_id = data.get("eventId")
    try:
        events_table.delete_item(Key={"id": event_id})
        return "Event deleted successfully", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.post("/view-attendees")
def view_attendees():
    role = request.cookies.get("role")
    if role not in ["staff", "admin"]:
        return "Unauthorised", 403

    data = request.get_json()
    event_id = data.get("eventId")
    event = events_table.get_item(Key={"id": event_id}).get("Item")
    
    if not event: return "Event not found", 404

    booked_ids = event.get("booked_users", [])
    if not booked_ids: return "No attendees yet.", 200

    attendee_names = []
    for uid in booked_ids:
        u_item = users_table.get_item(Key={"id": uid}).get("Item")
        if u_item:
            attendee_names.append(u_item.get("full_name", u_item.get("username", "Unknown")))

    return f"Attendees: {', '.join(attendee_names)}", 200

# ======================
# ADMIN PORTAL
# ======================

@app.route("/admin")
def admin_page():
    if request.cookies.get("role") != "admin":
        return "Unauthorised", 403
    return render_template("admin.html")

@app.route("/analytics")
def analytics_page():
    if request.cookies.get("role") not in ["staff", "admin"]:
        return "Unauthorised", 403
    return render_template("analytics.html")


@app.get("/api/users")
def get_all_users():
    if request.cookies.get("role") != "admin":
        return "Unauthorised", 403

    items = users_table.scan().get("Items", [])
    users_list = [{
        "id": u["id"],
        "full_name": u.get("full_name", "N/A"),
        "email": u.get("email", "N/A"),
        "role": u.get("role", "student")
    } for u in items]
    return jsonify(users_list), 200

@app.post("/update-role")
def update_role():
    if request.cookies.get("role") != "admin":
        return "Unauthorised", 403

    data = request.get_json()
    try:
        users_table.update_item(
            Key={"id": data.get("userId")},
            UpdateExpression="SET #r = :s",
            ExpressionAttributeNames={"#r": "role"},
            ExpressionAttributeValues={":s": data.get("newRole")}
        )
        return "Role updated", 200
    except:
        return "Failed", 500

@app.get("/api/analytics/weekly")
def analytics_weekly():
    role = request.cookies.get("role")
    if role not in ["staff", "admin"]:
        return "Unauthorised", 403

    events = events_table.scan().get("Items", [])

    weekly_events = defaultdict(int)
    weekly_attendees = defaultdict(int)

    for event in events:
        created_at = event.get("created_at")
        if not created_at:
            continue

        dt = parser.parse(created_at)
        year, week, _ = dt.isocalendar()
        week_key = f"{year}-W{week:02d}"


        weekly_events[week_key] += 1
        weekly_attendees[week_key] += len(event.get("booked_users", []))

    weeks_sorted = sorted(weekly_events.keys())

    return jsonify({
        "weeks": weeks_sorted,
        "events": [weekly_events[w] for w in weeks_sorted],
        "attendees": [weekly_attendees[w] for w in weeks_sorted]
    }), 200


@app.get("/api/analytics/daily")
def analytics_daily():
    role = request.cookies.get("role")
    if role not in ["staff", "admin"]:
        return "Unauthorised", 403

    events = events_table.scan().get("Items", [])

    daily_events = defaultdict(int)
    daily_attendees = defaultdict(int)

    for event in events:
        created_at = event.get("created_at")
        if not created_at:
            continue

        dt = parser.parse(created_at)
        day = dt.strftime("%A")  # Monday, Tuesday, etc.

        daily_events[day] += 1
        daily_attendees[day] += len(event.get("booked_users", []))

    ordered_days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    return jsonify({
        "days": ordered_days,
        "events": [daily_events[d] for d in ordered_days],
        "attendees": [daily_attendees[d] for d in ordered_days]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)