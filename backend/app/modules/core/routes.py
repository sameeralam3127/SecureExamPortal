from flask import Blueprint, jsonify

core_bp = Blueprint("core", __name__)

@core_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "OK",
        "service": "SecureExamPortal API",
        "version": "v1"
    }), 200