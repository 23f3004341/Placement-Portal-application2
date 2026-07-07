import io
import html
import json
import os
import re
from collections import Counter
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import URLError

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from ..cache_utils import cache_delete_pattern, cache_get, cache_set
from ..init import FRONTEND_DIR, db
from ..models import (
    AccountRestriction,
    Application,
    CompanyExportJob,
    CompanyProfile,
    ExportJob,
    Interview,
    JobPosition,
    Notification,
    Placement,
    StudentProfile,
    User,
)
from ..tasks import export_company_history_csv, export_student_applications_csv


main = Blueprint("main", __name__)
VALID_APPLICATION_STATUSES = {"applied", "shortlisted", "interview", "offer", "rejected", "placed", "withdrawn"}
SKILL_TERMS = {
    "python", "java", "javascript", "typescript", "sql", "flask", "django", "react", "vue",
    "angular", "node", "aws", "azure", "docker", "kubernetes", "redis", "git", "linux",
    "excel", "tableau", "powerbi", "communication", "leadership", "analytics", "machine learning",
}
ATS_STOP_WORDS = {
    "and", "the", "with", "for", "from", "that", "this", "you", "your", "are", "our", "will",
    "have", "has", "job", "role", "work", "team", "skills", "experience", "years", "candidate",
    "required", "preferred", "responsibilities", "qualification", "qualifications",
}


def api_error(message, status=400, errors=None):
    payload = {"ok": False, "message": message}
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status


