import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.extensions.db import SessionLocal, init_db
from app.extensions.mail import send_assignment_email, send_password_reset_email
from app.models.exam import AttemptAnswer, ExamAssignment, ExamAttempt
from app.models.job import BackgroundJob, JobStatus

logger = logging.getLogger(__name__)

ASSIGNMENT_EMAIL_JOB = "assignment_email"
ATTEMPT_REPORT_JOB = "attempt_report"
PASSWORD_RESET_EMAIL_JOB = "password_reset_email"


def enqueue_job(
    db: Session,
    job_type: str,
    payload: dict[str, Any],
    *,
    max_attempts: int = 3,
) -> BackgroundJob:
    job = BackgroundJob(job_type=job_type, payload=payload, max_attempts=max_attempts)
    db.add(job)
    db.flush()
    logger.info("Queued background job %s type=%s", job.id, job.job_type)
    return job


def enqueue_assignment_email(
    db: Session,
    *,
    recipient_email: str,
    student_name: str,
    exam_title: str,
) -> BackgroundJob:
    return enqueue_job(
        db,
        ASSIGNMENT_EMAIL_JOB,
        {
            "recipient_email": recipient_email,
            "student_name": student_name,
            "exam_title": exam_title,
        },
    )


def enqueue_attempt_report(db: Session, *, attempt_id: int) -> BackgroundJob:
    return enqueue_job(db, ATTEMPT_REPORT_JOB, {"attempt_id": attempt_id})


def enqueue_password_reset_email(
    db: Session,
    *,
    recipient_email: str,
    reset_token: str,
) -> BackgroundJob:
    return enqueue_job(
        db,
        PASSWORD_RESET_EMAIL_JOB,
        {"recipient_email": recipient_email, "reset_token": reset_token},
    )


def claim_next_job(db: Session) -> BackgroundJob | None:
    now = datetime.now(UTC)
    job = db.scalar(
        select(BackgroundJob)
        .where(
            BackgroundJob.status == JobStatus.queued,
            BackgroundJob.available_at <= now,
        )
        .order_by(BackgroundJob.created_at, BackgroundJob.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return None

    job.status = JobStatus.running
    job.attempts += 1
    job.started_at = now
    job.error = None
    db.commit()
    db.refresh(job)
    return job


def process_job(db: Session, job: BackgroundJob) -> None:
    try:
        result = _dispatch_job(db, job)
    except Exception as exc:
        logger.exception("Background job %s failed", job.id)
        job.error = str(exc)
        job.status = JobStatus.failed if job.attempts >= job.max_attempts else JobStatus.queued
        db.commit()
        return

    job.result = result or {}
    job.status = JobStatus.completed
    job.completed_at = datetime.now(UTC)
    db.commit()
    logger.info("Completed background job %s type=%s", job.id, job.job_type)


def process_one_job() -> bool:
    with SessionLocal() as db:
        job = claim_next_job(db)
        if job is None:
            return False
        process_job(db, job)
        return True


def run_worker(*, poll_interval: float = 2.0) -> None:
    init_db()
    logger.info("Background worker started")
    while True:
        did_work = process_one_job()
        if not did_work:
            time.sleep(poll_interval)


def _dispatch_job(db: Session, job: BackgroundJob) -> dict[str, Any]:
    if job.job_type == ASSIGNMENT_EMAIL_JOB:
        send_assignment_email(
            job.payload["recipient_email"],
            job.payload["student_name"],
            job.payload["exam_title"],
        )
        return {"sent": True}

    if job.job_type == ATTEMPT_REPORT_JOB:
        return _generate_attempt_report(db, int(job.payload["attempt_id"]))

    if job.job_type == PASSWORD_RESET_EMAIL_JOB:
        send_password_reset_email(
            job.payload["recipient_email"],
            job.payload["reset_token"],
        )
        return {"sent": True}

    raise ValueError(f"Unsupported background job type: {job.job_type}")


def _generate_attempt_report(db: Session, attempt_id: int) -> dict[str, Any]:
    attempt = db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id)
        .options(
            selectinload(ExamAttempt.student),
            selectinload(ExamAttempt.assignment).selectinload(ExamAssignment.exam),
            selectinload(ExamAttempt.answers).selectinload(AttemptAnswer.question),
        )
    )
    if attempt is None:
        raise ValueError(f"Attempt {attempt_id} not found")

    answered = len([answer for answer in attempt.answers if answer.selected_option])
    correct = len([answer for answer in attempt.answers if answer.is_correct])
    return {
        "attempt_id": attempt.id,
        "student_id": attempt.student_id,
        "student_name": attempt.student.full_name,
        "exam_id": attempt.assignment.exam_id,
        "exam_title": attempt.assignment.exam.title,
        "score": attempt.score,
        "total_marks": attempt.total_marks,
        "percentage": float(attempt.percentage),
        "answered_questions": answered,
        "correct_answers": correct,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
    }
