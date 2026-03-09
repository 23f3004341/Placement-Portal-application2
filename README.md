# Placement-Portal-Application
A complete role-based Placement Portal Application built using Flask, designed to streamline campus recruitment by managing students, companies, placement drives, and applications efficiently.

## Features
# Admin (Institute Placement Cell)

View dashboard statistics (students, companies, drives, applications)

Approve or reject company registrations

Approve or reject placement drives

View and manage all students and companies

Blacklist or deactivate accounts

Search students by name, ID, or contact

Search companies by name

View complete placement history and records

# Company Portal

Register and create company profile

Login only after admin approval

Create placement drives (job postings)

Edit, close, or delete placement drives

View student applications per drive

Shortlist / Select / Reject applicants

Track number of applicants per drive

# Student Portal

Self-registration and login

Update profile and upload resume

View approved placement drives

Apply for placement drives

Prevent duplicate applications

Track application status (Applied / Shortlisted / Selected / Rejected)

View past placement history

Core Functionalities

Role-based authentication system

Programmatic database creation (No manual DB setup)

Unique constraint to prevent duplicate applications

Only approved companies can create drives

Students can view only approved drives

Complete application history maintained

Secure password hashing

Resume upload and management

Clean responsive Bootstrap UI

## API Resources (JSON)

The project now exposes role-based JSON APIs (using Flask routes + `jsonify`):

- `GET /api/v1/users/me`
- `GET /api/v1/drives`
- `POST /api/v1/drives/<job_id>/apply` (student only)
- `GET /api/v1/applications`
- `PATCH /api/v1/applications/<application_id>/status` (company only)
- `GET /api/v1/stats/placements` (admin only)

Access rules:
- Student: own profile/applications + approved active drives
- Company: own drives + applications on own drives
- Admin: full system-level visibility

## Validation

- Frontend: HTML5 form constraints (`required`, `pattern`, `maxlength`, etc.) and lightweight JS where needed.
- Backend: Flask-WTF + route-level validation and role checks before DB writes.

## Analytics

- Dashboards include Python (Matplotlib) visualizations (no charting JS library):
  - Admin: placement status, application status, monthly placement trend
  - Company: drive status, applicant progress

## Pincode Autofill APIs

The registration forms auto-fill `city`, `state`, and `country` on pincode blur using:

- `https://api.postalpincode.in/pincode/<pincode>`

## Framework Compliance

- Back-end: Flask
- Front-end: Jinja2 templates, HTML, CSS, Bootstrap
- Database: SQLite only
- Core requirements (authentication, registration, approvals, applications) are handled on Flask routes and SQLite models
