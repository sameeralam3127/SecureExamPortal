from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.schemas.exam import ExamCreate


def list_exams(db: Session) -> list[Exam]:
    return list(db.scalars(select(Exam).order_by(Exam.id.desc())).all())


def create_exam(db: Session, payload: ExamCreate) -> Exam:
    exam = Exam(**payload.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam
