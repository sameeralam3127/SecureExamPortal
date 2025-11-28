from flask import Blueprint, render_template, request, redirect, url_for

student_bp = Blueprint(
    "student",
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

@student_bp.route("/")
def index():
    return render_template("index.html")

@student_bp.route("/exam")
def exam():
    return render_template("exam.html")

@student_bp.route("/submit", methods=["POST"])
def submit_exam():
    return render_template("submit.html")
