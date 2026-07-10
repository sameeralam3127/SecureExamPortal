from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.db import Base


class UserRole(str, Enum):
    admin = "admin"
    student = "student"


class AuthProvider(str, Enum):
    password = "password"
    google = "google"


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
    auth_provider: Mapped[AuthProvider] = mapped_column(
        SqlEnum(AuthProvider, name="auth_provider"),
        nullable=False,
        default=AuthProvider.password,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # Bumped to invalidate every previously issued access token for this user
    # (used by logout-everywhere and password changes/resets).
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reset_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
