import json
import smtplib
from email.message import EmailMessage
from urllib import request as urlrequest
from urllib.error import URLError

from flask import current_app


def send_email(to_address, subject, html_body, text_body=None, attachments=None):
    if not to_address:
        return False, "missing recipient"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["MAIL_SENDER"]
    message["To"] = to_address
    message.set_content(text_body or "Please view this message in an HTML-capable mail client.")
    message.add_alternative(html_body, subtype="html")
    for attachment in attachments or []:
        message.add_attachment(
            attachment["content"],
            maintype=attachment.get("maintype", "application"),
            subtype=attachment.get("subtype", "octet-stream"),
            filename=attachment["filename"],
        )

    try:
        with smtplib.SMTP(current_app.config["MAIL_SERVER"], current_app.config["MAIL_PORT"], timeout=15) as server:
            if current_app.config.get("MAIL_USE_TLS"):
                server.starttls()
            username = current_app.config.get("MAIL_USERNAME")
            password = current_app.config.get("MAIL_PASSWORD")
            if username and password:
                server.login(username, password)
            server.send_message(message)
    except OSError as exc:
        return False, str(exc)
    return True, "sent"


def send_chat_webhook(text):
    webhook_url = current_app.config.get("CHAT_WEBHOOK_URL")
    if not webhook_url:
        return False, "chat webhook not configured"

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urlrequest.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=15) as response:
            if response.status >= 400:
                return False, f"webhook returned {response.status}"
    except (OSError, URLError) as exc:
        return False, str(exc)
    return True, "sent"


def send_sms(phone_number, text):
    """Send SMS through a provider-neutral JSON webhook.

    Configure SMS_WEBHOOK_URL to an endpoint accepting
    {"to": "<phone>", "message": "<text>"}.
    """
    webhook_url = current_app.config.get("SMS_WEBHOOK_URL")
    if not webhook_url:
        return False, "SMS webhook not configured"
    if not phone_number:
        return False, "missing phone number"

    payload = json.dumps({"to": phone_number, "message": text}).encode("utf-8")
    req = urlrequest.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=15) as response:
            if response.status >= 400:
                return False, f"SMS webhook returned {response.status}"
    except (OSError, URLError) as exc:
        return False, str(exc)
    return True, "sent"
