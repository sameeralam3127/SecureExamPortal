# Secure Exam Portal

Secure Exam Portal is a production-oriented online examination platform for
creating, assigning, taking, and reviewing MCQ exams. It includes a FastAPI API,
PostgreSQL persistence, a queue worker for emails and reports, an Nginx edge
proxy, and a Vite React frontend.

> [!IMPORTANT]
> This repository is designed for real deployment, not only local demos. The
> production stack validates secrets, CORS origins, database URLs, token
> lifetimes, HTTPS frontend URLs, Google sign-in domains, and Nginx edge
> configuration before the app is exposed.

## What It Does

- Student registration, password login, bearer-token sessions, and optional
  Google Identity Services sign-in.
- Role-based admin and student dashboards.
- Admin student management, including single-student creation and CSV-style
  bulk upload.
- Admin exam authoring, including bulk JSON exam upload and MCQ question banks.
- Exam assignment workflow with optional SMTP email notifications.
- Database-backed worker queue for assignment emails and submitted-attempt
  reports.
- Student exam attempts with timer, autosaved answers, submission scoring, and
  attempt history.
- Configurable exam security controls for clipboard, context menu, inspect
  shortcuts, fullscreen, and focus-loss tracking.
- Admin visibility into queued jobs, completed reports, and security incidents.
- Production-ready Nginx reverse proxy with security headers, auth/API rate
  limits, ACME challenge support, and optional Let's Encrypt TLS config.

## Architecture

```text
Browser
  |
  v
Nginx edge proxy
  |-- /api/*  -> FastAPI backend
  |-- /*      -> Vite React frontend
  |
  |-- /.well-known/acme-challenge/* -> Certbot webroot

FastAPI backend
  |-- PostgreSQL
  |-- Database-backed jobs

Worker
  |-- PostgreSQL job queue
  |-- SMTP provider, when configured
```

## Tech Stack

| Layer           | Technology                                                     |
| --------------- | -------------------------------------------------------------- |
| Backend API     | FastAPI, SQLAlchemy, Pydantic, Uvicorn, Gunicorn               |
| Database        | PostgreSQL 16                                                  |
| Background jobs | Database-backed queue worker                                   |
| Frontend        | React, Vite                                                    |
| Edge            | Nginx reverse proxy                                            |
| Auth            | Password login, role checks, optional Google Identity Services |
| Deployment      | Docker, Docker Compose, optional Certbot/Let's Encrypt         |
| Registry        | GitHub Container Registry                                      |

## Quick Start

Run the development stack with hot reload:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Development URLs:

| Service          | URL                          |
| ---------------- | ---------------------------- |
| Frontend         | `http://localhost:5173`      |
| Backend API      | `http://localhost:8001`      |
| Nginx entrypoint | `http://localhost:8080`      |
| OpenAPI docs     | `http://localhost:8001/docs` |

Bootstrap the first admin account in a fresh development database:

```bash
INITIAL_ADMIN_USERNAME=admin \
INITIAL_ADMIN_PASSWORD=change-me \
INITIAL_ADMIN_EMAIL=admin@example.com \
docker compose -f docker-compose.dev.yml up --build
```

> [!NOTE]
> Student accounts can register from the login page. Admin accounts are created
> through the initial-admin bootstrap path, so do not leave bootstrap
> credentials enabled after the first production admin exists.

## Production Environment

Copy the sample environment file and replace every placeholder before starting
the production Compose stack:

```bash
cp .env.example .env
```

Required production values:

```env
ENVIRONMENT=production
POSTGRES_DB=secure_exam_portal
POSTGRES_USER=secure_exam_user
POSTGRES_PASSWORD=replace-with-a-strong-database-password
DATABASE_URL=postgresql+psycopg://secure_exam_user:replace-with-a-strong-database-password@db:5432/secure_exam_portal
AUTH_SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=120
AUTH_RATE_LIMIT_ATTEMPTS=10
AUTH_RATE_LIMIT_WINDOW_SECONDS=60
CORS_ORIGINS=["https://your-domain.example"]
FRONTEND_BASE_URL=https://your-domain.example
FRONTEND_PORT=80
HTTPS_PORT=443
VITE_API_BASE_URL=/api
```

Optional integrations and bootstrap values:

