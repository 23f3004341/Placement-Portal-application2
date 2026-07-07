# Placement Portal Application 

This document is a practical manual for running and using the Placement Portal.
The application is built with a VueJS single-page UI, Flask JSON APIs,
Bootstrap, SQLite, Redis, and Celery.

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
- Frontend UI: `VueJS` CLI single-page app, `Bootstrap`, and simple CSS
- Database: `SQLite`
- Cache: `Redis`
- Batch jobs: `Celery` with `Redis`
- Charts: `Chart.js`

## 3) Project Structure (Important Files)

- Entry point: `app.py`
- Backend folder: `backend/`
- App factory and DB setup: `backend/init.py`
- API routes and business logic: `backend/routes/api_routes.py`
- Blueprint route package: `backend/routes/`
- DB models package: `backend/models/`
- Background jobs: `backend/tasks.py`
- Frontend folder: `frontend/`
- Frontend browser entry: `frontend/public/index.html`
- Vue CLI config: `frontend/vue.config.js`
- Vue app shell: `frontend/src/App.vue`
- Vue source components: `frontend/src/components/`
- CSS theme: `frontend/src/assets/theme.css`
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
cd ../frontend
npm install
```

### 4.3 Start the Backend API

```bash
cd backend
python3 app.py
```

Default backend URL:

- `http://127.0.0.1:5000`

### 4.4 Start the Vue CLI Frontend

```bash
cd frontend
npm run serve
```

Default frontend URL:

- `http://127.0.0.1:8080`

### 4.5 Start Redis and Celery Jobs

Run Redis locally, then start the worker and scheduler in separate terminals:

```bash
redis-server
```

```bash
cd backend
celery -A app.celery worker --loglevel=info
```

```bash
cd backend
celery -A app.celery beat --loglevel=info
```

Useful environment variables:

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `ADMIN_EMAIL`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, `MAIL_SENDER`
- `CHAT_WEBHOOK_URL`
- `SMS_WEBHOOK_URL` (provider-neutral JSON webhook accepting `to` and `message`)
- `INTERVIEW_REMINDER_HOURS` (default: `24`)
- `DAILY_REMINDER_HOUR`, `DAILY_REMINDER_MINUTE`, `REMINDER_LOOKAHEAD_DAYS`
- `CACHE_DEFAULT_TIMEOUT`, `CACHE_SEARCH_TIMEOUT`

Example daily deadline reminder setup:

```bash
export DAILY_REMINDER_HOUR=9
export DAILY_REMINDER_MINUTE=0
export REMINDER_LOOKAHEAD_DAYS=3
export CHAT_WEBHOOK_URL="https://chat.googleapis.com/..."
export SMS_WEBHOOK_URL="https://your-sms-provider.example/send"
cd backend
celery -A app.celery worker --loglevel=info
```

Start Celery beat in another terminal with the same exported values:

```bash
export DAILY_REMINDER_HOUR=9
export DAILY_REMINDER_MINUTE=0
export REMINDER_LOOKAHEAD_DAYS=3
export CHAT_WEBHOOK_URL="https://chat.googleapis.com/..."
export SMS_WEBHOOK_URL="https://your-sms-provider.example/send"
cd backend
celery -A app.celery beat --loglevel=info
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

## 6) Login and Role Access

- Students and companies register from the Vue application.
- Admin logs in directly.
- Company account requires admin approval before full usage.
- The Vue router opens the role-specific dashboard after login.
- Flask exposes data and mutations through `/api/...` JSON endpoints.
- Jinja2 is not used for the browser UI; it is only used for backend-generated email bodies.

## 6.1 Backend Jobs

- Hourly interview reminders notify students by email and optional Google Chat/SMS webhooks.
- Daily application-deadline reminders remain available as an additional student notification.
- On the first day of each month, the admin receives the institute HTML activity report and companies receive company-specific HTML/PDF reports.
- Students and companies can trigger application/placement-history CSV exports. Each export runs in Celery and sends a completion alert.
- Redis caches dashboard metrics, approved job listings, company search, student search, and public analytics with TTL and mutation-time invalidation.

## 6.2 Frontend, PWA, Analytics, and ATS

- Bootstrap layouts include mobile breakpoints and HTML5/Vue client validation; every mutation is validated again by the Flask API.
- The public landing page uses Chart.js for placement trends, application funnel data, and approved-job skill demand.
- The ATS résumé screener is available to students and companies inside the Vue UI.
- `manifest.webmanifest` and the root-scoped service worker provide installable PWA behavior and an offline fallback.
- Vue, Bootstrap, and Chart.js are installed through npm and bundled by Vue CLI. CDN scripts are not used by the active frontend.

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

Charts and analytics data are generated by the backend API layer in `backend/routes/api_routes.py`.

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
