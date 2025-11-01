# Secure Exam Portal

A comprehensive **MCA Project** built with Flask for **secure online examinations**.
It supports both **local login** (username/password) and **Google Account login** for convenience and enhanced security.

The system provides role-based dashboards for **Admins** and **Students**, ensuring seamless exam management and participation.

**Live Demo:** [https://sameeralam3127.pythonanywhere.com/](https://sameeralam3127.pythonanywhere.com/)

---

## Features

### Admin Features

1. **Dashboard** – Overview of users, exams, and results
2. **User Management** – Add/edit/delete users; assign exams
3. **Exam Management** – Create, edit, and control exam availability
4. **Reports & Analytics** – View, filter, and export performance data

### Student Features

1. **Dashboard** – List of available and completed exams
2. **Exam Taking** – Timer-based, auto-submission, real-time scoring
3. **Result Review** – Detailed breakdown of performance

### Security & Authentication

- **Local Login** (username + password)
- **Google Account Login** (OAuth 2.0)
- Passwords hashed via **Werkzeug**
- **Flask-Login** for session management
- **Role-based access control** for Admins and Students

### UI & UX

- Built with **Bootstrap 5** for responsive, mobile-friendly layouts
- Modern components, modals, and interactive progress bars
- Toast notifications and user-friendly feedback

---

## Technical Overview

### Database Models

- **User** – Authentication, roles, Google account info
- **Exam** – Exam structure, total marks, duration
- **Question** – MCQs with options and correct answers
- **ExamResult** – Stores student exam attempts and scores
- **UserAnswer** – Tracks selected answers per question

### Stack

- **Flask** (Backend)
- **Flask-Login** (Authentication)
- **Flask-Dance** (Google OAuth)
- **SQLite / SQLAlchemy** (Database ORM)
- **Bootstrap 5** (Frontend)

---

## Setup Instructions

### Clone the repository

```bash
git clone https://github.com/sameeralam3127/SecureExamPortal.git
cd SecureExamPortal
```

### Create and activate a virtual environment (optional)

Using Poetry (recommended):

```bash
/bin/bash -c "$(curl -sSL https://install.python-poetry.org)"
export PATH="$HOME/.local/bin:$PATH"
poetry install
poetry shell
```

Or with venv:

```bash
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file in the **project root** (`SecureExamPortal/.env`) with the following variables:

```bash
# Flask Secret
FLASK_SECRET_KEY=your_random_secret_key_here

# Google OAuth Credentials
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

> ⚠️ Make sure to enable the **Google OAuth API** in your Google Cloud Console
> and set your **Authorized redirect URIs** as:
>
> ```
> http://localhost:5000/login/google/authorized
> http://127.0.0.1:5000/login/google/authorized
> ```

---

## ▶Running the App

```bash
python run.py
```

Then open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

**Default credentials:**

- **Admin:** `admin / admin123`
- **Student:** `student1 / student123`

---

## Google Login Flow

1. Click “Sign in with Google” on the login page
2. Approve access via your Google Account
3. On success:

   - A user is created automatically (if new)
   - You’re redirected to your **Admin** or **Student** dashboard

---

## Error Handling

- Custom error pages (`404`, `500`)
- Session expiry notifications
- Safe database relationships with cascade delete

---

## Future Enhancements

- Randomized question sets
- Bulk student import (CSV)
- Real-time analytics dashboard
- Email notifications and PDF report exports
- Docker + CI/CD deployment

---

## Contributing

We welcome contributions!
See [CONTRIBUTING.md](CONTRIBUTING.md) for pull request workflow and issue guidelines.

## Security

Report vulnerabilities privately through [SECURITY.md](SECURITY.md).

## License

Licensed under the **MIT License**.
See [LICENSE](LICENSE) for more information.

---

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-Love-red.svg" alt="Made with Love">
  <img src="https://img.shields.io/badge/Powered%20by-Flask-blue.svg" alt="Flask">
</p>

---
