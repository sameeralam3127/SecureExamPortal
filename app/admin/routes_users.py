from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from .. import db
from ..models import User, Exam, ExamResult
from datetime import datetime
from .decorators import admin_required

# -------------------------
# Manage Users
# -------------------------
@admin_bp.route("/users", methods=["GET", "POST"])
@admin_required
def admin_users():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        is_admin = "is_admin" in request.form

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for("admin.admin_users"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("admin.admin_users"))

        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("User created successfully!", "success")
        return redirect(url_for("admin.admin_users"))

    users = User.query.filter_by(is_admin=False).all()
    return render_template("admin/users.html", users=users)


# -------------------------
# Edit User
# -------------------------
@admin_bp.route("/user/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.username = request.form.get("username")
        user.email = request.form.get("email")
        if request.form.get("password"):
            user.set_password(request.form.get("password"))
        user.is_admin = "is_admin" in request.form
        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("admin.admin_users"))
    return render_template("admin/edit_user.html", user=user)


# -------------------------
# Assign Exam to User
# -------------------------
@admin_bp.route("/user/<int:user_id>/assign", methods=["GET", "POST"])
@admin_required
def assign_exam(user_id):
    user = User.query.get_or_404(user_id)
    exams = Exam.query.all()
    # Only consider completed exams as "taken"
    taken_exams = [res.exam_id for res in user.exams_taken if res.completed]

    if request.method == "POST":
        exam_id = request.form.get("exam_id")
        exam = Exam.query.get_or_404(exam_id)

        # Check only for completed exams
        existing = ExamResult.query.filter_by(user_id=user.id, exam_id=exam.id, completed=True).first()
        if existing:
            flash(f"{user.username} has already completed {exam.title}.", "warning")
            return redirect(url_for("admin.assign_exam", user_id=user.id))

        # Check if there is already an assigned (but not completed) exam
        assigned = ExamResult.query.filter_by(user_id=user.id, exam_id=exam.id, completed=False).first()
        if assigned:
            flash(f"{user.username} has already been assigned {exam.title}.", "info")
            return redirect(url_for("admin.assign_exam", user_id=user.id))

        # Assign new exam
        exam_result = ExamResult(
            user_id=user.id,
            exam_id=exam.id,
            score=0,
            total_marks=exam.total_marks,
            is_passed=False,
            completed=False,
            start_time=datetime.utcnow()
        )
        db.session.add(exam_result)
        db.session.commit()
        flash(f"Exam '{exam.title}' assigned to {user.username}.", "success")
        return redirect(url_for("admin.assign_exam", user_id=user.id))

    return render_template("admin/assign_exam.html", user=user, exams=exams, taken_exams=taken_exams)



# -------------------------
# Delete Exam Result
# -------------------------
@admin_bp.route("/result/<int:result_id>/delete", methods=["POST"])
@admin_required
def delete_result(result_id):
    result = ExamResult.query.get_or_404(result_id)
    user_id = result.user_id
    db.session.delete(result)
    db.session.commit()
    flash("Exam result deleted. Student can now retake the exam.", "success")
    return redirect(url_for("admin.assign_exam", user_id=user_id))
