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
    
    available_exams = Exam.query.filter_by(is_active=True).all()
    past_exams = ExamResult.query.filter_by(user_id=current_user.id).all()
    
    return render_template('student/dashboard.html', available_exams=available_exams, past_exams=past_exams)

@student_bp.route('/exam/<int:exam_id>/start', methods=['GET', 'POST'])
@login_required
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    if not exam.is_active:
        flash('This exam is not available.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    existing_result = ExamResult.query.filter_by(exam_id=exam_id, user_id=current_user.id).first()
    if existing_result:
        flash('You have already taken this exam.', 'warning')
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        score = 0
        answers = []
        for question in exam.questions:
            selected_answer = request.form.get(f'question_{question.id}')
            is_correct = selected_answer == question.correct_answer
            if is_correct:
                score += question.marks
            answers.append(UserAnswer(question_id=question.id, selected_answer=selected_answer, is_correct=is_correct))
        
        result = ExamResult(
            exam_id=exam.id,
            user_id=current_user.id,
            score=score,
            total_marks=exam.total_marks,
            end_time=datetime.utcnow(),
            is_passed=score >= exam.passing_marks,
            answers=answers
        )
        db.session.add(result)
        db.session.commit()
        
        flash('Exam submitted successfully!', 'success')
        return redirect(url_for('student.dashboard'))
    
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
