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

### Live Demo (Legacy Version)

[https://sameeralam3127.pythonanywhere.com/](https://sameeralam3127.pythonanywhere.com/)

> ⚠️ The live demo reflects the earlier SQLite-based version.
> The current branch introduces PostgreSQL + modular architecture.

---

### Architecture Overview (High-Level Architecture)

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

### Features (Admin Capabilities)

- Dashboard analytics
- User management (CRUD)
- Exam lifecycle management
- Result tracking and reporting
- Role-based access enforcement

### Student Capabilities

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
- Migration support (Flask-Migrate)
- Secure environment variable handling
- Structured logging

---

### Project Structure

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

### Setup (Development Mode) Clone Repository

```bash
git clone https://github.com/sameeralam3127/SecureExamPortal.git
cd SecureExamPortal
```

---

### Create Virtual Environment and Configure Environment Variables

Create `.env` in project root:

```
FLASK_SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://examuser:password@localhost:5432/exam_portal

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

---

### Run Application (Dev)

```bash
python run.py
```

---

### API (Planned / In Progress)

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
Backend Developer | Python | Flask | System Design
