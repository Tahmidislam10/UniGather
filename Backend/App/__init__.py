from flask import Flask, jsonify
from .config import Config
from .extensions import jwt, init_mongo



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    jwt.init_app(app)
    #init_mongo(app)

    from .routes.auth import bp as auth_bp
    from .routes.events import bp as events_bp
    from .routes.bookings import bp as bookings_bp
    from .routes.reminders import bp as reminders_bp
    from .routes.pdfs import bp as pdfs_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    app.register_blueprint(reminders_bp, url_prefix="/api/reminders")
    app.register_blueprint(pdfs_bp, url_prefix="/api/pdfs")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
