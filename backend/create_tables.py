from sqlalchemy import text

from .extensions import db
from .seed_admin import create_default_admin


def ensure_runtime_schema_updates():
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
            "users": {"fs_uniquifier": "VARCHAR(255)"},
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
        db.session.execute(
            text("UPDATE users SET fs_uniquifier = lower(hex(randomblob(16))) WHERE fs_uniquifier IS NULL OR fs_uniquifier = ''")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


def create_tables(user_datastore=None):
    from . import models

    del models
    db.create_all()
    ensure_runtime_schema_updates()
    create_default_admin(user_datastore)


def main():
    from .app import create_app

    app = create_app()
    with app.app_context():
        create_tables()
    print("SQLite database schema created successfully.")


if __name__ == "__main__":
    main()
