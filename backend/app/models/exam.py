from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.db import Base


class AttemptStatus(str, Enum):
    in_progress = "in_progress"
    submitted = "submitted"


class Exam(Base):
    __tablename__ = "portal_exams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("portal_users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_by = relationship("User", back_populates="created_exams")
    questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    assignments = relationship("ExamAssignment", back_populates="exam", cascade="all, delete-orphan")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("portal_exams.id", ondelete="CASCADE"), index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(String(255), nullable=False)
    option_b: Mapped[str] = mapped_column(String(255), nullable=False)
    option_c: Mapped[str] = mapped_column(String(255), nullable=False)
    option_d: Mapped[str] = mapped_column(String(255), nullable=False)
    correct_option: Mapped[str] = mapped_column(String(1), nullable=False)
    marks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    exam = relationship("Exam", back_populates="questions")
    answers = relationship("AttemptAnswer", back_populates="question", cascade="all, delete-orphan")


class ExamAssignment(Base):
    __tablename__ = "exam_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("portal_exams.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("portal_users.id", ondelete="CASCADE"), index=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    exam = relationship("Exam", back_populates="assignments")
    student = relationship("User", back_populates="assignments", foreign_keys=[student_id])
    attempts = relationship("ExamAttempt", back_populates="assignment", cascade="all, delete-orphan")


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("exam_assignments.id", ondelete="CASCADE"),
        index=True,
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("portal_users.id", ondelete="CASCADE"), index=True)
    status: Mapped[AttemptStatus] = mapped_column(
        SqlEnum(AttemptStatus, name="attempt_status"),
        nullable=False,
        default=AttemptStatus.in_progress,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_marks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignment = relationship("ExamAssignment", back_populates="attempts")
    student = relationship("User", back_populates="attempts")
    answers = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("exam_attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("exam_questions.id", ondelete="CASCADE"), index=True)
    selected_option: Mapped[str] = mapped_column(String(1), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    marks_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("ExamQuestion", back_populates="answers")
