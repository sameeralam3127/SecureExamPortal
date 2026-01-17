from datetime import datetime, timedelta

from app import create_app, db
from app.models import Exam, ExamResult, Question, User


def create_sample_data():
    app = create_app()

    with app.app_context():
        print("Creating sample data...")

        # ✅ ENSURE TABLES EXIST
        db.create_all()

        # -------------------------
        # Admin User
        # -------------------------
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")

        # -------------------------
        # Sample Exam
        # -------------------------
        exam = Exam.query.filter_by(title="Computer Science Fundamentals").first()
        if not exam:
            exam = Exam(
                title="Computer Science Fundamentals",
                description="A comprehensive test covering fundamental computer science concepts.",
                duration=60,
                total_marks=100,
                passing_marks=60,
                created_by=admin.id,
                is_active=True,
            )
            db.session.add(exam)
            db.session.commit()
            print("Sample exam created")

            questions = [
                Question(
                    exam_id=exam.id,
                    question_text="What is the time complexity of binary search?",
                    option_a="O(1)",
                    option_b="O(log n)",
                    option_c="O(n)",
                    option_d="O(n^2)",
                    correct_answer="B",
                    marks=10,
                ),
                Question(
                    exam_id=exam.id,
                    question_text="Which data structure uses LIFO principle?",
                    option_a="Queue",
                    option_b="Stack",
                    option_c="Tree",
                    option_d="Graph",
                    correct_answer="B",
                    marks=10,
                ),
            ]

            db.session.add_all(questions)
            db.session.commit()
            print("Sample questions added")
        else:
            print("Sample exam already exists")

        # -------------------------
        # Sample Students
        # -------------------------
        students = []
        for i in range(1, 4):
            username = f"student{i}"
            student = User.query.filter_by(username=username).first()
            if not student:
                student = User(
                    username=username,
                    email=f"{username}@example.com",
                    is_admin=False
                )
                student.set_password("student123")
                students.append(student)
                print(f"Created student: {username}")

        if students:
            db.session.add_all(students)
            db.session.commit()
            print("Sample students created")

        # -------------------------
        # Sample Exam Results
        # -------------------------
        current_time = datetime.utcnow()
        all_students = User.query.filter_by(is_admin=False).all()

        for student in all_students:

            # Passed attempt
            if not ExamResult.query.filter_by(
                user_id=student.id,
                exam_id=exam.id,
                score=80
            ).first():
                db.session.add(
                    ExamResult(
                        exam_id=exam.id,
                        user_id=student.id,
                        score=80,
                        total_marks=100,
                        start_time=current_time - timedelta(days=1),
                        end_time=current_time - timedelta(days=1, minutes=45),
                        is_passed=True,
                        completed=True,   # ✅ IMPORTANT
                    )
                )

            # Failed attempt
            if not ExamResult.query.filter_by(
                user_id=student.id,
                exam_id=exam.id,
                score=50
            ).first():
                db.session.add(
                    ExamResult(
                        exam_id=exam.id,
                        user_id=student.id,
                        score=50,
                        total_marks=100,
                        start_time=current_time - timedelta(hours=2),
                        end_time=current_time - timedelta(hours=1),
                        is_passed=False,
                        completed=True,   # ✅ IMPORTANT
                    )
                )

        db.session.commit()
        print("Sample exam results created")

        # -------------------------
        # Summary
        # -------------------------
        print("\n--- Data Summary ---")
        print(f"Total Users: {User.query.count()}")
        print(f"Total Exams: {Exam.query.count()}")
        print(f"Total Questions: {Question.query.count()}")
        print(f"Total Exam Results: {ExamResult.query.count()}")
        print("--------------------")


if __name__ == "__main__":
    create_sample_data()
