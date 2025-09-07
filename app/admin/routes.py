from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import User, Exam, Question, ExamResult
from .. import db
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

# Admin dashboard
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    
    exams = Exam.query.all()
    users = User.query.filter_by(is_admin=False).all()
    results = ExamResult.query.order_by(ExamResult.start_time.desc()).all()
    
    return render_template('admin/dashboard.html', exams=exams, users=users, results=results)

# Manage Exams
@admin_bp.route('/exams')
@login_required
def admin_exams():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    exams = Exam.query.all()
    return render_template('admin/exams.html', exams=exams)

@admin_bp.route('/exam/create', methods=['GET', 'POST'])
@login_required
def create_exam():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        exam = Exam(
            title=request.form.get('title'),
            description=request.form.get('description'),
            duration=int(request.form.get('duration')),
            total_marks=int(request.form.get('total_marks')),
            passing_marks=int(request.form.get('passing_marks')),
            created_by=current_user.id
        )
        db.session.add(exam)
        db.session.commit()
        flash('Exam created successfully!')
        return redirect(url_for('admin.admin_exams'))
    
    return render_template('admin/create_exam.html')

@admin_bp.route('/exam/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        exam.title = request.form.get('title')
        exam.description = request.form.get('description')
        exam.duration = int(request.form.get('duration'))
        exam.total_marks = int(request.form.get('total_marks'))
        exam.passing_marks = int(request.form.get('passing_marks'))
        db.session.commit()
        flash('Exam updated successfully!')
        return redirect(url_for('admin.admin_exams'))
    
    return render_template('admin/edit_exam.html', exam=exam)

@admin_bp.route('/exam/<int:exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    
    try:
        db.session.delete(exam)
        db.session.commit()
        flash('Exam deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting exam. Please try again.', 'danger')
        print(f"Error deleting exam: {str(e)}")
    
    return redirect(url_for('admin.admin_exams'))

# Manage Questions
@admin_bp.route('/exam/<int:exam_id>/questions', methods=['GET', 'POST'])
@login_required
def manage_questions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        question = Question(
            exam_id=exam_id,
            question_text=request.form.get('question_text'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_answer=request.form.get('correct_answer'),
            marks=int(request.form.get('marks', 1))
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.manage_questions', exam_id=exam_id))
    
    return render_template('admin/manage_questions.html', exam=exam)

@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    
    exam_id = question.exam_id
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.manage_questions', exam_id=exam_id))

# Manage Users
@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('admin.admin_users'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('admin.admin_users'))
        
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('admin.admin_users'))
    
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

# Reports
@admin_bp.route('/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('student.dashboard'))
    
    exam_id = request.args.get('exam_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    
    query = ExamResult.query.join(User).join(Exam).order_by(ExamResult.start_time.desc())
    
    if exam_id:
        query = query.filter(ExamResult.exam_id == exam_id)
    
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ExamResult.start_time >= date_from_dt)
        except ValueError:
            flash('Invalid date format for Date From', 'warning')
    
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ExamResult.start_time < date_to_dt)
        except ValueError:
            flash('Invalid date format for Date To', 'warning')
    
    if status:
        if status == 'passed':
            query = query.filter(ExamResult.is_passed == True)
        elif status == 'failed':
            query = query.filter(ExamResult.is_passed == False)
    
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
        'total_results': total_results,
        'pass_rate': round(pass_rate, 1),
        'avg_score': round(avg_score, 1),
        'unique_students': unique_students
    }
    
    exams = Exam.query.order_by(Exam.title).all()
    
    return render_template('admin/reports.html',
                           exams=exams,
                           results=results,
                           stats=stats,
                           filters={'exam_id': exam_id, 'date_from': date_from, 'date_to': date_to, 'status': status})