def api_ok(data=None, message=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    if message:
        payload["message"] = message
    return jsonify(payload), status


@main.app_errorhandler(404)
def not_found_error(_error):
    return api_error("Resource not found.", 404)


@main.app_errorhandler(405)
def method_not_allowed_error(_error):
    return api_error("Method not allowed.", 405)


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.user_role not in roles:
                return api_error("You are not authorized for this action.", 403)
            if current_user.user_role == "company" and not current_user.is_approved:
                return api_error("Company approval is required.", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def invalidate_caches():
    for pattern in ("metrics:*", "listings:*", "search:*", "analytics:*"):
        cache_delete_pattern(pattern)


def parse_date(value, field_name, required=False):
    value = (value or "").strip()
    if not value:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid date.") from exc


def parse_datetime(value):
    try:
        return datetime.fromisoformat((value or "").strip())
    except ValueError as exc:
        raise ValueError("Interview date and time is invalid.") from exc


def split_values(value):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def compose_address(payload):
    locality = ", ".join(
        value for value in (
            (payload.get("city") or "").strip(),
            (payload.get("state") or "").strip(),
            (payload.get("country") or "").strip(),
        ) if value
    )
    pincode = (payload.get("pincode") or "").strip()
    if pincode:
        locality = f"{locality} - {pincode}" if locality else pincode
    return "\n".join(
        value for value in (
            (payload.get("address_line1") or "").strip(),
            (payload.get("address_line2") or "").strip(),
            (payload.get("landmark") or "").strip(),
            locality,
        ) if value
    )


def compose_person_name(payload, prefix=""):
    fields = [f"{prefix}first_name", f"{prefix}middle_name", f"{prefix}last_name"]
    parts = [(payload.get(field) or "").strip() for field in fields]
    full_name = " ".join(value for value in parts if value)
    if full_name:
        return full_name
    fallback_keys = [f"{prefix}name", "name"]
    for key in fallback_keys:
        if key in payload and (payload.get(key) or "").strip():
            return (payload.get(key) or "").strip()
    return ""


def save_resume(file, user_id):
    if not file or not file.filename:
        return None
    extension = Path(secure_filename(file.filename)).suffix.lower()
    if extension not in {".pdf", ".doc", ".docx"}:
        raise ValueError("Resume must be PDF, DOC, or DOCX.")
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    max_size = current_app.config.get("RESUME_MAX_MB", 2) * 1024 * 1024
    if size > max_size:
        raise ValueError(f"Resume must not exceed {current_app.config.get('RESUME_MAX_MB', 2)} MB.")
    folder = Path(current_app.static_folder) / "uploads" / "resumes"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"student_{user_id}_{datetime.utcnow():%Y%m%d%H%M%S}{extension}"
    file.save(folder / filename)
    return filename


def user_json(user):
    return {
        "id": user.user_id,
        "name": user.user_name,
        "email": user.email_address,
        "contact": user.contact_number or "",
        "address": user.address or "",
        "role": user.user_role,
        "approved": bool(user.is_approved),
        "active": bool(user.is_active),
    }


def company_json(company, include_user=True):
    data = {
        "id": company.company_id,
        "name": company.company_name,
        "industry": company.industry or "",
        "website": company.website or "",
        "headquarters": company.headquarters or "",
        "description": company.description or "",
        "hr_name": company.hr_name or "",
        "hr_email": company.hr_email or "",
        "hr_phone": company.hr_phone or "",
    }
    if include_user:
        data["user"] = user_json(company.user)
    return data


def student_json(student, include_user=True):
    data = {
        "id": student.student_id,
        "roll_number": student.roll_number,
        "course": student.course,
        "branch": student.branch,
        "graduation_year": student.graduation_year,
        "cgpa": student.cgpa,
        "skills": student.skills or "",
        "experience": student.experience or "",
        "resume_url": url_for("static", filename=f"uploads/resumes/{student.resume_filename}") if student.resume_filename else None,
    }
    if include_user:
        data["user"] = user_json(student.user)
    return data


def drive_json(drive, student=None):
    eligible = None
    reasons = []
    if student:
        if drive.min_cgpa is not None and (student.cgpa is None or student.cgpa < drive.min_cgpa):
            reasons.append("CGPA")
        degrees = {v.lower() for v in split_values(drive.eligible_degrees)}
        branches = {v.lower() for v in split_values(drive.eligible_branches)}
        years = {v for v in split_values(drive.eligible_years)}
        if degrees and student.course.lower() not in degrees:
            reasons.append("degree")
        if branches and student.branch.lower() not in branches:
            reasons.append("branch")
        if years and str(student.graduation_year) not in years:
            reasons.append("graduation year")
        eligible = not reasons
    return {
        "id": drive.job_id,
        "company_id": drive.company_id,
        "company": drive.company.company_name,
        "title": drive.title,
        "job_type": drive.job_type,
        "location": drive.location or "",
        "salary": drive.salary_lpa,
        "salary_unit": drive.salary_unit,
        "openings": drive.openings,
        "min_cgpa": drive.min_cgpa,
        "eligible_degrees": drive.eligible_degrees or "",
        "eligible_branches": drive.eligible_branches or "",
        "eligible_years": drive.eligible_years or "",
        "skills_required": drive.skills_required or "",
        "experience_required": drive.experience_required or "",
        "benefits": drive.benefits or "",
        "description": drive.description or "",
        "deadline": drive.application_deadline.isoformat() if drive.application_deadline else None,
        "status": drive.status,
        "active": bool(drive.is_active),
        "eligible": eligible,
        "eligibility_reasons": reasons,
    }


def interview_json(interview):
    return {
        "id": interview.interview_id,
        "scheduled_at": interview.scheduled_at.isoformat(timespec="minutes"),
        "mode": interview.mode,
        "location_or_link": interview.location_or_link or "",
        "notes": interview.notes or "",
        "feedback": interview.feedback or "",
        "result": interview.result or "",
        "status": interview.status,
    }


def application_json(application):
    placement = application.placement
    return {
        "id": application.application_id,
        "student": student_json(application.student),
        "drive": drive_json(application.job_position),
        "status": application.status,
        "applied_at": application.applied_at.isoformat(timespec="minutes"),
        "feedback": application.company_feedback or "",
        "cover_letter": application.cover_letter or "",
        "interviews": [interview_json(item) for item in sorted(application.interviews, key=lambda x: x.scheduled_at)],
        "placement": None if not placement else {
            "id": placement.placement_id,
            "status": placement.placement_status,
            "package": placement.offered_package_lpa,
            "offer_date": placement.offer_date.isoformat() if placement.offer_date else None,
            "joining_date": placement.joining_date.isoformat() if placement.joining_date else None,
            "offer_notes": placement.offer_notes or "",
            "offer_letter_url": url_for("main.student_offer_letter", placement_id=placement.placement_id),
        },
    }


def notification_json(notification):
    return {
        "id": notification.notification_id,
        "title": notification.title,
        "message": notification.message,
        "category": notification.category,
        "link_url": notification.link_url or "",
        "is_read": bool(notification.is_read),
        "created_at": notification.created_at.isoformat(timespec="minutes"),
    }


def add_notification(user_id, title, message, category="info", link_url=None, source_key=None):
    if source_key:
        existing = Notification.query.filter_by(user_id=user_id, source_key=source_key).first()
        if existing:
            return existing
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        link_url=link_url,
        source_key=source_key,
    )
    db.session.add(notification)
    return notification


def sync_current_user_notifications():
    if current_user.user_role == "student" and current_user.student_profile:
        applications = Application.query.filter_by(student_id=current_user.student_profile.student_id).all()
        for application in applications:
            for interview in application.interviews:
                add_notification(
                    current_user.user_id,
                    "Interview scheduled",
                    (
                        f"{application.job_position.company.company_name} scheduled an interview for "
                        f"{application.job_position.title} on {interview.scheduled_at:%Y-%m-%d at %H:%M}."
                    ),
                    "interview",
                    "#student-applications",
                    f"interview:{interview.interview_id}",
                )
            if application.placement:
                add_notification(
                    current_user.user_id,
                    "Offer received",
                    (
                        f"{application.job_position.company.company_name} has an offer or placement update "
                        f"for {application.job_position.title}."
                    ),
                    "success",
                    "#student-applications",
                    f"placement:{application.placement.placement_id}",
                )
    db.session.commit()


@main.get("/")
def api_root():
    return api_ok({
        "service": "Placement Portal API",
        "frontend": "Run the Vue CLI app from the frontend directory.",
        "docs": "/api/public/stats",
    })


@main.get("/service-worker.js")
def service_worker():
    response = send_from_directory(Path(FRONTEND_DIR) / "public", "service-worker.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@main.get("/api/auth/me")
def auth_me():
    return api_ok({"user": user_json(current_user) if current_user.is_authenticated else None})


@main.post("/api/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = (payload.get("role") or "").strip().lower()
    user = User.query.filter(func.lower(User.email_address) == email).first()
    if not user or not user.check_password(password) or user.user_role != role:
        return api_error("Invalid email, password, or role.", 401)
    restriction = AccountRestriction.query.filter(func.lower(AccountRestriction.email_address) == email).first()
    if restriction or not user.is_active:
        return api_error("This account is inactive or restricted.", 403)
    if role == "company" and not user.is_approved:
        return api_error("Company registration is awaiting admin approval.", 403)
    login_user(user)
    return api_ok({"user": user_json(user)}, "Login successful.")


@main.post("/api/auth/logout")
@login_required
def auth_logout():
    logout_user()
    return api_ok(message="Logged out.")


@main.get("/api/notifications")
@login_required
def notifications_index():
    sync_current_user_notifications()
    limit = min(int(request.args.get("limit", 20)), 50)
    rows = (
        Notification.query.filter_by(user_id=current_user.user_id)
        .order_by(Notification.created_at.desc(), Notification.notification_id.desc())
        .limit(limit)
        .all()
    )
    unread_count = Notification.query.filter_by(user_id=current_user.user_id, is_read=False).count()
    return api_ok({
        "items": [notification_json(item) for item in rows],
        "unread_count": unread_count,
    })


@main.patch("/api/notifications/<int:notification_id>/read")
@login_required
def notification_mark_read(notification_id):
    notification = Notification.query.filter_by(
        notification_id=notification_id,
        user_id=current_user.user_id,
    ).first_or_404()
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    return api_ok(notification_json(notification))


@main.patch("/api/notifications/read-all")
@login_required
def notifications_mark_all_read():
    Notification.query.filter_by(user_id=current_user.user_id, is_read=False).update({
        "is_read": True,
        "read_at": datetime.utcnow(),
    })
    db.session.commit()
    return api_ok(message="Notifications marked as read.")


def validate_registration(payload, company=False):
    errors = {}
    if company:
        if len((payload.get("company_name") or "").strip()) < 2:
            errors["company_name"] = "A valid company name is required."
        if not (payload.get("industry") or "").strip():
            errors["industry"] = "Industry is required."
        if not (payload.get("hr_first_name") or "").strip() and len((payload.get("hr_name") or "").strip()) < 2:
            errors["hr_first_name"] = "HR first name is required."
        if not (payload.get("hr_last_name") or "").strip() and len((payload.get("hr_name") or "").strip()) < 2:
            errors["hr_last_name"] = "HR last name is required."
        hr_email = (payload.get("hr_email") or "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", hr_email):
            errors["hr_email"] = "A valid HR email is required."
        hr_phone = str(payload.get("hr_phone") or "").strip()
        if hr_phone and not re.fullmatch(r"\d{10}", hr_phone):
            errors["hr_phone"] = "HR phone must contain exactly 10 digits."
    else:
        if not (payload.get("first_name") or "").strip() and len((payload.get("name") or "").strip()) < 2:
            errors["first_name"] = "First name is required."
        if not (payload.get("last_name") or "").strip() and len((payload.get("name") or "").strip()) < 2:
            errors["last_name"] = "Last name is required."
    email = (payload.get("email") or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors["email"] = "A valid email is required."
    if len(payload.get("password") or "") < 6:
        errors["password"] = "Password must contain at least 6 characters."
    if payload.get("confirm_password") is not None and payload.get("password") != payload.get("confirm_password"):
        errors["confirm_password"] = "Passwords do not match."
    if User.query.filter(func.lower(User.email_address) == email).first():
        errors["email"] = "This email is already registered."
    contact = str(payload.get("contact") or "").strip()
    if contact and not re.fullmatch(r"\d{10}", contact):
        errors["contact"] = "Contact number must contain exactly 10 digits."
    for field in ("address_line1", "pincode", "city", "state", "country"):
        if not (payload.get(field) or "").strip():
            errors[field] = f"{field.replace('_', ' ').title()} is required."
    if payload.get("pincode") and not re.fullmatch(r"\d{6}", str(payload.get("pincode")).strip()):
        errors["pincode"] = "Pincode must contain exactly 6 digits."
    return errors


@main.post("/api/auth/register/student")
def register_student():
    payload = request.form
    errors = validate_registration(payload)
    required = {
        "course": payload.get("course"),
        "branch": payload.get("branch"),
        "graduation_year": payload.get("graduation_year"),
        "contact": payload.get("contact"),
        "cgpa": payload.get("cgpa"),
        "skills": payload.get("skills"),
    }
    for key, value in required.items():
        if not value:
            errors[key] = f"{key.replace('_', ' ').title()} is required."
    if not request.files.get("resume") or not request.files["resume"].filename:
        errors["resume"] = "Resume is required."
    if errors:
        return api_error("Please correct the registration form.", 422, errors)
    try:
        year = int(payload.get("graduation_year"))
        cgpa = float(payload.get("cgpa")) if payload.get("cgpa") else None
        user = User(
            user_name=compose_person_name(payload),
            email_address=payload.get("email").strip().lower(),
            contact_number=(payload.get("contact") or "").strip(),
            address=compose_address(payload),
            gender=(payload.get("gender") or "").strip() or None,
            dob=parse_date(payload.get("dob"), "Date of birth"),
            user_role="student",
            is_active=True,
            is_approved=True,
        )
        user.set_password(payload.get("password"))
        db.session.add(user)
        db.session.flush()
        roll = (payload.get("roll_number") or f"STU{year}{user.user_id:04d}").strip().upper()
        student = StudentProfile(
            user_id=user.user_id,
            roll_number=roll,
            course=payload.get("course").strip(),
            branch=payload.get("branch").strip(),
            graduation_year=year,
            cgpa=cgpa,
            skills=(payload.get("skills") or "").strip(),
            experience=(payload.get("experience") or "").strip(),
        )
        db.session.add(student)
        db.session.flush()
        student.resume_filename = save_resume(request.files.get("resume"), user.user_id)
        db.session.commit()
        invalidate_caches()
        return api_ok(message="Student registration completed.", status=201)
    except (ValueError, IntegrityError) as exc:
        db.session.rollback()
        return api_error(str(exc) if isinstance(exc, ValueError) else "Registration data already exists.", 422)


@main.post("/api/auth/register/company")
def register_company():
    payload = request.get_json(silent=True) or {}
    errors = validate_registration(payload, company=True)
    if errors:
        return api_error("Please correct the registration form.", 422, errors)
    user = User(
        user_name=payload.get("company_name").strip(),
        email_address=payload.get("email").strip().lower(),
        contact_number=(payload.get("contact") or "").strip(),
        address=compose_address(payload),
        user_role="company",
        is_active=True,
        is_approved=False,
    )
    user.set_password(payload.get("password"))
    company = CompanyProfile(
        user=user,
        company_name=payload.get("company_name").strip(),
        industry=(payload.get("industry") or "").strip(),
        website=(payload.get("website") or "").strip(),
        headquarters=(payload.get("headquarters") or "").strip(),
        hr_name=compose_person_name(payload, "hr_"),
        hr_email=(payload.get("hr_email") or "").strip(),
        hr_phone=(payload.get("hr_phone") or "").strip(),
        description=(payload.get("description") or "").strip(),
    )
    try:
        db.session.add_all([user, company])
        db.session.commit()
        invalidate_caches()
        return api_ok(message="Company registered and awaiting admin approval.", status=201)
    except IntegrityError:
        db.session.rollback()
        return api_error("Company name or email already exists.", 409)


def public_analytics():
    cached = cache_get("analytics:public-api")
    if cached is not None:
        return cached
    trend_rows = db.session.query(
        func.strftime("%Y-%m", Placement.created_at), func.count(Placement.placement_id)
    ).group_by(func.strftime("%Y-%m", Placement.created_at)).order_by(func.strftime("%Y-%m", Placement.created_at)).all()[-12:]
    funnel_rows = db.session.query(Application.status, func.count(Application.application_id)).filter(
        Application.status != "withdrawn"
    ).group_by(Application.status).all()
    text = " ".join(f"{drive.title} {drive.skills_required or ''} {drive.description or ''}".lower() for drive in JobPosition.query.filter_by(status="approved").all())
    counts = Counter({skill: text.count(skill) for skill in SKILL_TERMS})
    skills = [(key, value) for key, value in counts.most_common(8) if value]
    data = {
        "totals": {
            "students": StudentProfile.query.count(),
            "companies": CompanyProfile.query.join(User).filter(User.is_approved.is_(True)).count(),
            "drives": JobPosition.query.filter_by(status="approved", is_active=True).count(),
            "placements": Placement.query.count(),
        },
        "trends": {"labels": [r[0] for r in trend_rows], "values": [r[1] for r in trend_rows]},
        "funnel": {"labels": [r[0].title() for r in funnel_rows], "values": [r[1] for r in funnel_rows]},
        "skills": {"labels": [r[0].title() for r in skills], "values": [r[1] for r in skills]},
    }
    cache_set("analytics:public-api", data, timeout=900)
    return data


@main.get("/api/public/stats")
def public_stats():
    return api_ok(public_analytics())


@main.get("/api/public/pincode/<pincode>")
def public_pincode_lookup(pincode):
    if not re.fullmatch(r"\d{6}", pincode):
        return api_error("Pincode must contain exactly 6 digits.", 422)
    cache_key = f"lookup:pincode:{pincode}"
    cached = cache_get(cache_key)
    if cached is not None:
        return api_ok(cached)
    try:
        with urlrequest.urlopen(f"https://api.postalpincode.in/pincode/{pincode}", timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return api_error("Pincode service is temporarily unavailable.", 502)
    if not payload or payload[0].get("Status") != "Success" or not payload[0].get("PostOffice"):
        return api_error("No city or state was found for this pincode.", 404)
    post_office = payload[0]["PostOffice"][0]
    result = {
        "city": post_office.get("District") or post_office.get("Name") or "",
        "state": post_office.get("State") or "",
        "country": post_office.get("Country") or "India",
    }
    cache_set(cache_key, result, timeout=86400)
    return api_ok(result)


@main.get("/api/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    return api_ok({
        "metrics": {
            "students": StudentProfile.query.count(),
            "companies": CompanyProfile.query.count(),
            "drives": JobPosition.query.count(),
            "applications": Application.query.count(),
        },
        "recent_applications": [application_json(a) for a in Application.query.order_by(Application.applied_at.desc()).limit(8).all()],
    })


@main.get("/api/admin/companies")
@role_required("admin")
def admin_companies():
    query_text = (request.args.get("q") or "").strip().lower()
    key = f"search:companies-api:{query_text}"
    cached = cache_get(key)
    if cached is None:
        query = CompanyProfile.query.join(User)
        if query_text:
            like = f"%{query_text}%"
            query = query.filter(or_(func.lower(CompanyProfile.company_name).like(like), func.lower(CompanyProfile.industry).like(like)))
        cached = [company_json(item) for item in query.order_by(CompanyProfile.company_id).all()]
        cache_set(key, cached, timeout=current_app.config.get("CACHE_SEARCH_TIMEOUT", 180))
    return api_ok(cached)


@main.patch("/api/admin/companies/<int:company_id>/status")
@role_required("admin")
def admin_company_status(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    action = ((request.get_json(silent=True) or {}).get("action") or "").lower()
    if action == "approve":
        company.user.is_approved, company.user.is_active = True, True
    elif action in {"reject", "blacklist", "deactivate"}:
        company.user.is_active = False
        if action == "reject":
            company.user.is_approved = False
        restriction = AccountRestriction.query.filter_by(email_address=company.user.email_address).first()
        if not restriction:
            db.session.add(AccountRestriction(email_address=company.user.email_address, reason="blacklisted"))
    elif action == "activate":
        company.user.is_active = True
        restriction = AccountRestriction.query.filter_by(email_address=company.user.email_address).first()
        if restriction:
            db.session.delete(restriction)
    else:
        return api_error("Invalid company action.")
    db.session.commit()
    invalidate_caches()
    return api_ok(company_json(company), "Company status updated.")


@main.delete("/api/admin/companies/<int:company_id>")
@role_required("admin")
def admin_delete_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    db.session.delete(company.user)
    db.session.commit()
    invalidate_caches()
    return api_ok(message="Company removed.")


@main.get("/api/admin/students")
@role_required("admin")
def admin_students():
    query_text = (request.args.get("q") or "").strip().lower()
    key = f"search:students-api:{query_text}"
    cached = cache_get(key)
    if cached is None:
        query = StudentProfile.query.join(User)
        if query_text:
            like = f"%{query_text}%"
            query = query.filter(or_(
                func.lower(User.user_name).like(like),
                func.lower(StudentProfile.roll_number).like(like),
                func.lower(User.contact_number).like(like),
            ))
        cached = [student_json(item) for item in query.order_by(StudentProfile.student_id).all()]
        cache_set(key, cached, timeout=current_app.config.get("CACHE_SEARCH_TIMEOUT", 180))
    return api_ok(cached)


@main.patch("/api/admin/students/<int:student_id>/status")
@role_required("admin")
def admin_student_status(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    action = ((request.get_json(silent=True) or {}).get("action") or "").lower()
    if action in {"blacklist", "deactivate"}:
        student.user.is_active = False
        if not AccountRestriction.query.filter_by(email_address=student.user.email_address).first():
            db.session.add(AccountRestriction(email_address=student.user.email_address, reason="blacklisted"))
    elif action == "activate":
        student.user.is_active = True
        restriction = AccountRestriction.query.filter_by(email_address=student.user.email_address).first()
        if restriction:
            db.session.delete(restriction)
    else:
        return api_error("Invalid student action.")
    db.session.commit()
    invalidate_caches()
    return api_ok(student_json(student), "Student status updated.")


@main.delete("/api/admin/students/<int:student_id>")
@role_required("admin")
def admin_delete_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    db.session.delete(student.user)
    db.session.commit()
    invalidate_caches()
    return api_ok(message="Student removed.")


@main.get("/api/admin/drives")
@role_required("admin")
def admin_drives():
    query_text = (request.args.get("q") or "").strip().lower()
    query = JobPosition.query.join(CompanyProfile)
    if query_text:
        like = f"%{query_text}%"
        query = query.filter(or_(func.lower(JobPosition.title).like(like), func.lower(CompanyProfile.company_name).like(like), func.lower(JobPosition.skills_required).like(like)))
    return api_ok([drive_json(item) for item in query.order_by(JobPosition.job_id.desc()).all()])


@main.patch("/api/admin/drives/<int:job_id>/status")
@role_required("admin")
def admin_drive_status(job_id):
    drive = JobPosition.query.get_or_404(job_id)
    action = ((request.get_json(silent=True) or {}).get("action") or "").lower()
    if action not in {"approve", "reject", "close", "activate"}:
        return api_error("Invalid drive action.")
    drive.status = {"approve": "approved", "reject": "rejected", "close": "closed", "activate": "approved"}[action]
    drive.is_active = action in {"approve", "activate"}
    db.session.commit()
    invalidate_caches()
    return api_ok(drive_json(drive), "Drive status updated.")


@main.delete("/api/admin/drives/<int:job_id>")
@role_required("admin")
def admin_delete_drive(job_id):
    drive = JobPosition.query.get_or_404(job_id)
    db.session.delete(drive)
    db.session.commit()
    invalidate_caches()
    return api_ok(message="Drive removed.")


@main.get("/api/admin/applications")
@role_required("admin")
def admin_applications():
    return api_ok([application_json(item) for item in Application.query.order_by(Application.application_id.desc()).all()])


@main.get("/api/company/dashboard")
@role_required("company")
def company_dashboard():
    company = current_user.company_profile
    drives = JobPosition.query.filter_by(company_id=company.company_id).order_by(JobPosition.job_id.desc()).all()
    applications = Application.query.join(JobPosition).filter(JobPosition.company_id == company.company_id, Application.status != "withdrawn").all()
    latest_export = CompanyExportJob.query.filter_by(company_id=company.company_id).order_by(CompanyExportJob.created_at.desc()).first()
    return api_ok({
        "company": company_json(company),
        "metrics": {
            "drives": len(drives),
            "active_drives": sum(1 for d in drives if d.is_active and d.status == "approved"),
            "applications": len(applications),
            "shortlisted": sum(1 for a in applications if a.status in {"shortlisted", "interview", "offer", "placed"}),
        },
        "drives": [drive_json(drive) for drive in drives],
        "latest_export": export_json(latest_export),
    })


@main.patch("/api/company/profile")
@role_required("company")
def company_profile_update():
    company = current_user.company_profile
    payload = request.get_json(silent=True) or {}
    company.company_name = (payload.get("name") or company.company_name).strip()
    for key in ("industry", "website", "headquarters", "description", "hr_name", "hr_email", "hr_phone"):
        if key in payload:
            setattr(company, key, (payload.get(key) or "").strip())
    current_user.user_name = company.company_name
    if "contact" in payload:
        current_user.contact_number = (payload.get("contact") or "").strip()
    db.session.commit()
    invalidate_caches()
    return api_ok(company_json(company), "Company profile updated.")


def apply_drive_payload(drive, payload):
    required = {"title": payload.get("title"), "description": payload.get("description"), "deadline": payload.get("deadline")}
    missing = [key for key, value in required.items() if not str(value or "").strip()]
    if missing:
        raise ValueError(f"Required fields: {', '.join(missing)}.")
    drive.title = payload.get("title").strip()
    drive.job_type = (payload.get("job_type") or "full-time").strip()
    drive.location = (payload.get("location") or "").strip()
    drive.salary_lpa = float(payload.get("salary")) if payload.get("salary") not in (None, "") else None
    drive.salary_unit = (payload.get("salary_unit") or "lpa").strip()
    drive.openings = int(payload.get("openings") or 1)
    drive.min_cgpa = float(payload.get("min_cgpa")) if payload.get("min_cgpa") not in (None, "") else None
    drive.eligible_degrees = (payload.get("eligible_degrees") or "").strip()
    drive.eligible_branches = (payload.get("eligible_branches") or "").strip()
    drive.eligible_years = (payload.get("eligible_years") or "").strip()
    drive.skills_required = (payload.get("skills_required") or "").strip()
    drive.experience_required = (payload.get("experience_required") or "").strip()
    drive.benefits = (payload.get("benefits") or "").strip()
    drive.description = payload.get("description").strip()
    drive.application_deadline = parse_date(payload.get("deadline"), "Application deadline", True)
    if drive.application_deadline < date.today():
        raise ValueError("Application deadline cannot be in the past.")


@main.post("/api/company/drives")
@role_required("company")
def company_create_drive():
    payload = request.get_json(silent=True) or {}
    drive = JobPosition(company_id=current_user.company_profile.company_id, status="pending", is_active=True)
    try:
        apply_drive_payload(drive, payload)
    except (ValueError, TypeError) as exc:
        return api_error(str(exc), 422)
    db.session.add(drive)
    db.session.commit()
    invalidate_caches()
    return api_ok(drive_json(drive), "Drive submitted for admin approval.", 201)


@main.patch("/api/company/drives/<int:job_id>")
@role_required("company")
def company_update_drive(job_id):
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=current_user.company_profile.company_id).first_or_404()
    try:
        apply_drive_payload(drive, request.get_json(silent=True) or {})
    except (ValueError, TypeError) as exc:
        return api_error(str(exc), 422)
    drive.status = "pending"
    db.session.commit()
    invalidate_caches()
    return api_ok(drive_json(drive), "Drive updated and resubmitted.")


@main.patch("/api/company/drives/<int:job_id>/close")
@role_required("company")
def company_close_drive(job_id):
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=current_user.company_profile.company_id).first_or_404()
    drive.status, drive.is_active = "closed", False
    db.session.commit()
    invalidate_caches()
    return api_ok(drive_json(drive), "Drive closed.")


@main.get("/api/company/applications")
@role_required("company")
def company_applications():
    query = Application.query.join(JobPosition).filter(
        JobPosition.company_id == current_user.company_profile.company_id,
        Application.status != "withdrawn",
    )
    job_id = request.args.get("job_id", type=int)
    if job_id:
        query = query.filter(Application.job_id == job_id)
    return api_ok([application_json(item) for item in query.order_by(Application.application_id.desc()).all()])


@main.patch("/api/company/applications/<int:application_id>")
@role_required("company")
def company_application_status(application_id):
    application = Application.query.join(JobPosition).filter(
        Application.application_id == application_id,
        JobPosition.company_id == current_user.company_profile.company_id,
    ).first_or_404()
    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") or "").lower()
    if status not in VALID_APPLICATION_STATUSES - {"applied", "withdrawn", "interview"}:
        return api_error("Invalid application status.")
    application.status = status
    application.company_feedback = (payload.get("feedback") or application.company_feedback or "").strip()
    application.status_updated_at = datetime.utcnow()
    placement = application.placement
    if status in {"offer", "placed"}:
        if not placement:
            placement = Placement(
                application=application,
                student_id=application.student_id,
                company_id=application.job_position.company_id,
                job_id=application.job_id,
                offered_package_lpa=application.job_position.salary_lpa,
                offer_date=date.today(),
            )
            db.session.add(placement)
        placement.placement_status = "placed" if status == "placed" else "offered"
        placement.offer_notes = (payload.get("offer_notes") or placement.offer_notes or "").strip()
        if payload.get("joining_date"):
            try:
                placement.joining_date = parse_date(payload.get("joining_date"), "Joining date")
            except ValueError as exc:
                return api_error(str(exc), 422)
    elif status == "rejected" and placement:
        db.session.delete(placement)
    title = "Application updated"
    message = f"{application.job_position.company.company_name} updated your {application.job_position.title} application to {status}."
    if status in {"offer", "placed"}:
        title = "Offer received" if status == "offer" else "Placement confirmed"
        message = f"{application.job_position.company.company_name} marked your {application.job_position.title} application as {status}."
    elif status == "rejected":
        title = "Application decision"
    add_notification(
        application.student.user_id,
        title,
        message,
        "success" if status in {"offer", "placed"} else "info",
        "#student-applications",
        f"application-status:{application.application_id}:{status}:{application.status_updated_at.isoformat()}",
    )
    db.session.commit()
    invalidate_caches()
    return api_ok(application_json(application), "Application updated.")


@main.post("/api/company/applications/<int:application_id>/interviews")
@role_required("company")
def company_schedule_interview(application_id):
    application = Application.query.join(JobPosition).filter(
        Application.application_id == application_id,
        JobPosition.company_id == current_user.company_profile.company_id,
    ).first_or_404()
    payload = request.get_json(silent=True) or {}
    try:
        scheduled_at = parse_datetime(payload.get("scheduled_at"))
    except ValueError as exc:
        return api_error(str(exc), 422)
    if scheduled_at <= datetime.now():
        return api_error("Interview must be scheduled in the future.", 422)
    interview = Interview(
        application=application,
        scheduled_at=scheduled_at,
        mode=(payload.get("mode") or "online").strip(),
        location_or_link=(payload.get("location_or_link") or "").strip(),
        notes=(payload.get("notes") or "").strip(),
    )
    application.status = "interview"
    application.status_updated_at = datetime.utcnow()
    db.session.add(interview)
    add_notification(
        application.student.user_id,
        "Interview scheduled",
        (
            f"{application.job_position.company.company_name} scheduled an interview for "
            f"{application.job_position.title} on {scheduled_at:%Y-%m-%d at %H:%M}."
        ),
        "interview",
        "#student-applications",
        f"interview:{interview.interview_id}",
    )
    db.session.commit()
    invalidate_caches()
    return api_ok(interview_json(interview), "Interview scheduled.", 201)


@main.patch("/api/company/interviews/<int:interview_id>")
@role_required("company")
def company_interview_result(interview_id):
    interview = Interview.query.join(Application).join(JobPosition).filter(
        Interview.interview_id == interview_id,
        JobPosition.company_id == current_user.company_profile.company_id,
    ).first_or_404()
    payload = request.get_json(silent=True) or {}
    interview.feedback = (payload.get("feedback") or "").strip()
    result = (payload.get("result") or "").lower()
    if result not in {"", "offer", "rejected"}:
        return api_error("Interview result must be offer or rejected.")
    interview.result = result or None
    interview.status = "completed" if result else interview.status
    if result:
        interview.application.status = result
        interview.application.company_feedback = interview.feedback
        interview.application.status_updated_at = datetime.utcnow()
        if result == "offer" and not interview.application.placement:
            db.session.add(Placement(
                application=interview.application,
                student_id=interview.application.student_id,
                company_id=interview.application.job_position.company_id,
                job_id=interview.application.job_id,
                offered_package_lpa=interview.application.job_position.salary_lpa,
                offer_date=date.today(),
                placement_status="offered",
            ))
        add_notification(
            interview.application.student.user_id,
            "Interview result updated",
            (
                f"{interview.application.job_position.company.company_name} marked your "
                f"{interview.application.job_position.title} interview result as {result}."
            ),
            "success" if result == "offer" else "info",
            "#student-applications",
            f"interview-result:{interview.interview_id}:{result}",
        )
    db.session.commit()
    invalidate_caches()
    return api_ok(interview_json(interview), "Interview feedback saved.")


def export_json(export):
    if not export:
        return None
    return {
        "id": export.export_id,
        "status": export.status,
        "message": export.message or "",
        "file_url": url_for("static", filename=export.file_path) if export.file_path else None,
        "created_at": export.created_at.isoformat(timespec="minutes"),
    }


def complete_stale_export(export, task_func, stale_after_seconds=15):
    if not export or export.status not in {"queued", "running"} or export.file_path:
        return export
    if export.created_at and datetime.utcnow() - export.created_at < timedelta(seconds=stale_after_seconds):
        return export
    try:
        task_func(export.export_id)
        db.session.refresh(export)
    except Exception:
        db.session.rollback()
        export = type(export).query.get(export.export_id)
    return export


@main.post("/api/company/export")
@role_required("company")
def company_export():
    export = CompanyExportJob(company_id=current_user.company_profile.company_id, status="queued", message="CSV export queued.")
    db.session.add(export)
    db.session.flush()
    add_notification(
        current_user.user_id,
        "Export queued",
        "Your company placement CSV export has been queued.",
        "export",
        "#dashboard",
        f"company-export:{export.export_id}:queued",
    )
    db.session.commit()
    try:
        task = export_company_history_csv.delay(export.export_id)
        db.session.refresh(export)
        export.task_id = task.id
        if export.status == "queued":
            export.status, export.message = "running", "CSV export is running."
        db.session.commit()
    except Exception as exc:
        export.status, export.message, export.completed_at = "failed", str(exc)[:255], datetime.utcnow()
        db.session.commit()
        return api_error(export.message, 503)
    return api_ok(export_json(export), "Export started.", 202)


@main.get("/api/company/export")
@role_required("company")
def company_export_status():
    export = CompanyExportJob.query.filter_by(company_id=current_user.company_profile.company_id).order_by(CompanyExportJob.created_at.desc()).first()
    export = complete_stale_export(export, export_company_history_csv)
    return api_ok(export_json(export))


@main.get("/api/student/dashboard")
@role_required("student")
def student_dashboard():
    student = current_user.student_profile
    applications = Application.query.filter_by(student_id=student.student_id).order_by(Application.application_id.desc()).all()
    latest_export = ExportJob.query.filter_by(student_id=student.student_id).order_by(ExportJob.created_at.desc()).first()
    return api_ok({
        "student": student_json(student),
        "metrics": {
            "approved_drives": JobPosition.query.filter_by(status="approved", is_active=True).count(),
            "applications": len(applications),
            "interviews": sum(len([i for i in a.interviews if i.status == "scheduled"]) for a in applications),
            "placements": sum(1 for a in applications if a.placement),
        },
        "latest_export": export_json(latest_export),
    })


@main.patch("/api/student/profile")
@role_required("student")
def student_profile_update():
    student = current_user.student_profile
    payload = request.form
    try:
        current_user.user_name = (payload.get("name") or current_user.user_name).strip()
        current_user.contact_number = (payload.get("contact") or current_user.contact_number or "").strip()
        current_user.address = (payload.get("address") or current_user.address or "").strip()
        student.course = (payload.get("course") or student.course).strip()
        student.branch = (payload.get("branch") or student.branch).strip()
        student.graduation_year = int(payload.get("graduation_year") or student.graduation_year)
        student.cgpa = float(payload.get("cgpa")) if payload.get("cgpa") else student.cgpa
        student.skills = (payload.get("skills") or "").strip()
        student.experience = (payload.get("experience") or "").strip()
        resume = save_resume(request.files.get("resume"), current_user.user_id)
        if resume:
            student.resume_filename = resume
        db.session.commit()
        invalidate_caches()
        return api_ok(student_json(student), "Profile updated.")
    except ValueError as exc:
        db.session.rollback()
        return api_error(str(exc), 422)


@main.get("/api/student/drives")
@role_required("student")
def student_drives():
    student = current_user.student_profile
    query_text = (request.args.get("q") or "").strip().lower()
    eligible_only = request.args.get("eligible") == "1"
    key = f"listings:student-api:{query_text}"
    ids = cache_get(key)
    if ids is None:
        query = JobPosition.query.join(CompanyProfile).filter(JobPosition.status == "approved", JobPosition.is_active.is_(True))
        if query_text:
            like = f"%{query_text}%"
            query = query.filter(or_(
                func.lower(JobPosition.title).like(like),
                func.lower(CompanyProfile.company_name).like(like),
                func.lower(JobPosition.skills_required).like(like),
            ))
        ids = [row.job_id for row in query.order_by(JobPosition.job_id.desc()).all()]
        cache_set(key, ids, timeout=current_app.config.get("CACHE_SEARCH_TIMEOUT", 180))
    rows = JobPosition.query.filter(JobPosition.job_id.in_(ids)).all() if ids else []
    mapping = {row.job_id: row for row in rows}
    drives = [drive_json(mapping[item_id], student) for item_id in ids if item_id in mapping]
    if eligible_only:
        drives = [item for item in drives if item["eligible"]]
    applications = {a.job_id: a.status for a in Application.query.filter_by(student_id=student.student_id).all()}
    for drive in drives:
        drive["application_status"] = applications.get(drive["id"])
    return api_ok(drives)


@main.post("/api/student/drives/<int:job_id>/apply")
@role_required("student")
def student_apply(job_id):
    student = current_user.student_profile
    drive = JobPosition.query.get_or_404(job_id)
    details = drive_json(drive, student)
    if drive.status != "approved" or not drive.is_active or (drive.application_deadline and drive.application_deadline < date.today()):
        return api_error("This drive is not open for applications.", 409)
    if not details["eligible"]:
        return api_error(f"Eligibility not met: {', '.join(details['eligibility_reasons'])}.", 422)
    existing = Application.query.filter_by(student_id=student.student_id, job_id=job_id).first()
    if existing:
        if existing.status == "withdrawn":
            existing.status, existing.applied_at = "applied", datetime.utcnow()
            existing.status_updated_at = datetime.utcnow()
            db.session.commit()
            invalidate_caches()
            return api_ok(application_json(existing), "Application restored.")
        return api_error("You have already applied to this drive.", 409)
    application = Application(
        student_id=student.student_id,
        job_id=job_id,
        cover_letter=((request.get_json(silent=True) or {}).get("cover_letter") or "").strip(),
        status="applied",
    )
    db.session.add(application)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error("You have already applied to this drive.", 409)
    invalidate_caches()
    return api_ok(application_json(application), "Application submitted.", 201)


@main.get("/api/student/applications")
@role_required("student")
def student_applications():
    rows = Application.query.filter_by(student_id=current_user.student_profile.student_id).order_by(Application.application_id.desc()).all()
    return api_ok([application_json(item) for item in rows])


@main.patch("/api/student/applications/<int:application_id>/withdraw")
@role_required("student")
def student_withdraw(application_id):
    application = Application.query.filter_by(application_id=application_id, student_id=current_user.student_profile.student_id).first_or_404()
    if application.status != "applied":
        return api_error("Only an unprocessed application can be withdrawn.", 409)
    application.status, application.status_updated_at = "withdrawn", datetime.utcnow()
    db.session.commit()
    invalidate_caches()
    return api_ok(application_json(application), "Application withdrawn.")


@main.post("/api/student/export")
@role_required("student")
def student_export():
    export = ExportJob(student_id=current_user.student_profile.student_id, status="queued", message="CSV export queued.")
    db.session.add(export)
    db.session.flush()
    add_notification(
        current_user.user_id,
        "Export queued",
        "Your application CSV export has been queued.",
        "export",
        "#dashboard",
        f"student-export:{export.export_id}:queued",
    )
    db.session.commit()
    try:
        task = export_student_applications_csv.delay(export.export_id)
        db.session.refresh(export)
        export.task_id = task.id
        if export.status == "queued":
            export.status, export.message = "running", "CSV export is running."
        db.session.commit()
    except Exception as exc:
        export.status, export.message, export.completed_at = "failed", str(exc)[:255], datetime.utcnow()
        db.session.commit()
        return api_error(export.message, 503)
    return api_ok(export_json(export), "Export started.", 202)


@main.get("/api/student/export")
@role_required("student")
def student_export_status():
    export = ExportJob.query.filter_by(student_id=current_user.student_profile.student_id).order_by(ExportJob.created_at.desc()).first()
    export = complete_stale_export(export, export_student_applications_csv)
    return api_ok(export_json(export))


def student_activity_report_data(student):
    applications = (
        Application.query.filter_by(student_id=student.student_id)
        .order_by(Application.applied_at.asc(), Application.application_id.asc())
        .all()
    )
    status_counts = Counter(application.status for application in applications)
    return {
        "student": student,
        "applications": applications,
        "status_counts": status_counts,
        "generated_at": datetime.utcnow(),
        "metrics": {
            "Applications": len(applications),
            "Interviews": sum(len(application.interviews) for application in applications),
            "Offers": sum(1 for application in applications if application.placement),
            "Placements": sum(1 for application in applications if application.placement and application.placement.placement_status == "placed"),
        },
    }


def student_activity_report_html(report):
    student = report["student"]
    rows = []
    for application in report["applications"]:
        drive = application.job_position
        placement = application.placement
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(student.student_id))}</td>"
            f"<td>{html.escape(drive.company.company_name)}</td>"
            f"<td>{html.escape(drive.title)}</td>"
            f"<td>{html.escape(application.status.title())}</td>"
            f"<td>{application.applied_at:%Y-%m-%d}</td>"
            f"<td>{drive.application_deadline.strftime('%Y-%m-%d') if drive.application_deadline else '-'}</td>"
            f"<td>{html.escape(placement.placement_status.title()) if placement else '-'}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan=\"7\">No applications yet.</td></tr>")

    metric_rows = "".join(
        f"<tr><th align=\"left\">{html.escape(label)}</th><td>{value}</td></tr>"
        for label, value in report["metrics"].items()
    )
    status_rows = "".join(
        f"<tr><th align=\"left\">{html.escape(status.title())}</th><td>{count}</td></tr>"
        for status, count in sorted(report["status_counts"].items())
    ) or "<tr><td colspan=\"2\">No status history yet.</td></tr>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Student Placement Activity Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #1f2937; margin: 32px; }}
    h1 {{ margin-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; font-size: 13px; }}
    th {{ background: #f3f4f6; }}
    .muted {{ color: #6b7280; }}
  </style>
</head>
<body>
  <h1>Student Placement Activity Report</h1>
  <p class="muted">Generated at {report["generated_at"]:%Y-%m-%d %H:%M UTC}</p>
  <p><strong>Student:</strong> {html.escape(student.user.user_name)}<br>
  <strong>Roll number:</strong> {html.escape(student.roll_number)}<br>
  <strong>Student ID:</strong> {student.student_id}</p>
  <h2>Summary</h2>
  <table>{metric_rows}</table>
  <h2>Status Breakdown</h2>
  <table>{status_rows}</table>
  <h2>Application History</h2>
  <table>
    <thead><tr><th>Student ID</th><th>Company</th><th>Drive</th><th>Status</th><th>Applied</th><th>Deadline</th><th>Placement</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>"""


def student_activity_report_pdf(report):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 48
    student = report["student"]
    pdf.setTitle("Student Placement Activity Report")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(48, y, "Student Placement Activity Report")
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(48, y, f"Generated: {report['generated_at']:%Y-%m-%d %H:%M UTC}")
    y -= 18
    pdf.drawString(48, y, f"Student: {student.user.user_name} ({student.roll_number})")
    y -= 18
    pdf.drawString(48, y, f"Student ID: {student.student_id}")
    y -= 28
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Summary")
    y -= 18
    pdf.setFont("Helvetica", 10)
    for label, value in report["metrics"].items():
        pdf.drawString(58, y, f"{label}: {value}")
        y -= 15
    y -= 10
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Application History")
    y -= 18
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(48, y, "Company")
    pdf.drawString(150, y, "Drive")
    pdf.drawString(290, y, "Status")
    pdf.drawString(365, y, "Applied")
    pdf.drawString(430, y, "Deadline")
    pdf.drawString(500, y, "Placement")
    y -= 12
    pdf.setFont("Helvetica", 8)
    for application in report["applications"]:
        if y < 60:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 8)
        drive = application.job_position
        placement = application.placement
        pdf.drawString(48, y, drive.company.company_name[:22])
        pdf.drawString(150, y, drive.title[:30])
        pdf.drawString(290, y, application.status.title()[:14])
        pdf.drawString(365, y, f"{application.applied_at:%Y-%m-%d}")
        pdf.drawString(430, y, drive.application_deadline.strftime("%Y-%m-%d") if drive.application_deadline else "-")
        pdf.drawString(500, y, placement.placement_status.title()[:12] if placement else "-")
        y -= 13
    if not report["applications"]:
        pdf.drawString(48, y, "No applications yet.")
    pdf.drawRightString(width - 48, 32, "Generated by Placement Portal")
    pdf.save()
    output.seek(0)
    return output


@main.get("/api/student/report")
@role_required("student")
def student_activity_report():
    report_format = (request.args.get("format") or "html").strip().lower()
    if report_format not in {"html", "pdf"}:
        return api_error("Report format must be html or pdf.", 422)
    report = student_activity_report_data(current_user.student_profile)
    filename = f"student-{current_user.student_profile.student_id}-placement-report"
    if report_format == "pdf":
        return send_file(
            student_activity_report_pdf(report),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{filename}.pdf",
        )
    response = make_response(student_activity_report_html(report))
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.html"
    return response


@main.get("/api/student/placements/<int:placement_id>/offer-letter")
@role_required("student")
def student_offer_letter(placement_id):
    placement = Placement.query.filter_by(placement_id=placement_id, student_id=current_user.student_profile.student_id).first_or_404()
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    pdf.setTitle("Placement Offer Letter")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(54, 780, "Placement Offer / Confirmation")
    pdf.setFont("Helvetica", 11)
    lines = [
        f"Date: {placement.offer_date:%B %d, %Y}",
        f"Student: {placement.student.user.user_name}",
        f"Roll number: {placement.student.roll_number}",
        f"Company: {placement.company.company_name}",
        f"Position: {placement.job_position.title}",
        f"Package: {placement.offered_package_lpa or '-'} {placement.job_position.salary_unit or 'LPA'}",
        f"Joining date: {placement.joining_date.isoformat() if placement.joining_date else 'To be confirmed'}",
        f"Status: {placement.placement_status.title()}",
        f"Notes: {placement.offer_notes or 'Please contact the company HR for onboarding details.'}",
    ]
    y = 735
    for line in lines:
        pdf.drawString(54, y, line)
        y -= 28
    pdf.drawString(54, 430, "This document was generated by the Institute Placement Portal.")
    pdf.save()
    output.seek(0)
    return send_file(output, mimetype="application/pdf", as_attachment=True, download_name=f"offer-letter-{placement.placement_id}.pdf")


def ats_terms(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,30}", text.lower())
    return {word for word in words if len(word) > 2 and word not in ATS_STOP_WORDS}


def build_ats_result(resume_text, job_text):
    resume_terms, job_terms = ats_terms(resume_text), ats_terms(job_text)
    matched, missing = sorted(resume_terms & job_terms), sorted(job_terms - resume_terms)
    score = round(len(matched) / len(job_terms) * 100) if job_terms else 0
    return {
        "score": score,
        "summary": "Strong match" if score >= 70 else "Promising match" if score >= 45 else "Needs tailoring",
        "matched": matched[:40],
        "missing": missing[:40],
    }


@main.post("/api/tools/ats")
@role_required("student", "company")
def ats_screen():
    payload = request.get_json(silent=True) or {}
    resume_text = (payload.get("resume_text") or "").strip()[:50000]
    job_text = (payload.get("job_description") or "").strip()[:30000]
    if not resume_text or not job_text:
        return api_error("Résumé text and job description are required.", 422)
    return api_ok(build_ats_result(resume_text, job_text))
