from dotenv import load_dotenv
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_dance.contrib.google import google
from flask_login import current_user, login_required, login_user, logout_user
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from sqlalchemy import or_

from .. import db, login_manager
from ..models import User

# -------------------------------
# Setup
# -------------------------------
auth_bp = Blueprint("auth", __name__)


# -------------------------------
# Flask-Login Integration
# -------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------------
# Index Route
# -------------------------------
@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))
    return render_template("index.html")


# -------------------------------
# Register
# -------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        # Check existing username or email
        if User.query.filter(
            or_(User.username == username, User.email == email)
        ).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("auth.register"))

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# -------------------------------
# Login (Local)
# -------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome, {user.username}!", "success")
            return redirect(
                url_for("admin.dashboard")
                if user.is_admin
                else url_for("student.dashboard")
            )

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


# -------------------------------
# Google Login Callback
# -------------------------------
@auth_bp.route("/google_callback")
def google_callback():
    if not google.authorized:
        return redirect(url_for("google.login"))

    try:
        resp = google.get("/oauth2/v2/userinfo")
    except InvalidGrantError:
        session.clear()
        flash("Google session expired. Please try again.", "warning")
        return redirect(url_for("google.login"))

    if not resp.ok:
        flash("Failed to fetch Google user info.", "danger")
        return redirect(url_for("auth.login"))

    user_info = resp.json()
    email = user_info.get("email")
    google_id = user_info.get("id")
    picture = user_info.get("picture")
    username = user_info.get("name") or email.split("@")[0]

    if not email:
        flash("Google account did not return an email.", "danger")
        return redirect(url_for("auth.login"))

    # Check for existing user by Google ID or email
    user = User.query.filter(
        or_(User.google_id == google_id, User.email == email)
    ).first()

    if not user:
        # Create a new user from Google profile
        user = User(
            username=username,
            email=email,
            google_id=google_id,
            picture=picture,
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created via Google.", "success")
    else:
        # Update user’s Google info if changed
        user.google_id = google_id
        user.picture = picture
        db.session.commit()

    login_user(user)
    flash(f"Welcome back, {user.username}!", "success")

    # Redirect based on role
    if user.is_admin:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("student.dashboard"))


# -------------------------------
# Logout
# -------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.index"))
