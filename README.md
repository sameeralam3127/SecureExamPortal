# Secure Exam Portal

A scalable, modular, and API-enabled **Enterprise Online Examination Platform** built with **FastAPI**.

SecureExamPortal is evolving from an academic MCA project into a production-ready backend architecture featuring:

- Modular domain-driven structure
- PostgreSQL database support through Docker
- RESTful API (versioned)
- Dockerized deployment
- Secure authentication & role-based access control
- Student registration, Google login, and assignment email notifications
- Enterprise-grade configuration management

---

### Live Demo (Legacy Version)

[https://sameeralam3127.pythonanywhere.com/](https://sameeralam3127.pythonanywhere.com/)

> ⚠️ The live demo reflects the earlier SQLite-based version.
> The current branch introduces PostgreSQL + modular architecture.

---

### Architecture Overview (High-Level Architecture)

```
Client (Browser / API Consumer)
        ↓
Uvicorn (ASGI Server)
        ↓
FastAPI Application (Modular Architecture)
        ↓
PostgreSQL Database
```

---

### Features (Admin Capabilities)

- Dashboard analytics
- User management with single and bulk student creation
- Exam lifecycle management with single and bulk exam creation
- Exam assignment with email notification
- Result tracking and reporting
- Role-based access enforcement

### Student Capabilities

- Self-registration and login
- Optional Google authentication
- Exam dashboard
- Timed examinations
- Auto-submission
- Performance review
- Historical attempt tracking

---

### Enterprise Enhancements (New Architecture)

- Modular application structure
- PostgreSQL support (production-ready)
- Environment-based configuration (dev / prod / test)
- Docker & Docker Compose setup
- Gunicorn production server
- CORS configuration for API clients
- API-first design (`/api/v1`)
- SQLAlchemy ORM integration
- Secure environment variable handling
- Structured logging

---

### Project Structure

```
SecureExamPortal/
│
├── backend/
│   ├── app/
│   ├── config/          # Environment-based configuration
│   ├── extensions/      # FastAPI/SQLAlchemy initialization
│   ├── modules/         # Domain modules (auth, exams, admin, etc.)
│   ├── models/          # Database models
│   ├── services/        # Business logic layer
│   ├── repositories/    # Data access abstraction
│   ├── schemas/         # Serialization (API layer)
│   └── utils/
│
│   ├── docker/          # Containerization configs
│   ├── main.py          # FastAPI application factory
│   ├── manage.py        # Local dev entrypoint
│   └── requirements.txt
├── frontend/            # React client
└── docker-compose.yml   # PostgreSQL + FastAPI stack
```

---

### Setup (Development Mode) Clone Repository

```bash
git clone https://github.com/sameeralam3127/SecureExamPortal.git
cd SecureExamPortal
```

---

### Create Virtual Environment and Configure Environment Variables

Create `.env` in project root from `.env.example` if running locally without Docker:

```
DATABASE_URL=postgresql+psycopg://secure_exam_user:secure_exam_password@localhost:5432/secure_exam_portal
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
FRONTEND_BASE_URL=http://localhost:5173
GOOGLE_CLIENT_ID=your_google_oauth_client_id
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=true
```

---

### Run Application with Docker

```bash
docker compose up --build
```

Open:

```
Frontend UI: http://localhost:5173
Login page: http://localhost:5173/login
Register page: http://localhost:5173/register
Backend API docs: http://localhost:8001/docs
```

---

### API

Versioned API endpoints:

```
/api/v1/health
/api/v1/auth/login
/api/v1/auth/register
/api/v1/auth/google
/api/v1/admin/dashboard
/api/v1/admin/students
/api/v1/admin/students/bulk
/api/v1/admin/exams
/api/v1/admin/exams/bulk
/api/v1/admin/assignments
/api/v1/student/dashboard
/api/v1/student/assignments
/api/v1/student/attempts/history
```

Interactive API docs:

```
http://localhost:8001/docs
```

All API responses use:

- JSON format
- Standard HTTP status codes
- Structured error responses

### Bulk Upload Formats

Bulk students textarea:

```text
Full Name,username,email,password
```

Bulk exams textarea:

```json
{
  "exams": [
    {
      "title": "Computer Basics",
      "description": "Introductory MCQ exam",
      "duration_minutes": 20,
      "questions": [
        {
          "question_text": "CPU stands for?",
          "option_a": "Central Processing Unit",
          "option_b": "Computer Personal Unit",
          "option_c": "Central Power Utility",
          "option_d": "Control Process User",
          "correct_option": "A",
          "marks": 2
        }
      ]
    }
  ]
}
```

---

### Default Credentials (Dev Only)

Admin:

```
admin / admin123
```

Student:

```
student1 / student123
```

---

### Maintainer

Sameer Alam
Backend Developer | Python | FastAPI | System Design
