from flask import Blueprint, request, jsonify

bp = Blueprint("events", __name__)

# TEMP: in-memory store (Mongo replacement)
EVENTS = []


@bp.post("")
def create_event():
    data = request.get_json(force=True)

    event = {
        "id": len(EVENTS) + 1,
        "title": data.get("title"),
        "category": data.get("category"),
        "date": data.get("date"),
        "location": data.get("location"),
        "capacity": int(data.get("capacity", 0)),
    }

    EVENTS.append(event)
    return jsonify(event=event), 201


@bp.get("")
def list_events():
    return jsonify(events=EVENTS), 200


@bp.get("/test")
def test_events():
    return jsonify(message="events route works"), 200
