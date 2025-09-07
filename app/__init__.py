from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)

    # Ensure database folder exists
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
    os.makedirs(DATA_DIR, exist_ok=True)

    db_path = os.path.join(DATA_DIR, 'exam_portal.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Import Blueprints
    from .auth.routes import auth_bp
    from .admin import admin_bp      # ✅ admin blueprint
    from .student.routes import student_bp

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')

    return app
