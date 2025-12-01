import os

from dotenv import load_dotenv
from flask import Flask
from flask_dance.contrib.google import make_google_blueprint
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

    # --- Ensure database folder exists ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    os.makedirs(DATA_DIR, exist_ok=True)

    db_path = os.path.join(DATA_DIR, "exam_portal.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Initialize extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --- Import models ---
    from . import models
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Import Blueprints ---
    from .admin import admin_bp
    from .auth.routes import auth_bp
    from .student.routes import student_bp

    # --- Register Blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(student_bp, url_prefix="/student")

    # --- Google OAuth Setup ---
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Only for local testing

    google_bp = make_google_blueprint(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_to="auth.google_callback",  # where Google redirects after login
    )

    app.register_blueprint(google_bp, url_prefix="/login")

    return app
