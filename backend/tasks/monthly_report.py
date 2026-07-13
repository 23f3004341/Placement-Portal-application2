import json
import ssl
from datetime import date, datetime, timedelta
from urllib import request as urlrequest
from urllib.error import URLError

from flask import current_app, render_template
from flask_mail import Message
from sqlalchemy import func

from ..celery_app import celery_app
from ..extensions import mail
from ..models import Application, JobPosition, Placement


def send_email(to_address, subject, html_body, text_body=None):
    if not to_address:
        return False, "missing recipient"
    try:
        mail.send(Message(subject=subject, recipients=[to_address], html=html_body, body=text_body))
        return True, "sent"
    except Exception as exc:
        return False, str(exc)


def send_chat_webhook(text):
    webhook = current_app.config.get("CHAT_WEBHOOK_URL")
    if not webhook:
        return False, "chat webhook not configured"
    request = urlrequest.Request(webhook, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    context = None if current_app.config.get("WEBHOOK_VERIFY_SSL") else ssl._create_unverified_context()
    try:
        with urlrequest.urlopen(request, timeout=15, context=context) as response:
            return response.status < 400, f"webhook returned {response.status}"
    except (OSError, URLError) as exc:
        return False, str(exc)


def _date_range_for_previous_month(today=None):
    today = today or date.today()
    first_this_month = today.replace(day=1)
    last_previous_month = first_this_month - timedelta(days=1)
    return last_previous_month.replace(day=1), first_this_month


def monthly_metrics(start_dt, end_dt):
    applications = Application.query.filter(Application.applied_at >= start_dt, Application.applied_at < end_dt)
    selected = Application.query.filter(
        Application.status.in_(("selected", "placed")),
        Application.status_updated_at >= start_dt,
        Application.status_updated_at < end_dt,
    )
    return {
        "drives_conducted": JobPosition.query.filter(JobPosition.created_at >= start_dt, JobPosition.created_at < end_dt).count(),
        "students_applied": applications.with_entities(func.count(func.distinct(Application.student_id))).scalar() or 0,
        "selected_count": selected.with_entities(func.count(func.distinct(Application.student_id))).scalar() or 0,
        "placements_created": Placement.query.filter(Placement.created_at >= start_dt, Placement.created_at < end_dt).count(),
        "status_counts": dict(applications.with_entities(Application.status, func.count(Application.application_id)).group_by(Application.status).all()),
    }


@celery_app.task(name="tasks.send_monthly_activity_report")
def send_monthly_activity_report():
    start_date, end_date = _date_range_for_previous_month()
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.min.time())
    metrics = monthly_metrics(start_dt, end_dt)
    label = start_date.strftime("%B %Y")
    html = render_template(
        "emails/monthly_activity_report.html",
        company=None,
        period_start=start_date,
        period_end=end_date - timedelta(days=1),
        generated_at=datetime.utcnow(),
        **metrics,
    )
    ok, message = send_email(
        current_app.config["ADMIN_EMAIL"],
        f"Institute monthly placement activity report - {label}",
        html,
        f"Monthly report: {metrics['drives_conducted']} drives, {metrics['students_applied']} students applied, {metrics['selected_count']} selected.",
    )
    return {"admin_sent": ok, "admin_message": message, "period": start_date.strftime("%Y-%m"), **metrics}
