from flask import render_template, request, flash, redirect, url_for
from . import admin_bp
from .. import db
from ..models import Exam, ExamResult, User
from .decorators import admin_required
from datetime import datetime, timedelta

# -------------------------
# Exam Reports (Admin)
# -------------------------
@admin_bp.route("/reports", methods=["GET"], endpoint="admin_reports")
@admin_required
def reports():
    exam_id = request.args.get("exam_id", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    status = request.args.get("status")

    # Base query
    query = ExamResult.query.join(User).join(Exam).order_by(ExamResult.start_time.desc())

    # Apply filters
    if exam_id:
        query = query.filter(ExamResult.exam_id == exam_id)

    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(ExamResult.start_time >= date_from_dt)
        except ValueError:
            flash("Invalid 'Date From' format", "warning")

    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(ExamResult.start_time < date_to_dt)
        except ValueError:
            flash("Invalid 'Date To' format", "warning")

    if status == "passed":
        query = query.filter(ExamResult.is_passed.is_(True))
    elif status == "failed":
        query = query.filter(ExamResult.is_passed.is_(False))

    results = query.all()

    # Compute statistics
    total = len(results)
    passed = sum(1 for r in results if r.is_passed)
    pass_rate = round((passed / total) * 100, 1) if total else 0
    avg_score = round(sum((r.score / r.total_marks) * 100 for r in results) / total, 1) if total else 0
    unique_students = len(set(r.user_id for r in results))

    stats = {
        "total": total,
        "pass_rate": pass_rate,
        "avg_score": avg_score,
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


# -------------------------
# Delete Exam Result (Reports Only)
# -------------------------
@admin_bp.route("/reports/result/<int:result_id>/delete", methods=["POST"])
@admin_required
def delete_report_result(result_id):
    result = ExamResult.query.get_or_404(result_id)
    db.session.delete(result)
    db.session.commit()
    flash("Exam result deleted successfully.", "success")
    return redirect(url_for("admin.admin_reports"))
