import json
import ssl
from datetime import date
from urllib import request as urlrequest
from urllib.error import URLError

from flask import current_app

from ..celery_app import celery_app
from ..models import Application, CompanyProfile, JobPosition, StudentProfile, User


def send_chat_webhook(text):
    webhook = current_app.config.get("CHAT_WEBHOOK_URL")
    if not webhook:
        return False, "chat webhook not configured"
    request = urlrequest.Request(
        webhook,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    context = None if current_app.config.get("WEBHOOK_VERIFY_SSL") else ssl._create_unverified_context()
    try:
        with urlrequest.urlopen(request, timeout=15, context=context) as response:
            return response.status < 400, f"webhook returned {response.status}"
    except (OSError, URLError) as exc:
        return False, str(exc)


@celery_app.task(name="tasks.send_daily_deadline_reminders")
def send_daily_deadline_reminders():
    today = date.today()
    drives = (
        JobPosition.query.join(CompanyProfile)
        .filter(
            JobPosition.status == "approved",
            JobPosition.is_active.is_(True),
            JobPosition.application_deadline >= today,
        )
        .order_by(JobPosition.application_deadline, JobPosition.job_id)
        .all()
    )
    if not drives:
        return {"drives": 0, "students_notified": 0, "chat_sent": 0}

    students = StudentProfile.query.join(User).filter(User.is_active.is_(True), User.is_approved.is_(True)).all()
    lines = [
        (
            f"- {drive.company.company_name}: {drive.title}\n"
            f"  REMINDER: Application closes soon. Last date to apply: {drive.application_deadline:%d-%m-%Y}"
        )
        for drive in drives
    ]
    message_text = (
        f"{current_app.config.get('UNIVERSITY_NAME', 'Northbridge University')}\n"
        "Deadline Reminder for Students\n\n"
        + "\n".join(lines)
        + "\n\nPlease apply through the Placement Portal before the stated deadline. "
          "You may ignore a position if you have already applied or accepted a placement."
    )
    ok, message = send_chat_webhook(message_text)
    notified = len(students)
    chat_sent = int(ok)

    result = {"drives": len(drives), "students_notified": notified, "chat_sent": chat_sent}
    if not ok:
        result["chat_error"] = message
    return result
