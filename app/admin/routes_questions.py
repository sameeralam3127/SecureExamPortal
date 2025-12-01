from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from .. import db
from ..models import Exam, Question
from .decorators import admin_required


@admin_bp.route("/exam/<int:exam_id>/questions", methods=["GET", "POST"])
@admin_required
def manage_questions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if request.method == "POST":
        question = Question(
            exam_id=exam_id,
            question_text=request.form.get("question_text"),
            option_a=request.form.get("option_a"),
            option_b=request.form.get("option_b"),
            option_c=request.form.get("option_c"),
            option_d=request.form.get("option_d"),
            correct_answer=request.form.get("correct_answer"),
            marks=int(request.form.get("marks", 1)),
        )
        db.session.add(question)
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for("admin.manage_questions", exam_id=exam_id))

    return render_template("admin/manage_questions.html", exam=exam)


@admin_bp.route("/question/<int:question_id>/delete", methods=["POST"])
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    exam_id = question.exam_id
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for("admin.manage_questions", exam_id=exam_id))
