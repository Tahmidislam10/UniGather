import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from db import get_db
from routes.permissions import has_permission
from routes.pdf import generate_booking_pdf

events = Blueprint("events", __name__)

db = get_db()
events_table = db.Table("events")
users_table = db.Table("users")


# GET ALL EVENTS

@events.get("/events")
def get_all_events():
    # Returns all events sorted by creation time
    response = events_table.scan()
    items = response.get("Items", [])

    # Ensure DynamoDB sets are converted to lists for frontend compatibility
    for item in items:
        if "booked_users" not in item or not isinstance(item["booked_users"], list):
            item["booked_users"] = (
                list(item["booked_users"])
                if isinstance(item.get("booked_users"), set)
                else []
            )

        if "waitlist_users" not in item or not isinstance(item["waitlist_users"], list):
            item["waitlist_users"] = (
                list(item["waitlist_users"])
                if isinstance(item.get("waitlist_users"), set)
                else []
            )

    # Sorts events by earliest to furthest but sorts past events to the very bottom
    items.sort(
        key=lambda e: (
        (f"{e.get('event_date', '')} {e.get('event_time', '')}" < datetime.now().strftime("%Y-%m-%d %H:%M")),
        f"{e.get('event_date', '')} {e.get('event_time', '')}"
        )
    )

    return jsonify(items), 200



# GET SINGLE EVENT


@events.get("/events/<event_id>")
def get_single_event(event_id):
    # Returns details for a single event by ID
    response = events_table.get_item(Key={"id": event_id})
    event = response.get("Item")

    # Handle missing event
    if not event:
        return "Event not found", 404

    # Convert booked_users to list for JSON safety
    if "booked_users" in event and not isinstance(event["booked_users"], list):
        event["booked_users"] = list(event["booked_users"])

    return jsonify(event), 200



# REMINDERS


@events.get("/reminders")
def get_reminders():
    # Returns upcoming events booked by the logged-in user
    user_id = request.cookies.get("user_id")

    # Require user to be logged in
    if not user_id:
        return "Not logged in", 401

    # Fetch user details
    user_res = users_table.get_item(Key={"id": user_id})
    user = user_res.get("Item")

    if not user:
        return "User not found", 404

    booked_event_ids = user.get("booked_events", [])

    # No bookings found
    if not booked_event_ids:
        return jsonify([]), 200

    reminders = []
    for event_id in booked_event_ids:
        event_res = events_table.get_item(Key={"id": event_id})
        event = event_res.get("Item")
        if event:
            # Ensure booked_users is a list for frontend use
            event["booked_users"] = list(event.get("booked_users", []))
            reminders.append(event)

    # Sorts events by earliest to furthest but sorts past events to the very bottom
    reminders.sort(
        key=lambda e: (
        (f"{e.get('event_date', '')} {e.get('event_time', '')}" < datetime.now().strftime("%Y-%m-%d %H:%M")),
        f"{e.get('event_date', '')} {e.get('event_time', '')}"
        )
    )

    return jsonify(reminders), 200


# BOOKING CONFIRMATION PDF


@events.get("/booking-confirmation/<event_id>")
def download_booking_confirmation(event_id):
    # Generates and downloads a booking confirmation PDF for an event
    user_id = request.cookies.get("user_id")

    # Require user to be logged in
    if not user_id:
        return "Not logged in", 401

    # Fetch user and event details
    user_res = users_table.get_item(Key={"id": user_id})
    event_res = events_table.get_item(Key={"id": event_id})

    user = user_res.get("Item")
    event = event_res.get("Item")

    # Validate booking existence
    if not user or not event:
        return "Invalid booking", 404

    # Ensure the user is booked for this event
    booked_users = event.get("booked_users", [])
    if user_id not in booked_users:
        return "You are not booked for this event", 403

    # Generate booking confirmation PDF
    pdf_buffer = generate_booking_pdf(user, event)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"booking_{event_id}.pdf",
        mimetype="application/pdf"
    )


# CREATE EVENT


@events.post("/create/submit-event")
def create_event():
    # Creates a new event (staff/admin only)
    user_id = request.cookies.get("user_id")

    # Check permission to create events
    if not has_permission(user_id, ["staff", "admin"]):
        return "Unauthorised: only staff and admins allowed.", 403

    event_id = str(uuid.uuid4())

    try:
        # Build event object from form data
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

        # Save event to DynamoDB
        events_table.put_item(Item=event)
        return {"message": "Event created", "event_id": event_id}, 201

    except Exception as e:
        return f"Error: {str(e)}", 400



# BOOK EVENT


