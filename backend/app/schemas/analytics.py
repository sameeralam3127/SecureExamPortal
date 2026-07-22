from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssignmentBreakdown(BaseModel):
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    submitted: int = 0


class ResultsMetrics(BaseModel):
    submitted_attempts: int = 0
    average_score: float = 0
    highest_score: float = 0
    lowest_score: float = 0
    pass_rate: float = 0


class ExamPerformance(BaseModel):
    exam_id: int
    title: str
    assignments: int = 0
    submissions: int = 0
    average_score: float = 0


class IncidentBreakdown(BaseModel):
    total: int = 0
    by_type: dict[str, int] = {}


class AdminAnalytics(BaseModel):
    pass_threshold: int = 50
    total_students: int = 0
    total_exams: int = 0
    active_exams: int = 0
    assignments: AssignmentBreakdown = AssignmentBreakdown()
    results: ResultsMetrics = ResultsMetrics()
    incidents: IncidentBreakdown = IncidentBreakdown()
    exam_performance: list[ExamPerformance] = []


class AuditEventRead(BaseModel):
    id: int
    actor_username: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    detail: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
