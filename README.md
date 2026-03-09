# Placement Portal Application 

This document is a practical manual for running and using the Placement Portal.
The application is built with Flask, Jinja templates, Bootstrap, and SQLite.

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

- Backend: `Flask`
- Frontend: `Jinja2`, `HTML`, `CSS`, `Bootstrap`
- Database: `SQLite`
- Charts: `Matplotlib` (server-side image generation)

## 3) Project Structure (Important Files)

- Entry point: [`app.py`](/Users/aryatilak/Documents/Placement-Portal-Application/app.py)
- App factory and DB setup: [`init.py`](/Users/aryatilak/Documents/Placement-Portal-Application/init.py)
- Routes and business logic: [`routes.py`](/Users/aryatilak/Documents/Placement-Portal-Application/routes.py)
- DB models: [`models.py`](/Users/aryatilak/Documents/Placement-Portal-Application/models.py)
- Form validation: [`forms.py`](/Users/aryatilak/Documents/Placement-Portal-Application/forms.py)
- Templates: `/templates`
- CSS theme: [`static/theme.css`](/Users/aryatilak/Documents/Placement-Portal-Application/static/theme.css)

## 4) Installation and Run

### 4.1 Prerequisites

- Python 3.10+ recommended
- `pip`

### 4.2 Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.3 Start the App

```bash
python3 app.py
```

Default local URL:

- `http://127.0.0.1:5000`

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

- Students and companies register from the homepage.
- Admin logs in directly.
- Company account requires admin approval before full usage.
- Student/Company/Admin are redirected to their own dashboards after login.

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

Charts are generated in backend (`routes.py`) using Matplotlib and rendered as images.

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
