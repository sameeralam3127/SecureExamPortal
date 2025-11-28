from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")


    from .student import student_bp
    app.register_blueprint(student_bp)

    return app
   