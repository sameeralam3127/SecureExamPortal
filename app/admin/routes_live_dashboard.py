from datetime import datetime
from flask import jsonify
from sqlalchemy import func

from . import admin_bp
from .decorators import admin_required
from .. import db
from ..models import ExamResult


@admin_bp.route("/api/live-stats", methods=["GET"])
@admin_required
def live_stats():
    active_students = ExamResult.query.filter(
        ExamResult.end_time.is_(None)
    ).count()

    total_attempts = ExamResult.query.count()

    completed = ExamResult.query.filter(
        ExamResult.end_time.isnot(None)
    ).count()

    completion_rate = (
        round((completed / total_attempts) * 100, 1)
        if total_attempts else 0
    )

    avg_score = (
        db.session.query(
            func.avg((ExamResult.score / ExamResult.total_marks) * 100)
        )
        .filter(
            ExamResult.end_time.isnot(None),
            ExamResult.total_marks > 0
        )
        .scalar()
    )

    return jsonify({
        "active_students": active_students,
        "completion_rate": completion_rate,
        "average_score": round(avg_score or 0, 1),
        "timestamp": datetime.utcnow().isoformat()
    })
