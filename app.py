from flask import Flask

# Import blueprints
from routes.pages import pages
from routes.auth import auth
from routes.events import events
from routes.admin import admin
from routes.analytics import analytics

app = Flask(__name__)

# Register blueprints
app.register_blueprint(pages)
app.register_blueprint(auth)
app.register_blueprint(events)
app.register_blueprint(admin)
app.register_blueprint(analytics)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
