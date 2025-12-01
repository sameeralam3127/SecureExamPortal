from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from .. import db
from ..models import Exam
from . import admin_bp
from .decorators import admin_required


# -------------------------
# View All Exams
# -------------------------
@admin_bp.route("/exams")
@admin_required
def admin_exams():
    exams = Exam.query.all()
    return render_template("admin/exams.html", exams=exams)


# -------------------------
# Create Exam
# -------------------------
@admin_bp.route("/exam/create", methods=["GET", "POST"])
@admin_required
def create_exam():
    if request.method == "POST":
        exam = Exam(
            title=request.form.get("title"),
            description=request.form.get("description"),
            duration=int(request.form.get("duration")),
            total_marks=int(request.form.get("total_marks")),
            passing_marks=int(request.form.get("passing_marks")),
            created_by=current_user.id,
        )
        db.session.add(exam)
        db.session.commit()
        flash("Exam created successfully!", "success")
        return redirect(url_for("admin.admin_exams"))
    return render_template("admin/create_exam.html")


# -------------------------
# Edit Exam
# -------------------------
@admin_bp.route("/exam/<int:exam_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if request.method == "POST":
        exam.title = request.form.get("title")
        exam.description = request.form.get("description")
        exam.duration = int(request.form.get("duration"))
        exam.total_marks = int(request.form.get("total_marks"))
        exam.passing_marks = int(request.form.get("passing_marks"))
        db.session.commit()
        flash("Exam updated successfully!", "success")
        return redirect(url_for("admin.admin_exams"))
    return render_template("admin/edit_exam.html", exam=exam)


# -------------------------
# Delete Exam
# -------------------------
@admin_bp.route("/exam/<int:exam_id>/delete", methods=["POST"])
@admin_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    try:
        db.session.delete(exam)
        db.session.commit()
        flash("Exam deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting exam. Please try again.", "danger")
        print(f"Error deleting exam: {str(e)}")
    return redirect(url_for("admin.admin_exams"))
