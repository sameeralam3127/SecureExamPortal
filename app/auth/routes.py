from flask import Blueprint, render_template

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    return render_template("index.html")
