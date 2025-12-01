from flask import render_template, request, flash, redirect, url_for
from . import admin_bp
from .. import db
from ..models import Exam, ExamResult, User
from .decorators import admin_required
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload


# -------------------------------
# Admin Reports Route
# -------------------------------
@admin_bp.route("/reports", methods=["GET"], endpoint="admin_reports")
@admin_required
def reports():
    # Get filter values from query string
    exam_id = request.args.get("exam_id", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    status = request.args.get("status")

    # Base query with eager loading for relationships
    query = ExamResult.query.options(
        joinedload(ExamResult.student), joinedload(ExamResult.exam)
    ).order_by(ExamResult.start_time.desc())

    # Apply exam filter
    if exam_id:
        query = query.filter(ExamResult.exam_id == exam_id)

    # Apply date filters safely
    date_from_value, date_to_value = "", ""
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(ExamResult.start_time >= dt_from)
            date_from_value = dt_from.strftime("%Y-%m-%d")
        except ValueError:
            flash("Invalid 'Date From'. Use YYYY-MM-DD.", "warning")

    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(ExamResult.start_time < dt_to)
            date_to_value = (dt_to - timedelta(days=1)).strftime("%Y-%m-%d")
        except ValueError:
            flash("Invalid 'Date To'. Use YYYY-MM-DD.", "warning")

    # Apply status filter
    if status == "passed":
        query = query.filter(ExamResult.is_passed.is_(True))
    elif status == "failed":
        query = query.filter(ExamResult.is_passed.is_(False))

    # Fetch results
    results = query.all()

    # Compute statistics safely
    total = len(results)
    passed = sum(1 for r in results if r.is_passed)
    pass_rate = round((passed / total) * 100, 1) if total else 0

    valid_scores = [
        r.score / r.total_marks * 100
        for r in results
        if r.total_marks and r.total_marks > 0
    ]
    avg_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0

    unique_students = len(set(r.user_id for r in results))

    stats = {
        "total": total,
        "pass_rate": pass_rate,
        "avg_score": avg_score,
        "unique_students": unique_students,
    }

    # Load exams for filter dropdown
    exams = Exam.query.order_by(Exam.title).all()

    return render_template(
        "admin/reports.html",
        exams=exams,
        results=results,
        stats=stats,
        filters={
            "exam_id": exam_id,
            "date_from": date_from_value,
            "date_to": date_to_value,
            "status": status,
        },
    )


# -------------------------------
# Delete an Exam Result
# -------------------------------
@admin_bp.route("/reports/result/<int:result_id>/delete", methods=["POST"])
@admin_required
def delete_report_result(result_id):
    result = ExamResult.query.get_or_404(result_id)
    db.session.delete(result)
    db.session.commit()
    flash("Exam result deleted successfully.", "success")
    return redirect(url_for("admin.admin_reports"))
