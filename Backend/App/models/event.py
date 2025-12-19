def event_doc(title: str, category: str, date: str, location: str, capacity: int, organiser_id: str) -> dict:
    return {
        "title": title,
        "category": category,
        "date": date,                 # ISO string
        "location": location,
        "capacity": capacity,
        "bookedCount": 0,
        "organiserId": organiser_id,   # JWT identity string
        "createdAt": None,            # optional
        "updatedAt": None             # optional
    }
