from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from io import BytesIO
from reportlab.pdfgen import canvas
from ..extensions import mongo_client

bp = Blueprint("pdfs", __name__)

def db():
    return mongo_client.get_default_database()

@bp.get("/booking/<event_id>")
@jwt_required()
def booking_confirmation_pdf(event_id):
    user_id = get_jwt_identity()

    # must have active booking
    booking = db()["bookings"].find_one({"userId": user_id, "eventId": event_id, "status": "BOOKED"})
    if not booking:
        return jsonify(error="no active booking for this event"), 404

    try:
        event = db()["events"].find_one({"_id": ObjectId(event_id)})
    except Exception:
        return jsonify(error="invalid event id"), 400
    if not event:
        return jsonify(error="event not found"), 404

    # build PDF in memory
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, 780, "Booking Confirmation")
    c.setFont("Helvetica", 12)
    c.drawString(60, 740, f"Event: {event.get('title','')}")
    c.drawString(60, 720, f"Date: {event.get('date','')}")
    c.drawString(60, 700, f"Location: {event.get('location','')}")
    c.drawString(60, 680, f"Category: {event.get('category','')}")
    c.drawString(60, 660, f"Booking status: BOOKED")
    c.drawString(60, 640, f"User ID: {user_id}")
    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="booking_confirmation.pdf"
    )
