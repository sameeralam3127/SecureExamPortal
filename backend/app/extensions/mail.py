import logging
import smtplib
from email.message import EmailMessage

from app.config.base import get_settings

logger = logging.getLogger(__name__)


def send_assignment_email(
    recipient_email: str,
    student_name: str,
    exam_title: str,
) -> None:
    settings = get_settings()
    exam_url = f"{settings.frontend_base_url}/login"

    message = EmailMessage()
    message["Subject"] = f"New exam assigned: {exam_title}"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient_email
    message.set_content(
        f"""Hello {student_name},

You have been assigned a new exam: {exam_title}

Login here to start: {exam_url}

Regards,
Secure Exam Portal
"""
    )

    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
        logger.info(
            "Email notification skipped SMTP send. To=%s Exam=%s Login=%s",
            recipient_email,
            exam_title,
            exam_url,
        )
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
