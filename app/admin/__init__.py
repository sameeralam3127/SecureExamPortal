from flask import Blueprint
import os
from flask import Flask
from flask_mail import Mail
from dotenv import load_dotenv

admin_bp = Blueprint("admin", __name__)

# Import modular route files
from . import (
    routes_dashboard,
    routes_exams,
    routes_questions,
    routes_reports,
    routes_users,
)


