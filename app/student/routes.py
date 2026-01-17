from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..models import Exam, ExamResult, Question, UserAnswer
from ..utils.exam_randomizer import generate_random_order

student_bp = Blueprint("student", __name__)


# -------------------------
# Student Dashboard (UNCHANGED)
# -------------------------
@student_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    assigned_results = ExamResult.query.filter_by(user_id=current_user.id).all()

    past_exams = [res for res in assigned_results if res.completed]
    not_attempted_results = [res for res in assigned_results if not res.completed]
    available_exams = [res.exam for res in not_attempted_results]

    return render_template(
        "student/dashboard.html",
        available_exams=available_exams,
        past_exams=past_exams,
        not_attempted_results=not_attempted_results,
    )


# -------------------------
# Start Exam (Randomized + Correct Timer)
# -------------------------
@student_bp.route("/exam/<int:exam_id>/start", methods=["GET", "POST"])
@login_required
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    # ---------- EXISTING VALIDATIONS ----------
    if not exam.is_active:
        flash("This exam is not available.", "danger")
        return redirect(url_for("student.dashboard"))

    completed_result = ExamResult.query.filter_by(
        exam_id=exam_id,
        user_id=current_user.id,
        completed=True,
    ).first()

    if completed_result:
        flash("You have already taken this exam.", "warning")
        return redirect(url_for("student.dashboard"))

    assigned_result = ExamResult.query.filter_by(
        exam_id=exam_id,
        user_id=current_user.id,
        completed=False,
    ).first()

    if not assigned_result:
        flash("Exam not assigned.", "danger")
        return redirect(url_for("student.dashboard"))

    # --------------------------------------------------
    # ✅ FIX 1: START TIMER ON FIRST STUDENT OPEN
    # (assignment time ≠ attempt time)
    # --------------------------------------------------
    if assigned_result.start_time is None:
        assigned_result.start_time = datetime.utcnow()
        db.session.commit()

    # --------------------------------------------------
    # POST — SUBMIT EXAM (UNCHANGED)
    # --------------------------------------------------
    if request.method == "POST":
        score = 0
        answers = []

        for question in exam.questions:
            selected_answer = request.form.get(f"question_{question.id}")
            is_correct = selected_answer == question.correct_answer

            if is_correct:
                score += question.marks

            answers.append(
                UserAnswer(
                    question_id=question.id,
                    selected_answer=selected_answer,
                    is_correct=is_correct,
                )
            )

        assigned_result.score = score
        assigned_result.total_marks = exam.total_marks
        assigned_result.end_time = datetime.utcnow()
        assigned_result.is_passed = score >= exam.passing_marks
        assigned_result.completed = True
        assigned_result.answers = answers

        db.session.commit()
        flash("Exam submitted successfully!", "success")
        return redirect(url_for("student.dashboard"))

    # --------------------------------------------------
    # GET — RANDOMIZE QUESTIONS (UNCHANGED)
    # --------------------------------------------------
    if not assigned_result.question_order:
        question_order, option_order = generate_random_order(exam)
        assigned_result.question_order = question_order
        assigned_result.option_order = option_order
        db.session.commit()

    questions = Question.query.filter(
        Question.id.in_(assigned_result.question_order)
    ).all()

    question_map = {q.id: q for q in questions}
    ordered_questions = [
        question_map[qid] for qid in assigned_result.question_order
    ]

    # --------------------------------------------------
    # ⏱️ FIX 2: SERVER-SIDE TIMER CALCULATION
    # --------------------------------------------------
    exam_end_time = assigned_result.start_time + timedelta(
        minutes=exam.duration or 0
    )

    remaining_seconds = int(
        (exam_end_time - datetime.utcnow()).total_seconds()
    )

    if remaining_seconds < 0:
        remaining_seconds = 0

    return render_template(
        "student/take_exam.html",
        exam=exam,
        questions=ordered_questions,
        option_order=assigned_result.option_order,
        remaining_seconds=remaining_seconds,
    )


# -------------------------
# View Exam Result (UNCHANGED)
# -------------------------
@student_bp.route("/exam/result/<int:result_id>")
@login_required
def view_result(result_id):
    result = ExamResult.query.get_or_404(result_id)

    if result.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied", "danger")
        return redirect(url_for("student.dashboard"))

    for answer in result.answers:
        answer.question = Question.query.get(answer.question_id)

    return render_template("student/view_result.html", result=result)
