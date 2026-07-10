from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.extensions.db import get_db
from app.models.exam import AttemptAnswer, AttemptStatus, Exam, ExamAssignment, ExamAttempt, SecurityIncident
from app.models.user import User
from app.modules.auth.dependencies import require_student
from app.schemas.exam import (
    AnswerState,
    AssignmentStatusRead,
    AttemptResult,
    AttemptSubmitRequest,
    ExamStartResponse,
    QuestionRead,
    SecurityIncidentCreate,
    SecurityIncidentRead,
    StudentDashboard,
)
from app.services.job_queue import enqueue_attempt_report

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
            selectinload(ExamAssignment.attempts).selectinload(ExamAttempt.answers),
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

    saved_answers = [
        AnswerState(question_id=answer.question_id, selected_option=answer.selected_option)
        for answer in sorted(attempt.answers, key=lambda item: item.question_id)
    ]
    answered_question_ids = {answer.question_id for answer in attempt.answers}
    next_unanswered_index = next(
        (
            index
            for index, question in enumerate(assignment.exam.questions)
            if question.id not in answered_question_ids
        ),
        0,
    )

    return ExamStartResponse(
        attempt_id=attempt.id,
        assignment_id=assignment.id,
        exam_id=assignment.exam.id,
        title=assignment.exam.title,
        description=assignment.exam.description,
        duration_minutes=assignment.exam.duration_minutes,
        block_clipboard=assignment.exam.block_clipboard,
        block_context_menu=assignment.exam.block_context_menu,
        block_inspect_shortcuts=assignment.exam.block_inspect_shortcuts,
        enforce_fullscreen=assignment.exam.enforce_fullscreen,
        track_focus_loss=assignment.exam.track_focus_loss,
        started_at=attempt.started_at,
        question_count=len(assignment.exam.questions),
        current_question_index=next_unanswered_index,
        saved_answers=saved_answers,
        questions=[QuestionRead.model_validate(question) for question in assignment.exam.questions],
    )


@router.post(
    "/attempts/{attempt_id}/security-incidents",
    response_model=SecurityIncidentRead,
    status_code=status.HTTP_201_CREATED,
)
def log_security_incident(
    attempt_id: int,
    payload: SecurityIncidentCreate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> SecurityIncidentRead:
    attempt = db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id, ExamAttempt.student_id == current_user.id)
        .options(selectinload(ExamAttempt.assignment).selectinload(ExamAssignment.exam))
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if attempt.status == AttemptStatus.submitted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attempt already submitted")

    incident = SecurityIncident(
        attempt_id=attempt.id,
        student_id=current_user.id,
        exam_id=attempt.assignment.exam.id,
        incident_type=payload.incident_type,
        detail=payload.detail,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    return SecurityIncidentRead(
        id=incident.id,
        attempt_id=incident.attempt_id,
        student_id=incident.student_id,
        exam_id=incident.exam_id,
        incident_type=incident.incident_type,
        detail=incident.detail,
        occurred_at=incident.occurred_at,
        student_name=current_user.full_name,
        exam_title=attempt.assignment.exam.title,
    )


@router.put("/attempts/{attempt_id}/answers", response_model=list[AnswerState])
def autosave_answers(
    attempt_id: int,
    payload: AttemptSubmitRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> list[AnswerState]:
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

    valid_question_ids = {question.id for question in attempt.assignment.exam.questions}
    incoming_answers = {answer.question_id: answer.selected_option for answer in payload.answers}
    if not set(incoming_answers).issubset(valid_question_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more answers do not belong to this exam",
        )

    existing_answers = {answer.question_id: answer for answer in attempt.answers}
    for question_id, selected_option in incoming_answers.items():
        existing_answer = existing_answers.get(question_id)
        if existing_answer:
            existing_answer.selected_option = selected_option
        else:
            db.add(
                AttemptAnswer(
                    attempt_id=attempt.id,
                    question_id=question_id,
                    selected_option=selected_option,
                    is_correct=False,
                    marks_awarded=0,
                )
            )

    db.commit()
    refreshed_attempt = db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt.id)
        .options(selectinload(ExamAttempt.answers))
    )
    return [
        AnswerState(question_id=answer.question_id, selected_option=answer.selected_option)
        for answer in sorted(refreshed_attempt.answers, key=lambda item: item.question_id)
    ]


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

    allowed_finish_time = attempt.started_at.astimezone(UTC).timestamp() + (
        attempt.assignment.exam.duration_minutes * 60
    )
    now_ts = datetime.now(UTC).timestamp()

    question_map = {question.id: question for question in attempt.assignment.exam.questions}
    if payload.answers:
        incoming_answers = {answer.question_id: answer.selected_option for answer in payload.answers}
        existing_answers = {answer.question_id: answer for answer in attempt.answers}
        for question_id, selected_option in incoming_answers.items():
            existing_answer = existing_answers.get(question_id)
            if existing_answer:
                existing_answer.selected_option = selected_option
            elif question_id in question_map:
                db.add(
                    AttemptAnswer(
                        attempt_id=attempt.id,
                        question_id=question_id,
                        selected_option=selected_option,
                        is_correct=False,
                        marks_awarded=0,
                    )
                )
        db.flush()
        db.refresh(attempt)

    score = 0
    for answer in attempt.answers:
        question = question_map.get(answer.question_id)
        selected_option = answer.selected_option
        if question is None:
            continue
        if selected_option is None:
            continue
        is_correct = selected_option == question.correct_option
        marks_awarded = question.marks if is_correct else 0
        score += marks_awarded
        answer.is_correct = is_correct
        answer.marks_awarded = marks_awarded

    _ = now_ts > allowed_finish_time
    attempt.status = AttemptStatus.submitted
    attempt.score = score
    attempt.total_marks = sum(question.marks for question in question_map.values())
    attempt.percentage = round((score / attempt.total_marks) * 100, 2) if attempt.total_marks else 0
    attempt.submitted_at = datetime.now(UTC)
    db.flush()
    enqueue_attempt_report(db, attempt_id=attempt.id)
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
