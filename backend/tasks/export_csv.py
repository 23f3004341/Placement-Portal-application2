import csv
import json
import os
import ssl
from datetime import datetime
from urllib import request as urlrequest
from urllib.error import URLError

from flask import current_app, render_template
from flask_mail import Message

from ..celery_app import celery_app
from ..extensions import db, mail
from ..models import Application, ExportJob, Notification


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


def add_export_alert(export):
    source_key = f"student-export:{export.export_id}:completed"
    if not Notification.query.filter_by(user_id=export.student.user_id, source_key=source_key).first():
        db.session.add(Notification(
            user_id=export.student.user_id,
            title="Export ready",
            message="Your placement application CSV export is ready to download.",
            category="export",
            link_url="#dashboard",
            source_key=source_key,
        ))


@celery_app.task(name="tasks.export_student_applications_csv")
def export_student_applications_csv(export_id):
    export = ExportJob.query.get(export_id)
    if not export:
        return {"error": "export job not found"}
    export.status = "running"
    export.message = "Preparing CSV export."
    db.session.commit()

    try:
        os.makedirs(current_app.config["EXPORT_DIR"], exist_ok=True)
        student_identifier = export.student.roll_number if export.student else f"student-{export.student_id}"
        filename = f"{student_identifier}_applications_{datetime.utcnow():%Y%m%d%H%M%S}.csv"
        file_path = os.path.join(current_app.config["EXPORT_DIR"], filename)
        applications = Application.query.filter_by(student_id=export.student_id).order_by(Application.applied_at, Application.application_id).all()

        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date", "Deadline Date", "Updated At"])
            for application in applications:
                drive = application.job_position
                writer.writerow([
                    student_identifier,
                    drive.company.company_name,
                    drive.title,
                    application.status,
                    application.applied_at.strftime("%Y-%m-%d %H:%M:%S"),
                    drive.application_deadline.strftime("%Y-%m-%d") if drive.application_deadline else "",
                    application.status_updated_at.strftime("%Y-%m-%d %H:%M:%S") if application.status_updated_at else "",
                ])

        export.status = "completed"
        export.file_path = f"exports/{filename}"
        export.message = "CSV export is ready."
        export.completed_at = datetime.utcnow()
        add_export_alert(export)
        db.session.commit()
        return {"export_id": export_id, "status": "completed", "file_path": export.file_path}
    except Exception as exc:
        db.session.rollback()
        export = ExportJob.query.get(export_id)
        if export:
            export.status = "failed"
            export.message = str(exc)[:255]
            export.completed_at = datetime.utcnow()
            db.session.commit()
        raise
