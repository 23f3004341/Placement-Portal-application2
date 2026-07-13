"""Application configuration in one place."""

import os
from datetime import timedelta

from celery.schedules import crontab

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(BACKEND_DIR, "templates")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-env")
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "change-this-security-salt")
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_SEND_PASSWORD_RESET_EMAIL = False
    SECURITY_CSRF_PROTECT_MECHANISMS = []
    WTF_CSRF_ENABLED = False

    db_filename = os.environ.get("SQLITE_DB_NAME", "placement_portal.db")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, db_filename),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RESUME_MAX_MB = int(os.environ.get("RESUME_MAX_MB", "2"))
    EXPORT_DIR = os.environ.get("EXPORT_DIR", os.path.join(STATIC_DIR, "exports"))

    REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL", REDIS_URL)
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "60"))

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "127.0.0.1")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "1025"))
    MAILHOG_URL = os.environ.get("MAILHOG_URL", "http://127.0.0.1:8025")
    MAIL_SENDER = os.environ.get("MAIL_SENDER", "no-reply@placementportal.local")
    MAIL_DEFAULT_SENDER = MAIL_SENDER
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"

    ADMIN_EMAIL = os.environ.get(
        "ADMIN_EMAIL",
        os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@placementportal.com"),
    )
    UNIVERSITY_NAME = os.environ.get("UNIVERSITY_NAME", "Northbridge University")
    CHAT_WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
    WEBHOOK_VERIFY_SSL = os.environ.get("WEBHOOK_VERIFY_SSL", "false").lower() == "true"

    # Deadline reminders run once every morning until the application deadline.
    DEADLINE_REMINDER_HOUR = int(os.environ.get("DEADLINE_REMINDER_HOUR", "9"))
    DEADLINE_REMINDER_MINUTE = int(os.environ.get("DEADLINE_REMINDER_MINUTE", "0"))
    # Keep the admin report frequent.
    ADMIN_REPORT_SECONDS = int(os.environ.get("ADMIN_REPORT_SECONDS", "120"))
    CELERY_TIMEZONE = os.environ.get("CELERY_TIMEZONE", "Asia/Kolkata")
    REMINDER_LOOKAHEAD_DAYS = int(os.environ.get("REMINDER_LOOKAHEAD_DAYS", "3"))

    CELERY = {
        "broker_url": os.environ.get("CELERY_BROKER_URL", REDIS_URL),
        "result_backend": os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL),
        "broker_connection_retry_on_startup": True,
        "timezone": CELERY_TIMEZONE,
    }

    CELERY_BEAT_SCHEDULE = {
        "deadline-reminders-daily-at-9-am": {
            "task": "tasks.send_daily_deadline_reminders",
            "schedule": crontab(minute=DEADLINE_REMINDER_MINUTE, hour=DEADLINE_REMINDER_HOUR),
        },
        "admin-activity-report-every-2-minutes": {
            "task": "tasks.send_monthly_activity_report",
            "schedule": timedelta(seconds=ADMIN_REPORT_SECONDS),
        },
    }
