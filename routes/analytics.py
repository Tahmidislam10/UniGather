from flask import Blueprint, request, jsonify, render_template
from collections import defaultdict
from dateutil import parser
from db import get_db
from routes.permissions import has_permission

analytics = Blueprint("analytics", __name__)

db = get_db()
events_table = db.Table("events")


# ANALYTICS PAGE


@analytics.route("/analytics")
def analytics_page():
    # Renders the analytics dashboard page (staff/admin access)
    user_id = request.cookies.get("user_id")

    # Check staff or admin permissions
    if not has_permission(user_id, ["staff", "admin"]):
        return "Unauthorised: only staff and admins allowed.", 403

    return render_template("analytics.html")



# ANALYTICS APIs


@analytics.get("/api/analytics/weekly")
def analytics_weekly():
    # Returns weekly event and attendee statistics
    user_id = request.cookies.get("user_id")

    # Restrict access to staff and admins
    if not has_permission(user_id, ["staff", "admin"]):
        return "Unauthorised: only staff and admins allowed.", 403

    # Fetch all events
    events = events_table.scan().get("Items", [])

    weekly_events = defaultdict(int)
    weekly_attendees = defaultdict(int)

    # Group events by ISO calendar week
    for event in events:
        created_at = event.get("created_at")
        if not created_at:
            continue

        dt = parser.parse(created_at)
        year, week, _ = dt.isocalendar()
        week_key = f"{year}-W{week:02d}"

        weekly_events[week_key] += 1
        weekly_attendees[week_key] += len(event.get("booked_users", []))

    # Sort weeks chronologically
    weeks_sorted = sorted(weekly_events.keys())

    return jsonify({
        "weeks": weeks_sorted,
        "events": [weekly_events[w] for w in weeks_sorted],
        "attendees": [weekly_attendees[w] for w in weeks_sorted]
    }), 200



@analytics.get("/api/analytics/daily")
def analytics_daily():
    # Returns daily event and attendee statistics
    user_id = request.cookies.get("user_id")

    # Restrict access to staff and admins
    if not has_permission(user_id, ["staff", "admin"]):
        return "Unauthorised: only staff and admins allowed.", 403

    # Fetch all events
    events = events_table.scan().get("Items", [])

    daily_events = defaultdict(int)
    daily_attendees = defaultdict(int)

    # Group events by day of the week
    for event in events:
        created_at = event.get("created_at")
        if not created_at:
            continue

        dt = parser.parse(created_at)
        day = dt.strftime("%A")

        daily_events[day] += 1
        daily_attendees[day] += len(event.get("booked_users", []))

    # Ensure consistent day ordering
    ordered_days = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    return jsonify({
        "days": ordered_days,
        "events": [daily_events[d] for d in ordered_days],
        "attendees": [daily_attendees[d] for d in ordered_days]
    }), 200



@analytics.get("/api/analytics/summary")
def analytics_summary():
    # Returns overall booking and capacity statistics
    user_id = request.cookies.get("user_id")

    # Restrict access to staff and admins
    if not has_permission(user_id, ["staff", "admin"]):
        return "Unauthorised: only staff and admins allowed.", 403

    # Fetch all events
    events = events_table.scan().get("Items", [])

    total_capacity = 0
    total_booked = 0
    total_waitlisted = 0
    total_events = 0

    # Aggregate capacity and booking data
    for event in events:
        cap = int(event.get("event_cap", 0))
        booked = len(event.get("booked_users", []))
        waitlisted = len(event.get("waitlist_users", []))

        total_capacity += cap
        total_booked += booked
        total_waitlisted += waitlisted
        total_events += 1

    # Calculate average fill rate percentage
    avg_fill_rate = (
        round((total_booked / total_capacity) * 100, 2)
        if total_capacity > 0 else 0
    )

    # Derive cancellation count
    cancellations = total_capacity - total_booked - total_waitlisted
    if cancellations < 0:
        cancellations = 0

    return jsonify({
        "average_fill_rate": avg_fill_rate,
        "booked": total_booked,
        "waitlisted": total_waitlisted,
        "cancellations": cancellations
    }), 200

