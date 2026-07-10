import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.extensions.db import get_db
from app.models.exam import AttemptStatus, Exam, ExamAssignment, ExamAttempt, ExamQuestion, SecurityIncident
from app.models.job import BackgroundJob, JobStatus
from app.models.user import User, UserRole
from app.modules.auth.dependencies import require_admin
from app.schemas.exam import (
    AssignmentCreate,
    AssignmentRead,
    BackgroundJobRead,
    BulkExamCreate,
    DashboardStats,
    ExamCreate,
    ExamRead,
    SecurityIncidentRead,
)
from app.schemas.user import BulkUserCreate, UserCreate, UserRead
from app.services.job_queue import ATTEMPT_REPORT_JOB, enqueue_assignment_email
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


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    student = db.get(User, student_id)
    if student is None or student.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    db.delete(student)
    db.commit()


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
        block_clipboard=payload.block_clipboard,
        block_context_menu=payload.block_context_menu,
        block_inspect_shortcuts=payload.block_inspect_shortcuts,
        enforce_fullscreen=payload.enforce_fullscreen,
        track_focus_loss=payload.track_focus_loss,
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
            block_clipboard=exam.block_clipboard,
            block_context_menu=exam.block_context_menu,
            block_inspect_shortcuts=exam.block_inspect_shortcuts,
            enforce_fullscreen=exam.enforce_fullscreen,
            track_focus_loss=exam.track_focus_loss,
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


@router.delete("/exams/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    exam = db.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    db.delete(exam)
    db.commit()


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
    enqueue_assignment_email(
        db,
        recipient_email=student.email,
        student_name=student.full_name,
        exam_title=exam.title,
    )
    db.commit()
    db.refresh(assignment)
    logger.info("Queued assignment email to %s for exam %s", student.email, exam.title)
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


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    assignment = db.get(ExamAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    db.delete(assignment)
    db.commit()


@router.get("/jobs", response_model=list[BackgroundJobRead])
def list_background_jobs(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[BackgroundJob]:
    return list(db.scalars(select(BackgroundJob).order_by(desc(BackgroundJob.id)).limit(100)).all())


@router.get("/reports", response_model=list[BackgroundJobRead])
def list_generated_reports(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[BackgroundJob]:
    return list(
        db.scalars(
            select(BackgroundJob)
            .where(
                BackgroundJob.job_type == ATTEMPT_REPORT_JOB,
                BackgroundJob.status == JobStatus.completed,
            )
            .order_by(desc(BackgroundJob.completed_at), desc(BackgroundJob.id))
            .limit(100)
        ).all()
    )


@router.get("/security-incidents", response_model=list[SecurityIncidentRead])
def list_security_incidents(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[SecurityIncidentRead]:
    incidents = db.scalars(
        select(SecurityIncident)
        .options(selectinload(SecurityIncident.student), selectinload(SecurityIncident.exam))
        .order_by(desc(SecurityIncident.occurred_at), desc(SecurityIncident.id))
        .limit(100)
    ).all()

    return [
        SecurityIncidentRead(
            id=incident.id,
            attempt_id=incident.attempt_id,
            student_id=incident.student_id,
            exam_id=incident.exam_id,
            incident_type=incident.incident_type,
            detail=incident.detail,
            occurred_at=incident.occurred_at,
            student_name=incident.student.full_name if incident.student else None,
            exam_title=incident.exam.title if incident.exam else None,
        )
        for incident in incidents
    ]
