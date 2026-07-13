"""Create the default admin account for local/demo runs."""

import os
import uuid
from datetime import date

from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash

from .extensions import db


def create_default_admin(user_datastore=None):
    try:
        from .models import AdminProfile, Role, User

        for role_name, description in (
            ("admin", "Placement cell administrator"),
            ("company", "Recruiter company account"),
            ("student", "Student account"),
        ):
            if user_datastore:
                user_datastore.find_or_create_role(name=role_name, description=description)
            elif not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name, description=description))
        db.session.commit()

        admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@placementportal.com")
        admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
        admin_user = User.query.filter_by(user_role="admin").first()
        if not admin_user:
            admin_user = User.query.filter_by(email_address=admin_email).first()

        if not admin_user:
            admin_user = User(
                user_name=os.environ.get("DEFAULT_ADMIN_NAME", "Admin"),
                email_address=admin_email,
                password_hash=generate_password_hash(admin_password),
                fs_uniquifier=uuid.uuid4().hex,
                gender=os.environ.get("DEFAULT_ADMIN_GENDER", "Not Specified"),
                dob=date(2000, 1, 1),
                contact_number=os.environ.get("DEFAULT_ADMIN_PHONE", "9999999999"),
                address=os.environ.get("DEFAULT_ADMIN_ADDRESS", "Placement Cell Office"),
                user_role="admin",
                is_approved=True,
                is_active=True,
            )
            db.session.add(admin_user)
            db.session.flush()
        elif not admin_user.fs_uniquifier:
            admin_user.fs_uniquifier = uuid.uuid4().hex

        admin_role = Role.query.filter_by(name="admin").first()
        if admin_role and admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)

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
