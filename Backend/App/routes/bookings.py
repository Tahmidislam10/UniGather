from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from bson import ObjectId
from ..extensions import mongo_client

bp = Blueprint("bookings", __name__)

def db():
    return mongo_client.get_default_database()

def oid(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        return None

@bp.post("/<event_id>")
@jwt_required()
def book_event(event_id):
    user_id = get_jwt_identity()
    e_id = oid(event_id)
    if not e_id:
        return jsonify(error="invalid event id"), 400

    event = db()["events"].find_one({"_id": e_id})
    if not event:
        return jsonify(error="event not found"), 404

    # prevent double-booking
    existing = db()["bookings"].find_one({"userId": user_id, "eventId": event_id, "status": "BOOKED"})
    if existing:
        return jsonify(status="ALREADY_BOOKED"), 200

    # capacity check
    if event["bookedCount"] >= event["capacity"]:
        # offer waitlist status
        wl_existing = db()["waitlists"].find_one({"userId": user_id, "eventId": event_id, "status": "WAITING"})
        if wl_existing:
            return jsonify(status="FULL_ALREADY_WAITLISTED"), 200
        return jsonify(status="FULL_CAN_JOIN_WAITLIST"), 200

    now = datetime.now(timezone.utc).isoformat()

    # create booking + increment bookedCount
    db()["bookings"].insert_one({
        "userId": user_id,
        "eventId": event_id,
        "status": "BOOKED",
        "createdAt": now
    })
    db()["events"].update_one({"_id": e_id}, {"$inc": {"bookedCount": 1}, "$set": {"updatedAt": now}})

    return jsonify(status="BOOKED"), 201

@bp.post("/<event_id>/waitlist")
@jwt_required()
def join_waitlist(event_id):
    user_id = get_jwt_identity()
    e_id = oid(event_id)
    if not e_id:
        return jsonify(error="invalid event id"), 400

    event = db()["events"].find_one({"_id": e_id})
    if not event:
        return jsonify(error="event not found"), 404

    # if user already booked, no waitlist
    if db()["bookings"].find_one({"userId": user_id, "eventId": event_id, "status": "BOOKED"}):
        return jsonify(error="already booked"), 409

    # already waiting?
    if db()["waitlists"].find_one({"userId": user_id, "eventId": event_id, "status": "WAITING"}):
        return jsonify(status="ALREADY_WAITING"), 200

    now = datetime.now(timezone.utc).isoformat()
    # position = count + 1 (simple queue)
    pos = db()["waitlists"].count_documents({"eventId": event_id, "status": "WAITING"}) + 1

    db()["waitlists"].insert_one({
        "userId": user_id,
        "eventId": event_id,
        "position": pos,
        "status": "WAITING",
        "createdAt": now
    })

    return jsonify(status="WAITLISTED", position=pos), 201

@bp.post("/<event_id>/cancel")
@jwt_required()
def cancel_booking(event_id):
    user_id = get_jwt_identity()
    e_id = oid(event_id)
    if not e_id:
        return jsonify(error="invalid event id"), 400

    event = db()["events"].find_one({"_id": e_id})
    if not event:
        return jsonify(error="event not found"), 404

    booking = db()["bookings"].find_one({"userId": user_id, "eventId": event_id, "status": "BOOKED"})
    if not booking:
        return jsonify(error="no active booking to cancel"), 404

    now = datetime.now(timezone.utc).isoformat()

    # cancel booking + decrement bookedCount
    db()["bookings"].update_one({"_id": booking["_id"]}, {"$set": {"status": "CANCELLED"}})
    db()["events"].update_one({"_id": e_id}, {"$inc": {"bookedCount": -1}, "$set": {"updatedAt": now}})

    # auto-promote next waitlist user if capacity now available
    updated_event = db()["events"].find_one({"_id": e_id})
    if updated_event["bookedCount"] < updated_event["capacity"]:
        next_wl = db()["waitlists"].find_one(
            {"eventId": event_id, "status": "WAITING"},
            sort=[("position", 1)]
        )
        if next_wl:
            # promote: create booking
            db()["bookings"].insert_one({
                "userId": next_wl["userId"],
                "eventId": event_id,
                "status": "BOOKED",
                "createdAt": now
            })
            db()["events"].update_one({"_id": e_id}, {"$inc": {"bookedCount": 1}, "$set": {"updatedAt": now}})
            db()["waitlists"].update_one({"_id": next_wl["_id"]}, {"$set": {"status": "PROMOTED"}})

            # optional: email notification would go here

            return jsonify(status="CANCELLED_AND_PROMOTED_WAITLIST"), 200

    return jsonify(status="CANCELLED"), 200
