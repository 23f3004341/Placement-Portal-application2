import os
from datetime import date

from flask import Flask
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

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    del connection_record
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


@login_manager.user_loader
def load_user(user_id):
    try:
        from models import User
    except Exception:
        return None
    return User.query.get(int(user_id))


def create_default_admin():
    """
    Create one default admin user if no admin account exists.
    Uses env vars so credentials are not hardcoded in source.
    """
    try:
        from models import AdminProfile, User

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
        columns = db.session.execute(text("PRAGMA table_info(job_positions)")).fetchall()
        column_names = {row[1] for row in columns}
        if "eligible_degrees" not in column_names:
            db.session.execute(text("ALTER TABLE job_positions ADD COLUMN eligible_degrees TEXT"))
        if "salary_unit" not in column_names:
            db.session.execute(text("ALTER TABLE job_positions ADD COLUMN salary_unit TEXT DEFAULT 'lpa'"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def create_app():
    app = Flask(__name__, template_folder="templates")

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-env")
    db_filename = os.environ.get("SQLITE_DB_NAME", "placement_portal.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, db_filename)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["RESUME_MAX_MB"] = int(os.environ.get("RESUME_MAX_MB", "2"))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        try:
            import models
            db.create_all()
            _ensure_runtime_schema_updates()
            create_default_admin()
        except Exception as exc:
            print(f"Database bootstrap skipped: {exc}")

    return app
