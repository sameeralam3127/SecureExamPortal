from flask import render_template
from . import admin_bp
from .decorators import admin_required
from ..models import Exam, User, ExamResult

@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    # You can pass exams, users, and results as needed
    exams = Exam.query.all()
    users = User.query.filter_by(is_admin=False).all()
    results = ExamResult.query.order_by(ExamResult.start_time.desc()).all()
    return render_template("admin/dashboard.html", exams=exams, users=users, results=results)
