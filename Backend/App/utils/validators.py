from datetime import datetime

def is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except Exception:
        return False

def validate_event_payload(data: dict) -> tuple[bool, str]:
    title = (data.get("title") or "").strip()
    date = (data.get("date") or "").strip()
    location = (data.get("location") or "").strip()
    capacity = data.get("capacity")

    if not title:
        return False, "title is required"
    if not date or not is_iso_datetime(date):
        return False, "date is required and must be ISO format (e.g. 2026-01-30T18:00:00Z)"
    if not location:
        return False, "location is required"
    try:
        capacity = int(capacity)
        if capacity <= 0:
            return False, "capacity must be > 0"
    except Exception:
        return False, "capacity must be an integer"

    return True, ""
