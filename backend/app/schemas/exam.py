from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.exam import AttemptStatus


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=5)
    option_a: str = Field(min_length=1, max_length=255)
    option_b: str = Field(min_length=1, max_length=255)
    option_c: str = Field(min_length=1, max_length=255)
    option_d: str = Field(min_length=1, max_length=255)
    correct_option: str = Field(pattern="^[ABCD]$")
    marks: int = Field(gt=0, le=10)


class QuestionRead(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    marks: int

    model_config = ConfigDict(from_attributes=True)


class AdminQuestionRead(QuestionRead):
    correct_option: str


class ExamCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=5)
    duration_minutes: int = Field(gt=0, le=600)
    questions: list[QuestionCreate] = Field(min_length=1)


class BulkExamCreate(BaseModel):
    exams: list[ExamCreate] = Field(min_length=1)


class ExamRead(BaseModel):
    id: int
    title: str
    description: str
    duration_minutes: int
    is_active: bool
    created_at: datetime
    questions: list[AdminQuestionRead] = []

    model_config = ConfigDict(from_attributes=True)


class AssignmentCreate(BaseModel):
    exam_id: int
    student_id: int


class AssignmentRead(BaseModel):
    id: int
    exam_id: int
    student_id: int
    assigned_at: datetime
    exam_title: str
    student_name: str
    attempt_status: AttemptStatus | None = None
    latest_score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_students: int = 0
    total_exams: int = 0
    total_assignments: int = 0
    completed_attempts: int = 0
    average_score: float = 0


class StudentDashboard(BaseModel):
    assigned_exams: int = 0
    completed_exams: int = 0
    pending_exams: int = 0
    average_score: float = 0


class ExamStartResponse(BaseModel):
    attempt_id: int
    assignment_id: int
    exam_id: int
    title: str
    description: str
    duration_minutes: int
    started_at: datetime
    questions: list[QuestionRead]


class AnswerSubmit(BaseModel):
    question_id: int
    selected_option: str = Field(pattern="^[ABCD]$")


class AttemptSubmitRequest(BaseModel):
    answers: list[AnswerSubmit] = Field(default_factory=list)


class AttemptResult(BaseModel):
    attempt_id: int
    exam_title: str
    score: int
    total_marks: int
    percentage: float
    status: AttemptStatus
    submitted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AssignmentStatusRead(BaseModel):
    assignment_id: int
    exam_id: int
    exam_title: str
    duration_minutes: int
    assigned_at: datetime
    attempt_id: int | None = None
    status: AttemptStatus | None = None
    score: int | None = None
    total_marks: int | None = None
    percentage: float | None = None

    model_config = ConfigDict(from_attributes=True)
