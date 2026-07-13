# Placement Portal Application 

This document is a practical manual for running and using the Placement Portal.
The application is built with a CDN-based Vue single-page UI, Flask JSON APIs,
Bootstrap/Chart.js from CDN, SQLite, Redis/Celery, MailHog, and Google Chat webhook notifications.

## 1) What This System Does

The portal manages campus placement operations for 3 roles:

- `Admin` (Placement Cell)
- `Company`
- `Student`

Main modules:

- Account registration and role-based login
- Company approval and drive approval flow
- Placement drive creation and management
- Student applications with status tracking
- Placement history and dashboard analytics

## 2) Tech Stack

- Backend API: `Flask`
- Frontend UI: CDN `Vue`, CDN `Bootstrap`, CDN `Chart.js`, and simple CSS
- Database: `SQLite`
- Batch jobs: `Celery` with `Redis`
- Charts: `Chart.js`

## 3) Project Structure (Important Files)

- Entry point: `app.py`
- Backend folder: `backend/`
- Main app and app factory: `backend/app.py`
- Main config, ports, Redis, Celery, MailHog, webhooks: `backend/config.py`
- Flask extensions: `backend/extensions.py`
- Table creation/bootstrap: `backend/create_tables.py`
- Database models: `backend/models.py`
- Default admin seed: `backend/seed_admin.py`
- API routes by role/work area: `backend/routes/`
- Cron/task route wrappers: `backend/routes/cron.py`, `backend/routes/tasks_routes.py`
- Celery entry point: `backend/celery_app.py`
- Background jobs by job type: `backend/tasks/`
- Frontend folder: `frontend/`
- Frontend browser entry: `frontend/index.html`
- Frontend app script: `frontend/main.js`
- Frontend components: `frontend/components/`
- Frontend service placeholder: `frontend/services/api.js`
- CSS theme: `frontend/theme.css`
- Backend email templates: `backend/templates/emails/`

## 4) Installation and Run

### 4.1 Prerequisites

- Python 3.10+ recommended
- `pip`

### 4.2 Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
```

### 4.3 Start the App

```bash
python3 app.py
```

Default app URL:

- `http://127.0.0.1:5000`

There is no separate frontend server now. Flask serves the CDN frontend directly.

### 4.4 Start Redis and Celery Jobs

Run Redis locally, then start the worker and scheduler in separate terminals:

```bash
redis-server
```

```bash
cd backend
celery -A celery_app.celery worker --loglevel=info
```

```bash
cd backend
celery -A celery_app.celery beat --loglevel=info
```

Celery beat runs task (a) and task (b) every `120` seconds by default for viva/demo testing.

Useful environment variables:

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `ADMIN_EMAIL`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, `MAIL_SENDER`
- `CHAT_WEBHOOK_URL`
- `CELERY_SYNC_SECONDS` (default: `120`)
- `REMINDER_LOOKAHEAD_DAYS`

### 4.5 Start MailHog

```bash
/Users/aryatilak/go/bin/MailHog \
  -smtp-bind-addr 127.0.0.1:1025 \
  -api-bind-addr 127.0.0.1:8025 \
  -ui-bind-addr 127.0.0.1:8025 \
  -api-host http://127.0.0.1:8025
```

MailHog ports are in `backend/config.py`:

- SMTP: `127.0.0.1:1025`
- UI/API: `http://127.0.0.1:8025`

### 4.6 Google Chat Webhook

Do not hardcode the webhook URL in Python files. Export it before starting Flask/Celery:

```bash
export CHAT_WEBHOOK_URL="<your Google Chat webhook URL>"
```

Then start Flask, Celery worker, and Celery beat from terminals where this variable exists.

Example Celery setup:

```bash
export REMINDER_LOOKAHEAD_DAYS=3
export CHAT_WEBHOOK_URL="<your Google Chat webhook URL>"
cd backend
celery -A celery_app.celery beat --loglevel=info
```

To run tests, use the project root folder, not the `backend` folder:

```bash
cd ..
python3 -m unittest discover -s tests
```

## 5) Database and Default Admin

On startup, the app:

- creates SQLite tables (`db.create_all()`)
- applies runtime schema safety updates
- creates default admin if missing

Default admin values can be controlled with environment variables:

- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`
- `DEFAULT_ADMIN_NAME`
- `DEFAULT_ADMIN_PHONE`
- `DEFAULT_ADMIN_EMPLOYEE_CODE`
- MailHog is the default local email target. The MailHog settings live in `backend/config.py`.

## 6) Login and Role Access

- Students and companies register from the Vue application.
- Admin logs in directly.
- Company account requires admin approval before full usage.
- The Vue router opens the role-specific dashboard after login.
- Flask exposes data and mutations through `/api/...` JSON endpoints.
- Jinja2 is not used for the browser UI; it is only used for backend-generated email bodies.

## 6.1 Backend Jobs

- Hourly interview reminders notify students by email and optional Google Chat/SMS webhooks.
- Task (a): daily application-deadline reminders send student MailHog emails and Google Chat webhook messages.
- Task (b): monthly activity reports send admin/company MailHog emails and a Google Chat webhook summary.
- The app does not show an internal notifications panel. Notification events are delivered through Google Chat webhook and MailHog email, while the database keeps a small delivery log to avoid duplicate sends.
- Celery beat syncs task (a) and task (b) every 120 seconds by default. Admins can also run both tasks manually from the dashboard.
- Students and companies can trigger application/placement-history CSV exports. Each export runs in Celery and sends a completion alert.
- Redis is used as the Celery broker/result backend for background jobs.

## 6.2 Frontend and Analytics

- Bootstrap layouts include mobile breakpoints and HTML5/Vue client validation; every mutation is validated again by the Flask API.
- The public landing page uses CDN Chart.js for placement trends, application funnel data, and approved-job skill demand.
- Vue, Bootstrap, and Chart.js are loaded from CDN in `frontend/index.html`.
- The browser UI is served as plain static files, which keeps local testing predictable.

## 7) Role-Wise Manual

### 7.1 Admin Manual

From admin sidebar:

- `Dashboard`: view system analytics
- `Companies`: review pending company registrations, manage approved/rejected companies
- `All Placement Drives`: list of all drives, open drive detail, approve/reject pending drives
- `Applications and Placements`: global records
- `Search Students`: search, view, edit, blacklist/unblacklist, delete

Admin controls include:

- approve/reject company registrations
- approve/reject placement drives
- blacklist/unblacklist users
- edit student/company profiles
- delete accounts

### 7.2 Company Manual

Company can:

- complete profile
- create/edit/close/remove placement drives
- view applicants for each drive
- update applicant status (`shortlisted`, `selected`, `rejected`)

Important behavior:

- withdrawn student applications are hidden from company-side views
- company dashboard charts/counts exclude withdrawn applications

### 7.3 Student Manual

Student can:

- update profile and resume
- browse approved drives
- apply to drives
- undo application from approved drives page
- view combined `Applications and Placements` page

Application flow:

1. Initial state: `Apply` button visible  
2. After apply: status is `Applied`, `Undo` becomes available  
3. After undo: status becomes `Withdrawn`, `Apply` becomes available again  
4. If company updates status to `Shortlisted/Selected/Rejected`, apply/undo controls are removed

## 8) Form/Validation Rules

Validation is done with Flask-WTF and route-level checks.

Examples:

- duplicate application prevention
- role authorization checks on protected routes
- CGPA/degree/branch eligibility checks before student apply
- required fields and format checks (email, pincode, phone, etc.)
- company registration:
  - company email is login email
  - HR email must be different from company email

## 9) Salary/Stipend Unit Behavior

In company drive form:

- salary amount is stored as float
- unit options are `LPA` or `K/month`
- no automatic unit conversion is applied

## 10) Dashboards and Charts

Charts and analytics data are generated by the backend API layer in `backend/routes/public.py`.

- Admin:
  - application status pie chart
  - drive outcomes chart
- Company:
  - drive status pie chart
  - applicant progress pie chart

Legend styles and status color mapping are configured in route-side chart helpers.

## 11) Pincode Autofill

Registration/edit forms use pincode lookup to auto-fill city/state/country via:

- `https://api.postalpincode.in/pincode/<pincode>`

## 12) Troubleshooting

### App starts but no styles/charts update

- hard refresh browser (`Ctrl/Cmd + Shift + R`)

### DB schema mismatch after model update

- restart app to trigger runtime schema patching
- if needed for local dev, recreate DB after backup

### Login fails unexpectedly

- verify role while logging in
- verify account approval/active status from admin side

## 13) Quick Feature Checklist

- role-based authentication
- company approval flow
- drive approval flow
- application lifecycle management
- student undo/reapply behavior
- admin management actions
- placement history tracking
- server-generated analytics charts
