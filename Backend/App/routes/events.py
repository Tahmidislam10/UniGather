from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timezone
from bson import ObjectId
from ..extensions import mongo_client
from ..utils.authz import require_roles
from ..utils.validators import validate_event_payload

bp = Blueprint("events", __name__)

def db():
    return mongo_client.get_default_database()

def oid(id_str: str):
    try:
        return ObjectId(id_str)
    except Exception:
        return None

def serialise(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

@bp.post("")
@jwt_required()
@require_roles("organiser", "admin")
def create_event():
    data = request.get_json(force=True)

    ok, msg = validate_event_payload(data)
    if not ok:
        return jsonify(error=msg), 400

    organiser_id = get_jwt_identity()
    title = data["title"].strip()
    category = (data.get("category") or "").strip()
    date = data["date"].strip()
    location = data["location"].strip()
    capacity = int(data["capacity"])

    now = datetime.now(timezone.utc).isoformat()

    res = db()["events"].insert_one({
        "title": title,
        "category": category,
        "date": date,
        "location": location,
        "capacity": capacity,
        "bookedCount": 0,
        "organiserId": organiser_id,
        "createdAt": now,
        "updatedAt": now
    })
    return jsonify(id=str(res.inserted_id)), 201

@bp.get("")
def list_events():
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    date_from = (request.args.get("date_from") or "").strip()
    date_to = (request.args.get("date_to") or "").strip()

    query = {}
    if q:
        query["title"] = {"$regex": q, "$options": "i"}  # text-ish search
    if category:
        query["category"] = category
    if date_from or date_to:
        query["date"] = {}
        if date_from:
            query["date"]["$gte"] = date_from
        if date_to:
            query["date"]["$lte"] = date_to

    events = [serialise(e) for e in db()["events"].find(query).sort("date", 1)]
    return jsonify(events=events), 200

@bp.get("/<event_id>")
def get_event(event_id):
    _id = oid(event_id)
    if not _id:
        return jsonify(error="invalid event id"), 400

    e = db()["events"].find_one({"_id": _id})
    if not e:
        return jsonify(error="event not found"), 404
    return jsonify(event=serialise(e)), 200

@bp.patch("/<event_id>")
@jwt_required()
@require_roles("organiser", "admin")
def update_event(event_id):
    _id = oid(event_id)
    if not _id:
        return jsonify(error="invalid event id"), 400

    data = request.get_json(force=True)
    user_id = get_jwt_identity()
    role = get_jwt().get("role")

    event = db()["events"].find_one({"_id": _id})
    if not event:
        return jsonify(error="event not found"), 404

    # organiser can only update own events (admin can update all)
    if role != "admin" and event.get("organiserId") != user_id:
        return jsonify(error="forbidden: not your event"), 403

    updates = {}
    for field in ("title", "category", "date", "location", "capacity"):
        if field in data:
            updates[field] = data[field]

    # basic validation on capacity/date if supplied
    if "capacity" in updates:
        try:
            updates["capacity"] = int(updates["capacity"])
            if updates["capacity"] <= 0:
                return jsonify(error="capacity must be > 0"), 400
        except Exception:
            return jsonify(error="capacity must be integer"), 400

    if "date" in updates:
        # keep as ISO string; frontend/backends agree on ISO
        if not isinstance(updates["date"], str) or not updates["date"].strip():
            return jsonify(error="date must be a non-empty ISO string"), 400

    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    db()["events"].update_one({"_id": _id}, {"$set": updates})
    return jsonify(message="updated"), 200

@bp.delete("/<event_id>")
@jwt_required()
@require_roles("organiser", "admin")
def delete_event(event_id):
    _id = oid(event_id)
    if not _id:
        return jsonify(error="invalid event id"), 400

    user_id = get_jwt_identity()
    role = get_jwt().get("role")

    event = db()["events"].find_one({"_id": _id})
    if not event:
        return jsonify(error="event not found"), 404

    if role != "admin" and event.get("organiserId") != user_id:
        return jsonify(error="forbidden: not your event"), 403

    # optional: also delete bookings/waitlist linked to event
    db()["bookings"].delete_many({"eventId": event_id})
    db()["waitlists"].delete_many({"eventId": event_id})
    db()["events"].delete_one({"_id": _id})

    return jsonify(message="deleted"), 200
