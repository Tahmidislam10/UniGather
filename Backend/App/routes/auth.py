from flask import Blueprint, request, jsonify
from passlib.hash import bcrypt
from flask_jwt_extended import create_access_token
from datetime import datetime, timezone
from bson import ObjectId
from ..extensions import mongo_client

bp = Blueprint("auth", __name__)

def db():
    return mongo_client.get_default_database()

@bp.post("/register")
def register():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or "student"

    if not email or not password:
        return jsonify(error="email and password are required"), 400
    if role not in ("student", "organiser", "admin"):
        return jsonify(error="role must be student/organiser/admin"), 400

    if db()["users"].find_one({"email": email}):
        return jsonify(error="email already exists"), 409

    hashed = bcrypt.hash(password)
    db()["users"].insert_one({
        "email": email,
        "password": hashed,
        "role": role,
        "createdAt": datetime.now(timezone.utc).isoformat()
    })

    return jsonify(message="registered"), 201

@bp.post("/login")
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = db()["users"].find_one({"email": email})
    if not user or not bcrypt.verify(password, user["password"]):
        return jsonify(error="invalid credentials"), 401

    token = create_access_token(identity=str(user["_id"]), additional_claims={"role": user["role"]})
    return jsonify(access_token=token, role=user["role"]), 200
