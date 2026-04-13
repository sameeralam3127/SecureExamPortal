from collections.abc import Generator

from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.base import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models.exam import Exam, ExamAssignment, ExamQuestion
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.username == "admin"))
        student = db.scalar(select(User).where(User.username == "student1"))

        if admin is None:
            admin = User(
                full_name="Portal Administrator",
                username="admin",
                email="admin@secureexamportal.com",
                password_hash=hash_password("admin123"),
                role=UserRole.admin,
            )
            db.add(admin)
        elif admin.email.endswith(".local"):
            admin.email = "admin@secureexamportal.com"

        if student is None:
            student = User(
                full_name="Student One",
                username="student1",
                email="student1@secureexamportal.com",
                password_hash=hash_password("student123"),
                role=UserRole.student,
            )
            db.add(student)
        elif student.email.endswith(".local"):
            student.email = "student1@secureexamportal.com"

        db.commit()
        db.refresh(admin)
        db.refresh(student)

        existing_exam = db.scalar(select(Exam).where(Exam.title == "Python Fundamentals"))
        if existing_exam is None:
            exam = Exam(
                title="Python Fundamentals",
                description="Baseline MCQ assessment covering Python syntax and core concepts.",
                duration_minutes=15,
                created_by_id=admin.id,
                questions=[
                    ExamQuestion(
                        question_text="Which keyword defines a function in Python?",
                        option_a="func",
                        option_b="define",
                        option_c="def",
                        option_d="lambda",
                        correct_option="C",
                        marks=2,
                    ),
                    ExamQuestion(
                        question_text="Which built-in type stores key-value pairs?",
                        option_a="list",
                        option_b="tuple",
                        option_c="set",
                        option_d="dict",
                        correct_option="D",
                        marks=2,
                    ),
                ],
            )
            db.add(exam)
            db.commit()
            db.refresh(exam)
            db.add(ExamAssignment(exam_id=exam.id, student_id=student.id))
            db.commit()
