# Secure Exam Portal

Secure Exam Portal is a production-ready online examination system for creating,
assigning, taking, and reviewing MCQ exams. It ships with a FastAPI backend,
PostgreSQL persistence, a database-backed background worker, an Nginx edge
proxy, and a Vite React frontend, with Docker Compose workflows for development
and production-style deployments.

## Features

- Student registration, password login, bearer-token sessions, and optional Google sign-in.
- Role-based admin and student dashboards.
- Admin student management, including bulk student creation.
- Admin exam authoring, including bulk exam upload and MCQ question banks.
- Exam assignment workflow with SMTP email jobs processed asynchronously.
- Submitted-attempt report jobs processed by a database-backed worker queue.
- Student exam attempts with timer, autosaved answers, submission scoring, and attempt history.
- Configurable exam security controls for clipboard, context menu, inspect shortcuts, fullscreen, and focus-loss tracking.
- Admin views for security incidents, queued jobs, and completed reports.
- Production validation for secrets, database URLs, and CORS origins.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Uvicorn, Gunicorn
- Worker: database-backed queue for email and report jobs
- Frontend: React, Vite, Nginx
- Edge: Nginx reverse proxy with forwarded headers
- Auth: Password login, role checks, optional Google Identity Services
- Containers: Docker and Docker Compose
- Notifications: Optional SMTP assignment email

## Repository Layout

```text
SecureExamPortal/
├── backend/
│   ├── app/
│   │   ├── config/
│   │   ├── extensions/
│   │   ├── models/
│   │   ├── modules/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── utils/
│   ├── docker/Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   └── wsgi.py
├── docker/
│   └── nginx.conf
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

## Quick Start

Run the development stack with hot reload:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Local URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8001`
- Nginx entrypoint: `http://localhost:8080`
- API docs: `http://localhost:8001/docs`

To bootstrap an admin account in a fresh development database, provide these
values before starting the stack:

```bash
INITIAL_ADMIN_USERNAME=admin \
INITIAL_ADMIN_PASSWORD=change-me \
INITIAL_ADMIN_EMAIL=admin@example.com \
docker compose -f docker-compose.dev.yml up --build
```

Student accounts can also register from the login page. Admin accounts are
created only through the initial-admin bootstrap path.

## Environment Configuration

Copy `.env.example` to `.env` for production-style runs:

```bash
cp .env.example .env
```

Required production values:

```env
POSTGRES_PASSWORD=replace-with-a-strong-database-password
DATABASE_URL=postgresql+psycopg://secure_exam_user:replace-with-a-strong-database-password@db:5432/secure_exam_portal
AUTH_SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=["https://your-domain.example"]
FRONTEND_BASE_URL=https://your-domain.example
```

Optional integrations, worker settings, and bootstrap values:

```env
GOOGLE_CLIENT_ID=
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=no-reply@secureexamportal.com
SMTP_USE_TLS=true
WORKER_POLL_INTERVAL_SECONDS=2
INITIAL_ADMIN_USERNAME=
INITIAL_ADMIN_PASSWORD=
INITIAL_ADMIN_EMAIL=
INITIAL_ADMIN_FULL_NAME=Portal Administrator
```

In production, the backend rejects the default local secret, local database
passwords, and localhost CORS origins.

## Production-Style Docker Run

Build and run the production-style stack from this repository:

```bash
docker compose up --build
```

The production Compose stack starts separate services for:

- `nginx`: public entrypoint and reverse proxy for `/api` and frontend traffic
- `backend`: FastAPI API workers behind Nginx
- `worker`: queue consumer for assignment email and submitted-attempt report jobs
- `db`: PostgreSQL storage for application data and queued jobs
- `frontend`: built React assets served by Nginx

The Nginx entrypoint listens on `FRONTEND_PORT`, which defaults to `80`.

Scale API or worker capacity horizontally by adding replicas behind the Nginx entrypoint:

```bash
docker compose up --build --scale backend=2 --scale worker=2
```

Assignment notifications and submitted-attempt reports are queued in the
database and processed by the `worker` service. Admins can inspect recent queue
activity through `/api/v1/admin/jobs` and completed report jobs through
`/api/v1/admin/reports`.

## Published Docker Image

Published image:

```text
ghcr.io/sameeralam3127/secure-exam-portal:latest
```

Pull it:

```bash
docker pull ghcr.io/sameeralam3127/secure-exam-portal:latest
```

Build the single image locally:

```bash
docker build -t secure-exam-portal:local .
```

Run the local image:

```bash
docker run --env-file .env -p 80:80 secure-exam-portal:local
```

## Local Commands

Frontend commands:

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
npm test
```

Backend local setup:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Worker local run:

```bash
cd backend
python -m app.worker
```

The backend expects a PostgreSQL database. The development compose file exposes
PostgreSQL on `localhost:5432` with:

```text
Database: secure_exam_portal
User: secure_exam_user
Password: local_dev_password
```

## API Surface

Main versioned endpoints:

```text
GET  /api/v1/health
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/google
GET  /api/v1/auth/me

GET  /api/v1/admin/dashboard
GET  /api/v1/admin/students
POST /api/v1/admin/students
POST /api/v1/admin/students/bulk
GET  /api/v1/admin/exams
POST /api/v1/admin/exams
POST /api/v1/admin/exams/bulk
GET  /api/v1/admin/assignments
POST /api/v1/admin/assignments
GET  /api/v1/admin/jobs
GET  /api/v1/admin/reports
GET  /api/v1/admin/security-incidents

GET  /api/v1/student/dashboard
GET  /api/v1/student/assignments
POST /api/v1/student/assignments/{assignment_id}/start
PUT  /api/v1/student/attempts/{attempt_id}/answers
POST /api/v1/student/attempts/{attempt_id}/submit
POST /api/v1/student/attempts/{attempt_id}/security-incidents
GET  /api/v1/student/attempts/history
```

Interactive OpenAPI docs are available at `/docs` when the backend is running.

## Bulk Upload Formats

Bulk students use one student per line:

```text
Full Name,username,email,password
Jane Student,jane,jane@example.com,secret123
```

Bulk exams use JSON:

```json
{
  "exams": [
    {
      "title": "Computer Basics",
      "description": "Introductory MCQ exam",
      "duration_minutes": 20,
      "block_clipboard": true,
      "block_context_menu": true,
      "block_inspect_shortcuts": true,
      "enforce_fullscreen": false,
      "track_focus_loss": true,
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

## Releases

Docker images are published to GitHub Container Registry by the repository's
Docker image workflow.

Publishing rules:

- Pushes to `main` publish `latest`, `main`, and `sha-*` image tags.
- Version tags such as `v1.0.0` publish versioned images and create a GitHub Release.
- Publishing a GitHub Release also runs the Docker image workflow.

Create a release build:

```bash
git tag v1.0.0
git push origin v1.0.0
```
