# Secure Exam Portal

Production-ready online examination portal with a FastAPI backend, PostgreSQL database, and React frontend. Secure Exam Portal supports role-based administration, student exam delivery, assignment tracking, autosaved answers, score history, and configurable exam security controls.

## Features

- Admin dashboard for students, exams, assignments, score reports, and security activity
- Student dashboard for assigned exams, live attempts, autosave status, and score history
- Password authentication with role-based access for admins and students
- Optional Google sign-in through `VITE_GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_ID`
- Bulk student upload from CSV-style text
- Bulk exam upload from JSON
- Configurable exam security controls:
  - block copy, paste, and cut
  - block right-click context menu
  - block common inspect/developer shortcuts
  - optionally require fullscreen
  - track focus loss, tab switches, and fullscreen exits
- Optional SMTP email notification when an exam is assigned

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, Gunicorn/Uvicorn
- Frontend: React, Vite, Nginx
- Containers: Docker and Docker Compose
- Auth: Password login, role-based access, optional Google sign-in
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
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

## Configuration

Copy `.env.example` to `.env` and replace every production placeholder before starting containers.

Required production values:

```env
POSTGRES_PASSWORD=
DATABASE_URL=
AUTH_SECRET_KEY=
CORS_ORIGINS=["https://your-domain.example"]
FRONTEND_BASE_URL=https://your-domain.example
```

Optional first-admin bootstrap for a fresh database:

```env
INITIAL_ADMIN_USERNAME=
INITIAL_ADMIN_PASSWORD=
INITIAL_ADMIN_EMAIL=
INITIAL_ADMIN_FULL_NAME=Portal Administrator
```

The application does not create seeded users, seeded passwords, or starter exams automatically.

## Run With Docker Compose

Production-style stack built from this repository:

```bash
docker compose up --build
```

Development stack with hot reload:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Local development URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8001`
- API docs: `http://localhost:8001/docs`

## Published Docker Images

Published images:

```text
sameeralam3127/secure-exam-backend:latest
sameeralam3127/secure-exam-frontend:latest
```

Create `.env` from `.env.example`, set the required production values, then use the published images in your deployment if you do not want to build locally:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: secure_exam_portal
      POSTGRES_USER: secure_exam_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    image: sameeralam3127/secure-exam-backend:latest
    environment:
      ENVIRONMENT: production
      AUTH_SECRET_KEY: ${AUTH_SECRET_KEY}
      DATABASE_URL: ${DATABASE_URL}
      CORS_ORIGINS: ${CORS_ORIGINS}
      FRONTEND_BASE_URL: ${FRONTEND_BASE_URL}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:-}
      SMTP_HOST: ${SMTP_HOST:-}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_USERNAME: ${SMTP_USERNAME:-}
      SMTP_PASSWORD: ${SMTP_PASSWORD:-}
      SMTP_FROM_EMAIL: ${SMTP_FROM_EMAIL:-no-reply@secureexamportal.com}
      SMTP_USE_TLS: ${SMTP_USE_TLS:-true}
      INITIAL_ADMIN_USERNAME: ${INITIAL_ADMIN_USERNAME:-}
      INITIAL_ADMIN_PASSWORD: ${INITIAL_ADMIN_PASSWORD:-}
      INITIAL_ADMIN_EMAIL: ${INITIAL_ADMIN_EMAIL:-}
      INITIAL_ADMIN_FULL_NAME: ${INITIAL_ADMIN_FULL_NAME:-Portal Administrator}
    depends_on:
      - db

  frontend:
    image: sameeralam3127/secure-exam-frontend:latest
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Build images locally:

```bash
docker build -t sameeralam3127/secure-exam-backend:latest -f backend/docker/Dockerfile backend
docker build -t sameeralam3127/secure-exam-frontend:latest frontend
```

Push images:

```bash
docker push sameeralam3127/secure-exam-backend:latest
docker push sameeralam3127/secure-exam-frontend:latest
```

## Local Development Without Docker

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` for the frontend when the API is not served from the same origin.

## Quality Checks

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

Backend dependencies are listed in `backend/requirements.txt`. Use the FastAPI docs at `/docs` for manual API validation when running locally.

## API Surface

Main versioned endpoints:

```text
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
/api/v1/admin/security-incidents
/api/v1/student/dashboard
/api/v1/student/assignments
/api/v1/student/assignments/{assignment_id}/start
/api/v1/student/attempts/history
/api/v1/student/attempts/{attempt_id}/answers
/api/v1/student/attempts/{attempt_id}/submit
/api/v1/student/attempts/{attempt_id}/security-incidents
```

## Bulk Upload Formats

Bulk students textarea:

```text
Full Name,username,email,password
```

Bulk exams textarea:

```json
{
  "exams": [
    {
      "title": "Exam Title",
      "description": "Exam description",
      "duration_minutes": 30,
      "block_clipboard": true,
      "block_context_menu": true,
      "block_inspect_shortcuts": true,
      "enforce_fullscreen": false,
      "track_focus_loss": true,
      "questions": [
        {
          "question_text": "Question text",
          "option_a": "Option A",
          "option_b": "Option B",
          "option_c": "Option C",
          "option_d": "Option D",
          "correct_option": "A",
          "marks": 1
        }
      ]
    }
  ]
}
```

Security flags are optional in the API schema and default to secure values when omitted.

## Deployment Notes

- Always set a strong `AUTH_SECRET_KEY` in production.
- Do not deploy with the local development database password.
- Set `CORS_ORIGINS` to the exact production frontend origins only.
- Configure SMTP only if assignment notification email is required.
- Configure Google OAuth only if Google sign-in should be enabled.
