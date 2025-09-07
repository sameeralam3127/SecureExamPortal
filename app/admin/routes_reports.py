from flask import render_template, request, flash
from . import admin_bp
from ..models import Exam, ExamResult, User
from .decorators import admin_required
from datetime import datetime, timedelta

@admin_bp.route("/reports")
@admin_required
def admin_reports():
    exam_id = request.args.get("exam_id", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    status = request.args.get("status")

    query = ExamResult.query.join(User).join(Exam).order_by(ExamResult.start_time.desc())

    if exam_id:
        query = query.filter(ExamResult.exam_id == exam_id)
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(ExamResult.start_time >= date_from_dt)
        except ValueError:
            flash("Invalid date format for Date From", "warning")
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(ExamResult.start_time < date_to_dt)
        except ValueError:
            flash("Invalid date format for Date To", "warning")

    if status == "passed":
        query = query.filter(ExamResult.is_passed.is_(True))
    elif status == "failed":
        query = query.filter(ExamResult.is_passed.is_(False))

    results = query.all()
    total_results = len(results)
    if total_results > 0:
        passed_results = sum(1 for r in results if r.is_passed)
        pass_rate = (passed_results / total_results) * 100
        avg_score = sum((r.score / r.total_marks) * 100 for r in results) / total_results
        unique_students = len(set(r.user_id for r in results))
    else:
        pass_rate = avg_score = unique_students = 0

    stats = {
        "total_results": total_results,
        "pass_rate": round(pass_rate, 1),
        "avg_score": round(avg_score, 1),
        "unique_students": unique_students,
    }

    exams = Exam.query.order_by(Exam.title).all()
    return render_template(
        "admin/reports.html",
        exams=exams,
        results=results,
        stats=stats,
        filters={"exam_id": exam_id, "date_from": date_from, "date_to": date_to, "status": status},
    )
