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

    _send(message)


def send_password_reset_email(recipient_email: str, reset_token: str) -> None:
    settings = get_settings()
    reset_url = f"{settings.frontend_base_url}/reset-password?token={reset_token}"

    message = EmailMessage()
    message["Subject"] = "Reset your Secure Exam Portal password"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient_email
    message.set_content(
        f"""Hello,

We received a request to reset your Secure Exam Portal password.

Reset it using this link (it expires soon): {reset_url}

If you did not request this, you can safely ignore this email.

Regards,
Secure Exam Portal
"""
    )

    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
        # No SMTP configured: log the link so the flow stays testable in dev.
        logger.info(
            "Password reset email skipped SMTP send. To=%s Reset=%s",
            recipient_email,
            reset_url,
        )
        return

    _send(message)


def _send(message: EmailMessage) -> None:
    settings = get_settings()
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
