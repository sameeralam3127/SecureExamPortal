from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import User, Exam, ExamResult, Question, UserAnswer
from .. import db
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Show only exams assigned to this student (whether completed or not)
    assigned_results = ExamResult.query.filter_by(user_id=current_user.id).all()
    assigned_exam_ids = [res.exam_id for res in assigned_results]

    available_exams = Exam.query.filter(Exam.id.in_(assigned_exam_ids)).all()
    past_exams = assigned_results  # Includes both completed & not completed
    
    return render_template(
        'student/dashboard.html',
        available_exams=available_exams,
        past_exams=past_exams
    )


@student_bp.route('/exam/<int:exam_id>/start', methods=['GET', 'POST'])
@login_required
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    # Check if exam is active
    if not exam.is_active:
        flash('This exam is not available.', 'danger')
        return redirect(url_for('student.dashboard'))

    # Block only if exam is already COMPLETED
    completed_result = ExamResult.query.filter_by(
        exam_id=exam_id,
        user_id=current_user.id,
        completed=True
    ).first()
    if completed_result:
        flash('You have already taken this exam.', 'warning')
        return redirect(url_for('student.dashboard'))

    # Look for an assigned (but not completed) exam
    assigned_result = ExamResult.query.filter_by(
        exam_id=exam_id,
        user_id=current_user.id,
        completed=False
    ).first()

    if request.method == 'POST':
        score = 0
        answers = []
        for question in exam.questions:
            selected_answer = request.form.get(f'question_{question.id}')
            is_correct = selected_answer == question.correct_answer
            if is_correct:
                score += question.marks
            answers.append(
                UserAnswer(
                    question_id=question.id,
                    selected_answer=selected_answer,
                    is_correct=is_correct
                )
            )

        if assigned_result:
            # Update the assigned exam result
            assigned_result.score = score
            assigned_result.total_marks = exam.total_marks
            assigned_result.end_time = datetime.utcnow()
            assigned_result.is_passed = score >= exam.passing_marks
            assigned_result.completed = True
            assigned_result.answers = answers
        else:
            # If no assignment exists, create a new result
            new_result = ExamResult(
                exam_id=exam.id,
                user_id=current_user.id,
                score=score,
                total_marks=exam.total_marks,
                end_time=datetime.utcnow(),
                is_passed=score >= exam.passing_marks,
                completed=True,
                answers=answers
            )
            db.session.add(new_result)

        db.session.commit()
        flash('Exam submitted successfully!', 'success')
        return redirect(url_for('student.dashboard'))

    # If it's GET, render the exam
    return render_template('student/take_exam.html', exam=exam)


@student_bp.route('/exam/result/<int:result_id>')
@login_required
def view_result(result_id):
    result = ExamResult.query.get_or_404(result_id)
    
    if result.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('student.dashboard'))
    
    for answer in result.answers:
        answer.question = Question.query.get(answer.question_id)
    
    return render_template('student/view_result.html', result=result)
