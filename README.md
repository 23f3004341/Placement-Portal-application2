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

## Pincode Autofill APIs

The registration forms auto-fill `city`, `state`, and `country` on pincode blur using:

- `https://api.postalpincode.in/pincode/<pincode>`

## Framework Compliance

- Back-end: Flask
- Front-end: Jinja2 templates, HTML, CSS, Bootstrap
- Database: SQLite only
- Core requirements (authentication, registration, approvals, applications) are handled on Flask routes and SQLite models