@events.post("/book-event")
def book_event():
    # Handles event booking and waitlist logic
    user_id = request.cookies.get("user_id")

    # Require user to be logged in
    if not user_id:
        return "You must be logged in to book events", 401

    # Check booking permissions
    if not has_permission(user_id, ["student", "staff", "admin"]):
        return "Unauthorised", 403

    # Read event ID from request body
    data = request.get_json()
    event_id = data.get("eventId")

    # Fetch event details
    event = events_table.get_item(Key={"id": event_id}).get("Item")
    if not event:
        return "Event not found", 404

    booked_users = event.get("booked_users", [])
    waitlist_users = event.get("waitlist_users", [])
    capacity = int(event.get("event_cap", 0))

    # Prevent duplicate bookings
    if user_id in booked_users:
        return "You already booked this event", 400

    if user_id in waitlist_users:
        return "You are already on the waitlist", 400

    # Add to waitlist if event is full
    if len(booked_users) >= capacity:
        events_table.update_item(
            Key={"id": event_id},
            UpdateExpression=(
                "SET waitlist_users = "
                "list_append(if_not_exists(waitlist_users, :e), :u)"
            ),
            ExpressionAttributeValues={
                ":u": [user_id],
                ":e": []
            }
        )
        return "Event full. You have been added to the waitlist.", 200

    # Add event to user's bookings
    users_table.update_item(
        Key={"id": user_id},
        UpdateExpression=(
            "SET booked_events = "
            "list_append(if_not_exists(booked_events, :e), :b)"
        ),
        ExpressionAttributeValues={
            ":b": [event_id],
            ":e": []
        }
    )

    # Add user to event's booked list
    events_table.update_item(
        Key={"id": event_id},
        UpdateExpression=(
            "SET booked_users = "
            "list_append(if_not_exists(booked_users, :e), :u)"
        ),
        ExpressionAttributeValues={
            ":u": [user_id],
            ":e": []
        }
    )

    return "Event booked successfully", 200



# CANCEL WAITLIST


@events.post("/cancel-waitlist")
def cancel_waitlist():
    # Removes the logged-in user from an event waitlist
    user_id = request.cookies.get("user_id")
    data = request.get_json()
    event_id = data.get("eventId")

    # Validate required data
    if not user_id or not event_id:
        return "Missing data", 400

    # Fetch event details
    event = events_table.get_item(Key={"id": event_id}).get("Item")
    if not event:
        return "Event not found", 404

    # Remove user from waitlist
    new_waitlist = [
        u for u in event.get("waitlist_users", [])
        if u != user_id
    ]

    events_table.update_item(
        Key={"id": event_id},
        UpdateExpression="SET waitlist_users = :w",
        ExpressionAttributeValues={":w": new_waitlist}
    )

    return "You have left the waitlist", 200



# CANCEL BOOKING


@events.post("/cancel-booking")
def cancel_booking():
    # Cancels a user's booking and handles waitlist promotion
    user_id = request.cookies.get("user_id")
    data = request.get_json()
    event_id = data.get("eventId")

    # Validate required data
    if not user_id or not event_id:
        return "Missing user or event", 400

    try:
        
        # Remove booking from user
       
        user_res = users_table.get_item(Key={"id": user_id})
        user = user_res.get("Item")

        if user:
            new_booked = [
                e for e in user.get("booked_events", [])
                if e != event_id
            ]
            users_table.update_item(
                Key={"id": user_id},
                UpdateExpression="SET booked_events = :b",
                ExpressionAttributeValues={":b": new_booked}
            )

       
        # Remove user from event
        
        event_res = events_table.get_item(Key={"id": event_id})
        event = event_res.get("Item")

        if not event:
            return "Booking cancelled successfully", 200

        new_attendees = [
            u for u in event.get("booked_users", [])
            if u != user_id
        ]

        
        # Auto-promote from waitlist
        
        waitlist_users = event.get("waitlist_users", [])
        capacity = int(event.get("event_cap", 0))

        if waitlist_users and len(new_attendees) < capacity:
            next_user_id = waitlist_users.pop(0)
            new_attendees.append(next_user_id)

            users_table.update_item(
                Key={"id": next_user_id},
                UpdateExpression=(
                    "SET booked_events = "
                    "list_append(if_not_exists(booked_events, :empty), :e)"
                ),
                ExpressionAttributeValues={
                    ":e": [event_id],
                    ":empty": []
                }
            )

        
        # Update event record
        
        events_table.update_item(
            Key={"id": event_id},
            UpdateExpression="SET booked_users = :b, waitlist_users = :w",
            ExpressionAttributeValues={
                ":b": new_attendees,
                ":w": waitlist_users
            }
        )

        return "Booking cancelled successfully", 200

    except Exception as e:
        print(f"Cancel error: {e}")
        return "Failed to cancel booking", 500


# DELETE EVENT


@events.post("/delete-event")
def delete_event():
    # Deletes an event (staff/admin only)
    user_id = request.cookies.get("user_id")

    # Check permission to delete events
    if not has_permission(user_id, ["staff", "admin"]):
        return "Unauthorised: only staff and admins can delete events.", 403

    # Read event ID from request body
    data = request.get_json()
    event_id = data.get("eventId")

    try:
        # Remove event from DynamoDB
        events_table.delete_item(Key={"id": event_id})
        return "Event deleted successfully", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

