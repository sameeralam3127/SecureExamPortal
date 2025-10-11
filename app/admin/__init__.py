from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import modular route files
from . import routes_exams, routes_questions, routes_users, routes_reports, routes_dashboard
