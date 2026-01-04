from flask import Blueprint, render_template

pages = Blueprint("pages", __name__)

@pages.route("/")
def home():
    return render_template("index.html")

@pages.route("/events-page")
def events_page():
    return render_template("events.html")

@pages.route("/create")
def create_page():
    return render_template("create.html")

@pages.route("/about")
def about_page():
    return render_template("about.html")

@pages.route("/register")
def register_page():
    return render_template("register.html")

@pages.route("/login")
def login_page():
    return render_template("login.html")


