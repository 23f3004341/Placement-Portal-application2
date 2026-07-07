import os
from datetime import date

from flask import Flask, jsonify
try:
    from celery import Celery, Task
    from celery.schedules import crontab
except ImportError:
    Celery = None
    Task = object

    def crontab(*args, **kwargs):
        return None
    
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "info"


@login_manager.unauthorized_handler
def unauthorized_api_request():
    return jsonify({"ok": False, "message": "Authentication required."}), 401


class _MissingCeleryTask:
    def __init__(self, func):
        self.func = func
        self.__name__ = getattr(func, "__name__", "missing_celery_task")

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def delay(self, *args, **kwargs):
        raise RuntimeError("Celery is not installed. Run: pip install -r requirements.txt")


class _MissingCeleryApp:
    def __init__(self):
        self.conf = {}
        self.Task = Task

    def task(self, *args, **kwargs):
        del args, kwargs

        def decorator(func):
            return _MissingCeleryTask(func)

        return decorator

    def set_default(self):
        return None


celery_app = Celery(__name__) if Celery else _MissingCeleryApp()

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(BACKEND_DIR, "templates")


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    del connection_record
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


@login_manager.user_loader
def load_user(user_id):
    try:
        from .models import User
    except Exception:
        return None
    return User.query.get(int(user_id))


def create_default_admin():
    """
    Create one default admin user if no admin account exists.
    Uses env vars so credentials are not hardcoded in source.
    """
    try:
        from .models import AdminProfile, User

        admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@placementportal.com")
        admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
        admin_user = User.query.filter_by(user_role="admin").first()
        if not admin_user:
            admin_user = User.query.filter_by(email_address=admin_email).first()

        if not admin_user:
            admin_user = User(
                user_name=os.environ.get("DEFAULT_ADMIN_NAME", "Admin"),
                email_address=admin_email,
                gender=os.environ.get("DEFAULT_ADMIN_GENDER", "Not Specified"),
                dob=date(2000, 1, 1),
                contact_number=os.environ.get("DEFAULT_ADMIN_PHONE", "9999999999"),
                address=os.environ.get("DEFAULT_ADMIN_ADDRESS", "Placement Cell Office"),
                user_role="admin",
                is_approved=True,
                is_active=True,
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.flush()

        existing_admin = AdminProfile.query.filter_by(user_id=admin_user.user_id).first()
        if existing_admin:
            db.session.commit()
            return

        admin_profile = AdminProfile(
            user_id=admin_user.user_id,
            employee_code=os.environ.get("DEFAULT_ADMIN_EMPLOYEE_CODE", "ADMIN001"),
            office_name=os.environ.get("DEFAULT_ADMIN_OFFICE_NAME", "Placement Cell"),
        )
        db.session.add(admin_profile)
        db.session.commit()
        print(f"Default admin created: {admin_email}")

    except (ImportError, AttributeError):
        pass
    except OperationalError:
        pass
    except Exception as exc:
        print(f"Skipping default admin creation due to: {exc}")


def _ensure_runtime_schema_updates():
    try:
        additions = {
            "job_positions": {
                "eligible_degrees": "TEXT",
                "salary_unit": "TEXT DEFAULT 'lpa'",
                "eligible_years": "TEXT",
                "skills_required": "TEXT",
                "experience_required": "VARCHAR(255)",
                "benefits": "TEXT",
            },
            "student_profiles": {"experience": "TEXT"},
            "applications": {
                "company_feedback": "TEXT",
                "status_updated_at": "DATETIME",
            },
            "placements": {"offer_notes": "TEXT"},
            "interviews": {
                "feedback": "TEXT",
                "result": "VARCHAR(20)",
            },
            "notifications": {"source_key": "VARCHAR(120)"},
        }
        for table_name, table_additions in additions.items():
            columns = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            column_names = {row[1] for row in columns}
            for column_name, column_type in table_additions.items():
                if column_name not in column_names:
                    db.session.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                    )
        db.session.execute(
            text("UPDATE applications SET status_updated_at = applied_at WHERE status_updated_at IS NULL")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


def configure_celery(app):
    if Celery is None:
        app.extensions["celery"] = celery_app
        return celery_app

    celery_app.conf.update(app.config["CELERY"])

    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = FlaskTask
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app(test_config=None):
    app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-env")
    db_filename = os.environ.get("SQLITE_DB_NAME", "placement_portal.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, db_filename)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["RESUME_MAX_MB"] = int(os.environ.get("RESUME_MAX_MB", "2"))
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    app.config["REDIS_URL"] = redis_url
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300"))
    app.config["CACHE_SEARCH_TIMEOUT"] = int(os.environ.get("CACHE_SEARCH_TIMEOUT", "180"))
    app.config["EXPORT_DIR"] = os.environ.get(
        "EXPORT_DIR", os.path.join(STATIC_DIR, "exports")
    )
    app.config["ADMIN_EMAIL"] = os.environ.get("ADMIN_EMAIL", os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@placementportal.com"))
    app.config["MAIL_SENDER"] = os.environ.get("MAIL_SENDER", "no-reply@placementportal.local")
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "localhost")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "25"))
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
    app.config["CHAT_WEBHOOK_URL"] = os.environ.get("CHAT_WEBHOOK_URL")
    app.config["SMS_WEBHOOK_URL"] = os.environ.get("SMS_WEBHOOK_URL")
    app.config["REMINDER_LOOKAHEAD_DAYS"] = int(os.environ.get("REMINDER_LOOKAHEAD_DAYS", "3"))
    app.config["INTERVIEW_REMINDER_HOURS"] = int(os.environ.get("INTERVIEW_REMINDER_HOURS", "24"))
    app.config["DAILY_REMINDER_HOUR"] = int(os.environ.get("DAILY_REMINDER_HOUR", "9"))
    app.config["DAILY_REMINDER_MINUTE"] = int(os.environ.get("DAILY_REMINDER_MINUTE", "0"))
    app.config["CELERY"] = {
        "broker_url": os.environ.get("CELERY_BROKER_URL", redis_url),
        "result_backend": os.environ.get("CELERY_RESULT_BACKEND", redis_url),
        "broker_connection_retry_on_startup": True,
        "timezone": os.environ.get("CELERY_TIMEZONE", "Asia/Kolkata"),
        "beat_schedule": {
            "hourly-interview-reminders": {
                "task": "tasks.send_interview_reminders",
                "schedule": crontab(minute=0),
            },
            "daily-application-deadline-reminders": {
                "task": "tasks.send_daily_deadline_reminders",
                "schedule": crontab(
                    hour=app.config["DAILY_REMINDER_HOUR"],
                    minute=app.config["DAILY_REMINDER_MINUTE"],
                ),
            },
            "monthly-company-activity-reports": {
                "task": "tasks.send_monthly_activity_report",
                "schedule": crontab(day_of_month=1, hour=8, minute=0),
            },
        },
    }
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    configure_celery(app)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        try:
            from . import models, tasks
            db.create_all()
            _ensure_runtime_schema_updates()
            create_default_admin()
        except Exception as exc:
            print(f"Database bootstrap skipped: {exc}")

    return app
