from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.extensions.db import get_db
from app.models.exam import AttemptAnswer, AttemptStatus, Exam, ExamAssignment, ExamAttempt
from app.models.user import User
from app.modules.auth.dependencies import require_student
from app.schemas.exam import (
    AssignmentStatusRead,
    AttemptResult,
    AttemptSubmitRequest,
    ExamStartResponse,
    QuestionRead,
    StudentDashboard,
)

router = APIRouter(prefix="/student", tags=["student"])


@router.get("/dashboard", response_model=StudentDashboard)
def student_dashboard(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> StudentDashboard:
    assigned_exams = (
        db.scalar(select(func.count(ExamAssignment.id)).where(ExamAssignment.student_id == current_user.id))
        or 0
    )
    completed_exams = (
        db.scalar(
            select(func.count(ExamAttempt.id)).where(
                ExamAttempt.student_id == current_user.id,
                ExamAttempt.status == AttemptStatus.submitted,
            )
        )
        or 0
    )
    average_score = (
        db.scalar(
            select(func.avg(ExamAttempt.percentage)).where(
                ExamAttempt.student_id == current_user.id,
                ExamAttempt.status == AttemptStatus.submitted,
            )
        )
        or 0
    )
    return StudentDashboard(
        assigned_exams=assigned_exams,
        completed_exams=completed_exams,
        pending_exams=max(assigned_exams - completed_exams, 0),
        average_score=round(float(average_score), 2),
    )


@router.get("/assignments", response_model=list[AssignmentStatusRead])
def my_assignments(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> list[AssignmentStatusRead]:
    assignments = db.scalars(
        select(ExamAssignment)
        .where(ExamAssignment.student_id == current_user.id)
        .options(selectinload(ExamAssignment.exam), selectinload(ExamAssignment.attempts))
        .order_by(desc(ExamAssignment.id))
    ).all()

    response: list[AssignmentStatusRead] = []
    for assignment in assignments:
        latest_attempt = max(assignment.attempts, key=lambda item: item.id) if assignment.attempts else None
        response.append(
            AssignmentStatusRead(
                assignment_id=assignment.id,
                exam_id=assignment.exam_id,
                exam_title=assignment.exam.title,
                duration_minutes=assignment.exam.duration_minutes,
                assigned_at=assignment.assigned_at,
                attempt_id=latest_attempt.id if latest_attempt else None,
                status=latest_attempt.status if latest_attempt else None,
                score=latest_attempt.score if latest_attempt else None,
                total_marks=latest_attempt.total_marks if latest_attempt else None,
                percentage=float(latest_attempt.percentage) if latest_attempt else None,
            )
        )
    return response


@router.post("/assignments/{assignment_id}/start", response_model=ExamStartResponse)
def start_exam(
    assignment_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> ExamStartResponse:
    assignment = db.scalar(
        select(ExamAssignment)
        .where(ExamAssignment.id == assignment_id, ExamAssignment.student_id == current_user.id)
        .options(
            selectinload(ExamAssignment.exam).selectinload(Exam.questions),
            selectinload(ExamAssignment.attempts),
        )
    )

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    latest_attempt = max(assignment.attempts, key=lambda item: item.id) if assignment.attempts else None
    if latest_attempt and latest_attempt.status == AttemptStatus.submitted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exam already submitted",
        )

    if latest_attempt and latest_attempt.status == AttemptStatus.in_progress:
        attempt = latest_attempt
    else:
        total_marks = sum(question.marks for question in assignment.exam.questions)
        attempt = ExamAttempt(
            assignment_id=assignment.id,
            student_id=current_user.id,
            total_marks=total_marks,
            status=AttemptStatus.in_progress,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

    return ExamStartResponse(
        attempt_id=attempt.id,
        assignment_id=assignment.id,
        exam_id=assignment.exam.id,
        title=assignment.exam.title,
        description=assignment.exam.description,
        duration_minutes=assignment.exam.duration_minutes,
        started_at=attempt.started_at,
        questions=[QuestionRead.model_validate(question) for question in assignment.exam.questions],
    )


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptResult)
def submit_attempt(
    attempt_id: int,
    payload: AttemptSubmitRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> AttemptResult:
    attempt = db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id, ExamAttempt.student_id == current_user.id)
        .options(
            selectinload(ExamAttempt.assignment)
            .selectinload(ExamAssignment.exam)
            .selectinload(Exam.questions),
            selectinload(ExamAttempt.answers),
        )
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if attempt.status == AttemptStatus.submitted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attempt already submitted")

    allowed_finish_time = attempt.started_at.astimezone(timezone.utc).timestamp() + (
        attempt.assignment.exam.duration_minutes * 60
    )
    now_ts = datetime.now(timezone.utc).timestamp()

    question_map = {question.id: question for question in attempt.assignment.exam.questions}
    answer_map = {answer.question_id: answer.selected_option for answer in payload.answers}

    attempt.answers.clear()
    score = 0
    for question_id, question in question_map.items():
        selected_option = answer_map.get(question_id)
        if selected_option is None:
            continue
        is_correct = selected_option == question.correct_option
        marks_awarded = question.marks if is_correct else 0
        score += marks_awarded
        db.add(
            AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question_id,
                selected_option=selected_option,
                is_correct=is_correct,
                marks_awarded=marks_awarded,
            )
        )

    _ = now_ts > allowed_finish_time
    attempt.status = AttemptStatus.submitted
    attempt.score = score
    attempt.total_marks = sum(question.marks for question in question_map.values())
    attempt.percentage = round((score / attempt.total_marks) * 100, 2) if attempt.total_marks else 0
    attempt.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)

    return AttemptResult(
        attempt_id=attempt.id,
        exam_title=attempt.assignment.exam.title,
        score=attempt.score,
        total_marks=attempt.total_marks,
        percentage=float(attempt.percentage),
        status=attempt.status,
        submitted_at=attempt.submitted_at,
    )


@router.get("/attempts/history", response_model=list[AttemptResult])
def attempt_history(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> list[AttemptResult]:
    attempts = db.scalars(
        select(ExamAttempt)
        .where(ExamAttempt.student_id == current_user.id)
        .options(selectinload(ExamAttempt.assignment).selectinload(ExamAssignment.exam))
        .order_by(desc(ExamAttempt.id))
    ).all()

    return [
        AttemptResult(
            attempt_id=attempt.id,
            exam_title=attempt.assignment.exam.title,
            score=attempt.score,
            total_marks=attempt.total_marks,
            percentage=float(attempt.percentage),
            status=attempt.status,
            submitted_at=attempt.submitted_at,
        )
        for attempt in attempts
    ]
