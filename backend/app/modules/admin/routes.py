import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.extensions.db import get_db
from app.models.audit import AuditEvent
from app.models.exam import AttemptStatus, Exam, ExamAssignment, ExamAttempt, ExamQuestion, SecurityIncident
from app.models.job import BackgroundJob, JobStatus
from app.models.user import User, UserRole
from app.modules.auth.dependencies import require_admin
from app.schemas.analytics import (
    AdminAnalytics,
    AssignmentBreakdown,
    AuditEventRead,
    ExamPerformance,
    IncidentBreakdown,
    ResultsMetrics,
)
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
from app.services.audit import record_audit
from app.services.job_queue import ATTEMPT_REPORT_JOB, enqueue_assignment_email
from app.utils.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

PASS_THRESHOLD = 50


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
    admin: User = Depends(require_admin),
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
    db.flush()
    record_audit(
        db,
        actor=admin,
        action="student.create",
        entity_type="user",
        entity_id=student.id,
        detail={"username": student.username},
    )
    db.commit()
    db.refresh(student)
    return student


@router.post("/students/bulk", response_model=list[UserRead], status_code=status.HTTP_201_CREATED)
def create_students_bulk(
    payload: BulkUserCreate,
    admin: User = Depends(require_admin),
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
    db.flush()
    record_audit(
        db,
        actor=admin,
        action="student.bulk_create",
        entity_type="user",
        detail={"count": len(students)},
    )
    db.commit()
    for student in students:
        db.refresh(student)
    return students


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    student = db.get(User, student_id)
    if student is None or student.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    record_audit(
        db,
        actor=admin,
        action="student.delete",
        entity_type="user",
        entity_id=student.id,
        detail={"username": student.username},
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
    db.flush()
    record_audit(
        db,
        actor=current_user,
        action="exam.create",
        entity_type="exam",
        entity_id=exam.id,
        detail={"title": exam.title, "questions": len(payload.questions)},
    )
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
    db.flush()
    record_audit(
        db,
        actor=current_user,
        action="exam.bulk_create",
        entity_type="exam",
        detail={"count": len(exams)},
    )
    db.commit()
    for exam in exams:
        db.refresh(exam)
    return exams


@router.delete("/exams/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    exam = db.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    record_audit(
        db,
        actor=admin,
        action="exam.delete",
        entity_type="exam",
        entity_id=exam.id,
        detail={"title": exam.title},
    )
    db.delete(exam)
    db.commit()


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_exam(
    payload: AssignmentCreate,
    admin: User = Depends(require_admin),
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
    db.flush()
    record_audit(
        db,
        actor=admin,
        action="assignment.create",
        entity_type="assignment",
        entity_id=assignment.id,
        detail={"exam_id": exam.id, "student_id": student.id},
    )
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
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    assignment = db.get(ExamAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    record_audit(
        db,
        actor=admin,
        action="assignment.delete",
        entity_type="assignment",
        entity_id=assignment.id,
        detail={"exam_id": assignment.exam_id, "student_id": assignment.student_id},
    )
    db.delete(assignment)
    db.commit()


@router.get("/analytics", response_model=AdminAnalytics)
def admin_analytics(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminAnalytics:
    total_students = (
        db.scalar(select(func.count(User.id)).where(User.role == UserRole.student)) or 0
    )
    total_exams = db.scalar(select(func.count(Exam.id))) or 0
    active_exams = db.scalar(select(func.count(Exam.id)).where(Exam.is_active.is_(True))) or 0

    assignments = db.scalars(
        select(ExamAssignment).options(
            selectinload(ExamAssignment.exam),
            selectinload(ExamAssignment.attempts),
        )
    ).all()

    breakdown = AssignmentBreakdown(total=len(assignments))
    scores: list[float] = []
    per_exam: dict[int, dict] = {}
    for assignment in assignments:
        latest = assignment.attempts[-1] if assignment.attempts else None
        status_value = latest.status if latest else None
        if status_value == AttemptStatus.submitted:
            breakdown.submitted += 1
        elif status_value == AttemptStatus.in_progress:
            breakdown.in_progress += 1
        else:
            breakdown.pending += 1

        bucket = per_exam.setdefault(
            assignment.exam_id,
            {"title": assignment.exam.title, "assignments": 0, "submissions": 0, "score_sum": 0.0},
        )
        bucket["assignments"] += 1
        if status_value == AttemptStatus.submitted and latest is not None:
            score = float(latest.percentage)
            scores.append(score)
            bucket["submissions"] += 1
            bucket["score_sum"] += score

    results = ResultsMetrics(submitted_attempts=len(scores))
    if scores:
        results.average_score = round(sum(scores) / len(scores), 2)
        results.highest_score = round(max(scores), 2)
        results.lowest_score = round(min(scores), 2)
        passed = len([score for score in scores if score >= PASS_THRESHOLD])
        results.pass_rate = round((passed / len(scores)) * 100, 2)

    exam_performance = [
        ExamPerformance(
            exam_id=exam_id,
            title=data["title"],
            assignments=data["assignments"],
            submissions=data["submissions"],
            average_score=round(data["score_sum"] / data["submissions"], 2)
            if data["submissions"]
            else 0,
        )
        for exam_id, data in per_exam.items()
    ]
    exam_performance.sort(key=lambda item: (item.submissions, item.assignments), reverse=True)

    incident_total = db.scalar(select(func.count(SecurityIncident.id))) or 0
    incident_rows = db.execute(
        select(SecurityIncident.incident_type, func.count(SecurityIncident.id)).group_by(
            SecurityIncident.incident_type
        )
    ).all()
    incidents = IncidentBreakdown(
        total=incident_total,
        by_type={incident_type: count for incident_type, count in incident_rows},
    )

    return AdminAnalytics(
        pass_threshold=PASS_THRESHOLD,
        total_students=total_students,
        total_exams=total_exams,
        active_exams=active_exams,
        assignments=breakdown,
        results=results,
        incidents=incidents,
        exam_performance=exam_performance[:10],
    )


@router.get("/audit-events", response_model=list[AuditEventRead])
def list_audit_events(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AuditEvent]:
    return list(
        db.scalars(select(AuditEvent).order_by(desc(AuditEvent.id)).limit(100)).all()
    )


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
