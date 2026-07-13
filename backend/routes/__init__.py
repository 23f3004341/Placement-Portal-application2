import io
import html
import json
import os
import re
import ssl
from collections import Counter
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib import parse as urlparse
from urllib import request as urlrequest
from urllib.error import URLError

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from ..extensions import cache, db, mail
from ..config import FRONTEND_DIR
from ..models import (
    AccountRestriction,
    Application,
    CompanyProfile,
    ExportJob,
    Interview,
    JobPosition,
    Notification,
    Placement,
    Role,
    StudentProfile,
    User,
)
from ..tasks import (
    export_student_applications_csv,
    send_daily_deadline_reminders,
    send_monthly_activity_report,
)


main = Blueprint("main", __name__)
VALID_APPLICATION_STATUSES = {"applied", "shortlisted", "interview", "offer", "rejected", "placed", "withdrawn"}
SKILL_TERMS = {
    "python", "java", "javascript", "typescript", "sql", "flask", "django", "react", "vue",
    "angular", "node", "aws", "azure", "docker", "kubernetes", "redis", "git", "linux",
    "excel", "tableau", "powerbi", "communication", "leadership", "analytics", "machine learning",
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
    cache.delete("admin_dashboard")
    cache.delete("admin_reports")
    cache.delete("student_drives")


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


def reject_same_company_applications_after_placement(application):
    siblings = Application.query.join(JobPosition).filter(
        Application.student_id == application.student_id,
        Application.application_id != application.application_id,
        JobPosition.company_id == application.job_position.company_id,
        Application.status.notin_(("withdrawn", "rejected")),
    ).all()
    changed = False
    for sibling in siblings:
        sibling.status = "rejected"
        sibling.company_feedback = "Already placed at a different role"
        sibling.status_updated_at = datetime.utcnow()
        if sibling.placement:
            db.session.delete(sibling.placement)
        changed = True
    return changed


def ensure_placement_for_placed_application(application):
    if application.status != "placed" or application.placement:
        return False
    db.session.add(Placement(
        application=application,
        student_id=application.student_id,
        company_id=application.job_position.company_id,
        job_id=application.job_id,
        offered_package_lpa=application.job_position.salary_lpa,
        offer_date=date.today(),
        placement_status="placed",
    ))
    return True


def send_chat_message(text):
    webhook = current_app.config.get("CHAT_WEBHOOK_URL")
    if not webhook:
        return False, "chat webhook not configured"
    request_data = json.dumps({"text": text}).encode("utf-8")
    request_obj = urlrequest.Request(
        webhook,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    context = None if current_app.config.get("WEBHOOK_VERIFY_SSL") else ssl._create_unverified_context()
    try:
        with urlrequest.urlopen(request_obj, timeout=15, context=context) as response:
            return response.status < 400, f"webhook returned {response.status}"
    except ssl.SSLCertVerificationError:
        return False, "SSL certificate verification failed. For local demo runs, restart Flask with WEBHOOK_VERIFY_SSL=false."
    except (OSError, URLError) as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            return False, "SSL certificate verification failed. For local demo runs, restart Flask with WEBHOOK_VERIFY_SSL=false."
        return False, str(exc)


def send_student_email(student, subject, body):
    if not student or not student.user.email_address:
        return False, "missing student email"
    try:
        mail.send(Message(
            subject=subject,
            recipients=[student.user.email_address],
            body=body,
            html=f"<p>{html.escape(body).replace(chr(10), '<br>')}</p>",
        ))
        return True, "sent"
    except Exception as exc:
        return False, str(exc)


def mailhog_url():
    return current_app.config.get("MAILHOG_URL", "http://127.0.0.1:8025")


def recipient_for_user(user):
    if user.user_role == "company" and user.company_profile:
        return user.company_profile.hr_email or user.email_address
    return user.email_address


def load_mailhog_messages(recipient):
    query = urlparse.urlencode({"kind": "to", "query": recipient})
    api_url = f"{mailhog_url().rstrip('/')}/api/v2/search?{query}"
    try:
        with urlrequest.urlopen(api_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return []
    return payload.get("items", [])


def message_subject(message):
    headers = message.get("Content", {}).get("Headers", {})
    subject = headers.get("Subject") or ["(no subject)"]
    return subject[0] if isinstance(subject, list) else subject


def message_sender(message):
    headers = message.get("Content", {}).get("Headers", {})
    sender = headers.get("From") or message.get("From", {}).get("Mailbox") or ["unknown"]
    return sender[0] if isinstance(sender, list) else str(sender)


def render_filtered_inbox(user):
    recipient = recipient_for_user(user)
    rows = []
    for message in load_mailhog_messages(recipient):
        rows.append(
            "<tr>"
            f"<td>{html.escape(message_sender(message))}</td>"
            f"<td>{html.escape(message_subject(message))}</td>"
            f"<td>{html.escape(str(message.get('Created', '')))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or '<tr><td colspan="3">No MailHog email for this login yet.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MailHog inbox - {html.escape(recipient)}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-4">
  <div class="d-flex justify-content-between align-items-center mb-3">
    <div>
      <h1 class="h3 mb-1">MailHog inbox</h1>
      <p class="text-secondary mb-0">Showing mail addressed to {html.escape(recipient)}</p>
    </div>
    <a class="btn btn-outline-secondary" href="{html.escape(mailhog_url())}" target="_blank">Open full MailHog</a>
  </div>
  <table class="table table-bordered align-middle">
    <thead><tr><th>From</th><th>Subject</th><th>Created</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
</body>
</html>"""


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
        "gender": user.gender or "",
        "dob": user.dob.isoformat() if user.dob else "",
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
        "address_line1": student.user.address or "",
        "address_line2": "",
        "landmark": "",
        "pincode": "",
        "city": "",
        "state": "",
        "country": "India",
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
    placed_application = Application.query.join(JobPosition).filter(
            Application.student_id == application.student_id,
            JobPosition.company_id == application.job_position.company_id,
            Application.status.in_(("selected", "placed")),
        ).first()
    placed_record = Placement.query.filter(
        Placement.student_id == application.student_id,
        Placement.company_id == application.job_position.company_id,
        Placement.placement_status == "placed",
    ).first()
    student_placed = placed_application is not None or placed_record is not None
    placed_application_id = (
        placed_record.application_id
        if placed_record
        else placed_application.application_id if placed_application else None
    )
    already_placed_elsewhere = bool(
        student_placed and placed_application_id != application.application_id
    )
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
            "package_unit": placement.job_position.salary_unit or "lpa",
            "offer_date": placement.offer_date.isoformat() if placement.offer_date else None,
            "joining_date": placement.joining_date.isoformat() if placement.joining_date else None,
            "offer_notes": placement.offer_notes or "",
            "offer_letter_url": url_for(
                "main.student_offer_letter",
                placement_id=placement.placement_id,
                v=int(datetime.utcnow().timestamp()),
            ),
        },
        "student_placed": student_placed,
        "already_placed_elsewhere": already_placed_elsewhere,
    }



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


# Import route modules so their @main.route decorators register on the blueprint.
from . import admin, auth, company, cron, public, student, tasks_routes  # noqa: F401,E402

__all__ = ["main"]
