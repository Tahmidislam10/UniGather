def booking_doc(user_id: str, event_id: str) -> dict:
    return {
        "userId": user_id,
        "eventId": event_id,
        "status": "BOOKED",   # BOOKED | CANCELLED
        "createdAt": None
    }

def waitlist_doc(user_id: str, event_id: str, position: int) -> dict:
    return {
        "userId": user_id,
        "eventId": event_id,
        "position": position,
        "status": "WAITING",  # WAITING | PROMOTED | REMOVED
        "createdAt": None
    }
