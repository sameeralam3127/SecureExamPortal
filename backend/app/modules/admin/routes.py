import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.extensions.db import get_db
from app.extensions.mail import send_assignment_email
from app.models.exam import AttemptStatus, Exam, ExamAssignment, ExamAttempt, ExamQuestion
from app.models.user import User, UserRole
from app.modules.auth.dependencies import require_admin
from app.schemas.exam import AssignmentCreate, AssignmentRead, BulkExamCreate, DashboardStats, ExamCreate, ExamRead
from app.schemas.user import BulkUserCreate, UserCreate, UserRead
from app.utils.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardStats)
def admin_dashboard(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DashboardStats:
    total_students = db.scalar(select(func.count(User.id)).where(User.role == UserRole.student)) or 0
    total_exams = db.scalar(select(func.count(Exam.id))) or 0
    total_assignments = db.scalar(select(func.count(ExamAssignment.id))) or 0
    completed_attempts = (
        db.scalar(
            select(func.count(ExamAttempt.id)).where(ExamAttempt.status == AttemptStatus.submitted)
        )
        or 0
    )
    average_score = (
        db.scalar(
            select(func.avg(ExamAttempt.percentage)).where(
                ExamAttempt.status == AttemptStatus.submitted
            )
        )
        or 0
    )
    return DashboardStats(
        total_students=total_students,
        total_exams=total_exams,
        total_assignments=total_assignments,
        completed_attempts=completed_attempts,
        average_score=round(float(average_score), 2),
    )


@router.get("/students", response_model=list[UserRead])
def list_students(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(
        db.scalars(
            select(User).where(User.role == UserRole.student).order_by(desc(User.id))
        ).all()
    )


@router.post("/students", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    duplicate = db.scalar(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    student = User(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.student,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.post("/students/bulk", response_model=list[UserRead], status_code=status.HTTP_201_CREATED)
def create_students_bulk(
    payload: BulkUserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    usernames = [student.username for student in payload.users]
    emails = [student.email for student in payload.users]
    duplicate_usernames = {username for username in usernames if usernames.count(username) > 1}
    duplicate_emails = {email for email in emails if emails.count(email) > 1}
    if duplicate_usernames or duplicate_emails:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate usernames/emails found in uploaded batch",
        )

    existing_users = db.scalars(
        select(User.username).where((User.username.in_(usernames)) | (User.email.in_(emails)))
    ).all()
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate users found: {', '.join(sorted(set(existing_users)))}",
        )

    students = [
        User(
            full_name=student.full_name,
            username=student.username,
            email=student.email,
            password_hash=hash_password(student.password),
            role=UserRole.student,
        )
        for student in payload.users
    ]
    db.add_all(students)
    db.commit()
    for student in students:
        db.refresh(student)
    return students


@router.get("/exams", response_model=list[ExamRead])
def list_exams(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Exam]:
    return list(
        db.scalars(
            select(Exam)
            .options(selectinload(Exam.questions))
            .order_by(desc(Exam.id))
        ).all()
    )


@router.post("/exams", response_model=ExamRead, status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Exam:
    exam = Exam(
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        created_by_id=current_user.id,
        questions=[ExamQuestion(**question.model_dump()) for question in payload.questions],
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


@router.post("/exams/bulk", response_model=list[ExamRead], status_code=status.HTTP_201_CREATED)
def create_exams_bulk(
    payload: BulkExamCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Exam]:
    exams = [
        Exam(
            title=exam.title,
            description=exam.description,
            duration_minutes=exam.duration_minutes,
            created_by_id=current_user.id,
            questions=[ExamQuestion(**question.model_dump()) for question in exam.questions],
        )
        for exam in payload.exams
    ]
    db.add_all(exams)
    db.commit()
    for exam in exams:
        db.refresh(exam)
    return exams


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_exam(
    payload: AssignmentCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AssignmentRead:
    exam = db.get(Exam, payload.exam_id)
    student = db.get(User, payload.student_id)
    if exam is None or student is None or student.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valid exam and student are required",
        )

    existing = db.scalar(
        select(ExamAssignment).where(
            ExamAssignment.exam_id == payload.exam_id,
            ExamAssignment.student_id == payload.student_id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exam is already assigned to this student",
        )

    assignment = ExamAssignment(exam_id=payload.exam_id, student_id=payload.student_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    try:
        send_assignment_email(student.email, student.full_name, exam.title)
    except Exception:
        logger.exception(
            "Failed to send assignment email to %s for exam %s",
            student.email,
            exam.title,
        )
    return AssignmentRead(
        id=assignment.id,
        exam_id=assignment.exam_id,
        student_id=assignment.student_id,
        assigned_at=assignment.assigned_at,
        exam_title=exam.title,
        student_name=student.full_name,
    )


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AssignmentRead]:
    assignments = db.scalars(
        select(ExamAssignment)
        .options(
            selectinload(ExamAssignment.exam),
            selectinload(ExamAssignment.student),
            selectinload(ExamAssignment.attempts),
        )
        .order_by(desc(ExamAssignment.id))
    ).all()

    result: list[AssignmentRead] = []
    for assignment in assignments:
        latest_attempt = assignment.attempts[-1] if assignment.attempts else None
        result.append(
            AssignmentRead(
                id=assignment.id,
                exam_id=assignment.exam_id,
                student_id=assignment.student_id,
                assigned_at=assignment.assigned_at,
                exam_title=assignment.exam.title,
                student_name=assignment.student.full_name,
                attempt_status=latest_attempt.status if latest_attempt else None,
                latest_score=float(latest_attempt.percentage) if latest_attempt else None,
            )
        )
    return result
