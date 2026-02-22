# Secure Exam Portal

A scalable, modular, and API-enabled **Enterprise Online Examination Platform** built with Flask.

SecureExamPortal is evolving from an academic MCA project into a production-ready backend architecture featuring:

- Modular domain-driven structure
- PostgreSQL database support
- RESTful API (versioned)
- Dockerized deployment
- Secure authentication & role-based access control
- Enterprise-grade configuration management

---

## Live Demo (Legacy Version)

[https://sameeralam3127.pythonanywhere.com/](https://sameeralam3127.pythonanywhere.com/)

> ⚠️ The live demo reflects the earlier SQLite-based version.
> The current branch introduces PostgreSQL + modular architecture.

---

# Architecture Overview

## High-Level Architecture

```
Client (Browser / API Consumer)
        ↓
Gunicorn (WSGI Server)
        ↓
Flask Application (Modular Architecture)
        ↓
PostgreSQL Database
```

---

# Features

## Admin Capabilities

- Dashboard analytics
- User management (CRUD)
- Exam lifecycle management
- Result tracking and reporting
- Role-based access enforcement

## Student Capabilities

- Exam dashboard
- Timed examinations
- Auto-submission
- Performance review
- Historical attempt tracking

---

# Enterprise Enhancements (New Architecture)

- Modular application structure
- PostgreSQL support (production-ready)
- Environment-based configuration (dev / prod / test)
- Docker & Docker Compose setup
- Gunicorn production server
- CORS configuration for API clients
- API-first design (`/api/v1`)
- Migration support (Flask-Migrate)
- Secure environment variable handling
- Structured logging

---

# Project Structure

```
SecureExamPortal/
│
├── app/
│   ├── config/          # Environment-based configuration
│   ├── extensions/      # Flask extension initialization
│   ├── modules/         # Domain modules (auth, exams, admin, etc.)
│   ├── models/          # Database models
│   ├── services/        # Business logic layer
│   ├── repositories/    # Data access abstraction
│   ├── schemas/         # Serialization (API layer)
│   └── utils/
│
├── migrations/          # Database migrations
├── docker/              # Containerization configs
├── tests/               # Unit & integration tests
├── wsgi.py              # Production entrypoint
├── manage.py            # CLI management script
└── requirements.txt
```

---

# Tech Stack

Backend:

- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Dance (Google OAuth)
- Flask-Migrate
- Flask-CORS
- Gunicorn

Database:

- PostgreSQL (Primary)
- SQLite (Development fallback)

Containerization:

- Docker
- Docker Compose

Security:

- Password hashing (Werkzeug)
- Role-based access control
- Environment-based secrets
- OAuth 2.0 integration

Frontend:

- Bootstrap 5

---

# Setup (Development Mode)

## 1. Clone Repository

```bash
git clone https://github.com/sameeralam3127/SecureExamPortal.git
cd SecureExamPortal
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create `.env` in project root:

```
FLASK_SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://examuser:password@localhost:5432/exam_portal

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

---

## 4. Run Application (Dev)

```bash
python run.py
```

---

# Docker Deployment (Recommended)

## 1. Build & Run

```bash
docker compose up --build
```

Services:

- `web` (Flask + Gunicorn)
- `db` (PostgreSQL)

---

## 2. Apply Database Migrations

```bash
docker exec -it secure_exam_app flask db upgrade
```

---

# API (Planned / In Progress)

Versioned API endpoints:

```
/api/v1/auth
/api/v1/exams
/api/v1/results
```

All API responses:

- JSON format
- Standard HTTP status codes
- Structured error responses

Future: JWT-based authentication.

---

# Default Credentials (Dev Only)

Admin:

```
admin / admin123
```

Student:

```
student1 / student123
```

---

# Security Considerations

- Never commit `.env`
- Use strong SECRET_KEY
- Enforce HTTPS in production
- Disable OAUTHLIB_INSECURE_TRANSPORT outside development
- Use PostgreSQL in production

---

# Development Roadmap

- JWT authentication for APIs
- Rate limiting
- Nginx reverse proxy
- CI/CD pipeline
- Test coverage > 80%
- Cloud deployment (AWS / Render)

---

# Contributing

Pull requests are welcome.

Before submitting:

- Create feature branch
- Follow commit conventions
- Ensure tests pass

---

# License

MIT License
See `LICENSE` for details.

---

# Maintainer

Sameer Alam
Backend Developer | Python | Flask | System Design

---
