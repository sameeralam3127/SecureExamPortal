from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# ---------------------------
# User Model (Local + Google)
# ---------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Local user info
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    # Google OAuth fields
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    picture = db.Column(db.String(512), nullable=True)

    # Common metadata
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    exams_taken = db.relationship("ExamResult", backref="student", lazy=True)

    # Password helpers
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------------------
# Exam Model
# ---------------------------
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)
    total_marks = db.Column(db.Integer)
    passing_marks = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    questions = db.relationship(
        "Question", backref="exam", lazy=True, cascade="all, delete-orphan"
    )
    results = db.relationship(
        "ExamResult", backref="exam", lazy=True, cascade="all, delete-orphan"
    )


# ---------------------------
# Question Model
# ---------------------------
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    marks = db.Column(db.Integer, default=1)


# ---------------------------
# Exam Result Model
# ---------------------------
class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(
        db.Integer, db.ForeignKey("exam.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    score = db.Column(db.Integer, default=0)
    total_marks = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_passed = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)

    # Relationships
    answers = db.relationship(
        "UserAnswer", backref="result", lazy=True, cascade="all, delete-orphan"
    )


# ---------------------------
# User Answer Model
# ---------------------------
class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(
        db.Integer, db.ForeignKey("exam_result.id", ondelete="CASCADE"), nullable=False
    )
    question_id = db.Column(
        db.Integer, db.ForeignKey("question.id", ondelete="CASCADE"), nullable=False
    )
    selected_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean)

    # Relationship
    question = db.relationship("Question", backref="user_answers")
