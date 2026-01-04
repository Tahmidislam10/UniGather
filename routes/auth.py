import uuid
from flask import Blueprint, request, redirect, make_response, render_template
from boto3.dynamodb.conditions import Attr
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

auth = Blueprint("auth", __name__)
db = get_db()
users_table = db.Table("users")


# LOGIN


@auth.post("/login")
def login():
    # Gets the plain text email and password from the form
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    # Finds the user in DynamoDB via their provided email
    response = users_table.scan(
        FilterExpression=Attr("email").eq(email)
    )
    items = response.get("Items", [])

    # Error if an invalid email is provided
    if not items:
        return "Invalid email or password", 401

    user = items[0]
    stored_hashed_password = user.get("password")

    # Hashes the provided password and checks against the stored hashed password
    if not check_password_hash(stored_hashed_password, password):
        return "Invalid email or password", 401

    # If not returned by now, previous checks must have been successes
    display_name = user.get("full_name", user.get("username", "User"))

    response = make_response(redirect("/events-page"))
    response.set_cookie("user_id", user["id"])
    response.set_cookie("role", user["role"])
    response.set_cookie("username", display_name)

    return response



# LOGOUT

@auth.route("/logout")
def logout():
    response = make_response(redirect("/"))
    response.set_cookie("user_id", "", expires=0)
    response.set_cookie("role", "", expires=0)
    response.set_cookie("username", "", expires=0)
    return response



# REGISTER


@auth.post("/register")
def register():
    # Gets the plain text name, email and password from the form
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    # Basic validation to ensure all fields were provided
    if not full_name or not email or not password:
        return "All fields are required", 400

    # Checks that the email address is an academic email (.ac.uk)
    if not email.endswith(".ac.uk"):
        return render_template(
            "register.html",
            error="Registration is restricted to ac.uk email addresses."
        ), 400

    # Checks if the email is already in use
    existing_user = users_table.scan(
        FilterExpression=Attr("email").eq(email)
    )
    if existing_user.get("Items"):
        return "An account with this email already exists", 400

    # Hashes the password (do not store plain text passwords)
    hashed_password = generate_password_hash(
        password,
        method="pbkdf2:sha256"
    )

    # Prepares the new user's entry
    new_user = {
        "id": str(uuid.uuid4()),
        "full_name": full_name,
        "email": email,
        "password": hashed_password,
        "role": "student",
        "booked_events": []
    }

    # Saves to database
    try:
        users_table.put_item(Item=new_user)
        return redirect("/login")
    except Exception as e:
        print(f"Registration Error: {e}")
        return "Failed to create account. Please try again later.", 500
