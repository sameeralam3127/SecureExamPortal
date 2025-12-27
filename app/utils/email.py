from flask_mail import Message
from .. import mail


def send_exam_assigned_email(user, exam):
    msg = Message(
        subject=f"New Exam Assigned: {exam.title}",
        recipients=[user.email],
        html=f"""
        <p>Hello {user.username},</p>

        <p>You have been assigned a new exam.</p>

        <ul>
            <li><b>Exam:</b> {exam.title}</li>
            <li><b>Duration:</b> {exam.duration} minutes</li>
            <li><b>Total Marks:</b> {exam.total_marks}</li>
        </ul>

        <p>Please log in to your account to attempt the exam.</p>

        <p>Best regards,<br>
        Exam Management System</p>
        """
    )

    mail.send(msg)
