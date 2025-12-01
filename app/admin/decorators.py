from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required


def admin_required(func):
    """Ensure only admins can access."""

    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Access denied", "danger")
            return redirect(url_for("student.dashboard"))
        return func(*args, **kwargs)

    return wrapper
