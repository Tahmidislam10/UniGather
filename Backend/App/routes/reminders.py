from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from ..extensions import mongo_client

bp = Blueprint("reminders", __name__)

def db():
    return mongo_client.get_default_database()

@bp.get("")
@jwt_required()
def my_upcoming_events():
    user_id = get_jwt_identity()

    bookings = list(db()["bookings"].find({"userId": user_id, "status": "BOOKED"}))
    event_ids = [b["eventId"] for b in bookings]

    # fetch events by _id
    obj_ids = []
    for eid in event_ids:
        try:
            obj_ids.append(ObjectId(eid))
        except Exception:
            pass

    events = []
    if obj_ids:
        for e in db()["events"].find({"_id": {"$in": obj_ids}}).sort("date", 1):
            e["id"] = str(e.pop("_id"))
            events.append(e)

    return jsonify(upcoming=events), 200