```env
GOOGLE_CLIENT_ID=
GOOGLE_ALLOWED_DOMAINS=[]
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

> [!CAUTION]
> Never commit `.env`. Rotate `AUTH_SECRET_KEY`, database passwords, SMTP
> credentials, and OAuth credentials if they are ever exposed.

> [!IMPORTANT]
> In production, the backend rejects weak defaults: local development secrets,
> secrets shorter than 32 characters, token lifetimes above 240 minutes, local
> database passwords, localhost CORS origins, and non-HTTPS frontend URLs.

Generate a strong application secret:

```bash
openssl rand -hex 32
```

## Production Deployment

Start the production-style stack:

```bash
docker compose up --build -d
```

The stack starts:

| Service    | Purpose                                                         |
| ---------- | --------------------------------------------------------------- |
| `nginx`    | Public entrypoint, reverse proxy, security headers, rate limits |
| `backend`  | FastAPI application workers                                     |
| `worker`   | Queue consumer for email and report jobs                        |
| `db`       | PostgreSQL data store                                           |
| `frontend` | Built React app served behind Nginx                             |
| `certbot`  | Optional TLS certificate management profile                     |

The default `docker/nginx.conf` is suitable for initial public setup because it
serves `/.well-known/acme-challenge/`, proxies the frontend and API, adds
security headers, and rate limits auth/API traffic.

### Enable HTTPS

Point DNS for your production domain at the server, set `CORS_ORIGINS` and
`FRONTEND_BASE_URL` to the real `https://` domain, then start the stack.

Issue the first Let's Encrypt certificate:

```bash
docker compose --profile tls run --rm certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  --email admin@your-domain.example \
  --agree-tos \
  --no-eff-email \
  -d your-domain.example
```

After the certificate exists in the shared `letsencrypt` volume, update the
Nginx config mount in `docker-compose.yml` from:

```yaml
- ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
```

to:

```yaml
- ./docker/nginx.tls.conf:/etc/nginx/conf.d/default.conf:ro
```

Reload Nginx:

```bash
docker compose up -d nginx
```

Renew certificates from the same host:

```bash
docker compose --profile tls run --rm certbot renew --webroot --webroot-path /var/www/certbot
docker compose exec nginx nginx -s reload
```

> [!WARNING]
> Do not put the TLS config in front of a domain until certificates exist. Use
> the default HTTP config first so Certbot can complete the ACME challenge.

### Scale Services

Scale API and worker capacity behind the Nginx entrypoint:

```bash
docker compose up --build --scale backend=2 --scale worker=2 -d
```

## Google Sign-In

Set `GOOGLE_CLIENT_ID` to the OAuth web client ID from Google Cloud. The same
value is passed into the frontend build through Docker Compose.

To restrict sign-ins to a school or company domain:

```env
GOOGLE_ALLOWED_DOMAINS=["example.edu"]
```

Leave the list empty to allow any verified Google email:

```env
GOOGLE_ALLOWED_DOMAINS=[]
```

> [!TIP]
> Configure Google authorized JavaScript origins for the exact production
> domain that users open in the browser.

## Email And Background Jobs

Assignment notifications and submitted-attempt reports are stored in the
database-backed queue and processed by the `worker` service.

Admins can inspect queue activity through:

```text
GET /api/v1/admin/jobs
GET /api/v1/admin/reports
```

SMTP is optional. If SMTP variables are empty, the portal still runs, but email
delivery features will not send real messages.

## Local Development Commands

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
npm test
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Worker:

```bash
cd backend
python -m app.worker
```

Development database defaults:

```text
Host: localhost:5432
Database: secure_exam_portal
User: secure_exam_user
Password: local_dev_password
```

## Quality Checks

Run these before opening a pull request:

```bash
python3 -m compileall backend/app

cd frontend
npm test
npm run build
npm run lint
```

Validate the production Compose file after editing deployment settings:

```bash
docker compose --env-file .env.example config
```

> [!NOTE]
> Docker and Nginx validation require those tools to be available on the host or
> in CI. If Docker is not running locally, treat image and edge validation as
> incomplete until CI or the production server checks them.

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

## Docker Image

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

## Release Workflow

Docker images are published to GitHub Container Registry by
`.github/workflows/docker-publish.yml`.

Publishing rules:

- Pushes to `main` publish `latest`, `main`, and `sha-*` image tags.
- Version tags such as `v1.0.0` publish versioned images and create a GitHub
  Release.
- Publishing a GitHub Release also runs the Docker image workflow.

Create a release build:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Security Notes

> [!IMPORTANT]
> Treat the production server as the source of truth for final deployment
> validation. Local checks are useful, but TLS, DNS, real OAuth origins, SMTP,
> firewall rules, and certificate renewal must be verified on the host that
> serves users.

Recommended production practices:

- Use a strong `AUTH_SECRET_KEY` and rotate it during incident response.
- Keep `.env` out of Git and out of public logs.
- Keep `CORS_ORIGINS` limited to real application domains.
- Use HTTPS-only `FRONTEND_BASE_URL` in production.
- Restrict `GOOGLE_ALLOWED_DOMAINS` when the portal is for one institution.
- Back up the PostgreSQL volume before upgrades.
- Monitor worker logs so queued emails and reports do not silently stall.

## License

This project is released under the license in `LICENSE`.
