from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.db import Base


class UserRole(str, Enum):
    admin = "admin"
    student = "student"


class User(Base):
    __tablename__ = "portal_users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.student,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_exams = relationship("Exam", back_populates="created_by")
    assignments = relationship(
        "ExamAssignment",
        back_populates="student",
        cascade="all, delete-orphan",
        foreign_keys="ExamAssignment.student_id",
    )
    attempts = relationship("ExamAttempt", back_populates="student", cascade="all, delete-orphan")
