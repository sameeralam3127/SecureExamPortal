from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.extensions.db import get_db
from app.repositories.exam_repository import create_exam, list_exams
from app.schemas.exam import ExamCreate, ExamRead

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("/", response_model=list[ExamRead])
def get_exams(db: Session = Depends(get_db)) -> list[ExamRead]:
    return list_exams(db)


@router.post("/", response_model=ExamRead, status_code=status.HTTP_201_CREATED)
def add_exam(payload: ExamCreate, db: Session = Depends(get_db)) -> ExamRead:
    return create_exam(db, payload)
