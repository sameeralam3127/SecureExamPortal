# Secure Exam Portal

Production-ready online examination portal with a FastAPI backend, PostgreSQL database, and React frontend.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, Gunicorn/Uvicorn
- Workers: database-backed background queue for email and report jobs
- Frontend: React, Vite, Nginx
- Containers: Docker and Docker Compose
- Auth: Password login, role-based access, optional Google sign-in
- Edge: Nginx reverse proxy with forwarded headers
- Notifications: Optional SMTP assignment email processed asynchronously

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

## Production Configuration

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

## Run With Docker

Production-style stack built from this repository:

```bash
docker compose up --build
```

The production Compose stack starts separate services for:

- `nginx`: public entrypoint and reverse proxy for `/api` and frontend traffic
- `backend`: FastAPI API workers behind Nginx
- `worker`: queue consumer for assignment email and submitted-attempt report jobs
- `db`: PostgreSQL storage for application data and queued jobs
- `frontend`: built React assets served by Nginx

Scale API or worker capacity horizontally by adding replicas behind the Nginx entrypoint:

```bash
docker compose up --build --scale backend=2 --scale worker=2
```

Production stack using the published GitHub Packages image:

```bash
docker pull ghcr.io/sameeralam3127/secure-exam-portal:latest
```

Create `.env` from `.env.example`, set the required production values, then use the published image in your deployment:

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

  app:
    image: ghcr.io/sameeralam3127/secure-exam-portal:latest
    ports:
      - "80:80"
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

volumes:
  postgres_data:
```

Development stack with hot reload:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Local development URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8001`
- Nginx entrypoint: `http://localhost:8080`
- API docs: `http://localhost:8001/docs`

Assignment notifications and submitted-attempt reports are queued in the database and processed by
the `worker` service. Admins can inspect recent queue activity through:

```text
/api/v1/admin/jobs
/api/v1/admin/reports
```

## Docker Image

Published image:

```text
ghcr.io/sameeralam3127/secure-exam-portal:latest
```

Build the image locally:

```bash
docker build -t secure-exam-portal:local .
```

Run the local image:

```bash
docker run --env-file .env -p 80:80 secure-exam-portal:local
```

## GitHub Packages and Releases

Docker images are published to GitHub Container Registry by the `Build and Publish Docker Images`
workflow.

Published package name:

```text
ghcr.io/sameeralam3127/secure-exam-portal
```

Publishing rules:

- Push to `main` publishes `latest`, `main`, and `sha-*` image tags.
- Push a version tag like `v1.0.0` to publish versioned images and create a GitHub Release.
- Publishing a GitHub Release also runs the Docker image workflow.

Create a release build:

```bash
git tag v1.0.0
git push origin v1.0.0
```

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
/api/v1/admin/jobs
/api/v1/admin/reports
/api/v1/student/dashboard
/api/v1/student/assignments
/api/v1/student/attempts/history
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
