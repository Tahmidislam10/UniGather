def user_doc(email: str, hashed_pw: str, role: str) -> dict:
    return {
        "email": email,
        "password": hashed_pw,
        "role": role,
        "createdAt": None,  # optional: set in route
    }
