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
    # 1. Get the plain text email and password from the form
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    # 2. Find the user in DynamoDB by their email
    response = users_table.scan(
        FilterExpression=Attr("email").eq(email)
    )
    items = response.get("Items", [])

    # 3. If no user found with that email
    if not items:
        return "Invalid email or password", 401

    user = items[0]
    stored_hashed_password = user.get("password")

    # 4. SECURITY CHECK
    if not check_password_hash(stored_hashed_password, password):
        return "Invalid email or password", 401

    # 5. Success: Set cookies and redirect
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
    # 1. Retrieve and clean form data
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    # 2. Basic validation
    if not full_name or not email or not password:
        return "All fields are required", 400

    # 3. Academic email restriction (.ac.uk)
    if not email.endswith(".ac.uk"):
        return render_template(
            "register.html",
            error="Registration is restricted to ac.uk email addresses."
        ), 400

    # 4. Check if the email is already in use
    existing_user = users_table.scan(
        FilterExpression=Attr("email").eq(email)
    )
    if existing_user.get("Items"):
        return "An account with this email already exists", 400

    # 5. Security: Hash the password
    hashed_password = generate_password_hash(
        password,
        method="pbkdf2:sha256"
    )

    # 6. Prepare the user object
    new_user = {
        "id": str(uuid.uuid4()),
        "full_name": full_name,
        "email": email,
        "password": hashed_password,
        "role": "student",
        "booked_events": []
    }

    # 7. Save to database
    try:
        users_table.put_item(Item=new_user)
        return redirect("/login")
    except Exception as e:
        print(f"Registration Error: {e}")
        return "Failed to create account. Please try again later.", 500
