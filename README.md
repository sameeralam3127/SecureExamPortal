

# Secure Exam Portal

A comprehensive **MCA Project** built with Flask for secure online exam conduction. The portal allows administrators to manage users and exams, while students can take tests, view results, and track performance. Security measures such as authentication, role-based access, and result integrity are included.

**Live Demo:** [https://sameeralam3127.pythonanywhere.com/](https://sameeralam3127.pythonanywhere.com/)

---

## Features

### Admin Features

1. **Dashboard** – Statistics overview, quick actions, responsive UI
2. **User Management** – Create, edit, delete users; assign exams
3. **Exam Management** – Create, configure, and manage exams/questions
4. **Reports & Analytics** – View, filter, export results; statistics and insights

### Student Features

1. **Dashboard** – See available exams and past results
2. **Exam Taking** – Timer-based, auto-submit, instant results
3. **Result Review** – Detailed breakdown with correct/incorrect answers

### Security Features

* Authentication with password hashing (Werkzeug)
* Role-based access control (Admin/Student)
* CSRF protection and input validation

### UI Features

* Responsive design (Bootstrap 5)
* Interactive elements (progress bars, filters, notifications)
* Mobile-friendly interface

---

## Technical Details

### Database Models

* **User**: manages authentication and roles
* **Exam**: holds exam parameters
* **Question**: stores exam questions
* **ExamResult**: records student results
* **UserAnswer**: tracks selected answers

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/sameeralam3127/SecureExamPortal.git
cd SecureExamPortal

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py
```

Default credentials:

* Admin → `admin / admin123`
* Student → `student1 / student123`

---

## Error Handling

* Custom error pages (404, 500)
* Session timeout alerts
* Cascade deletion safety

---

## Future Enhancements

* Multiple question types, file uploads
* Randomized questions and question bank
* Batch user import, analytics graphs
* Email notifications, PDF exports
* API documentation and Docker deployment

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for pull request workflow and issue reporting.

## Code of Conduct

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) when engaging in the community.

## Security

Report vulnerabilities via [SECURITY.md](SECURITY.md).

## License

This project is licensed under the **MIT License** – see [LICENSE](LICENSE).




