import csv
import os
import tempfile
import unittest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import patch

from backend.app import create_app
from backend.extensions import db
from backend.models import Application, CompanyProfile, ExportJob, JobPosition, Notification, StudentProfile, User
from backend.tasks import send_daily_deadline_reminders, send_monthly_activity_report


class MilestoneSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            "TESTING": True,
            "CACHE_TYPE": "SimpleCache",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "CELERY": {
                "broker_url": "memory://",
                "result_backend": "cache+memory://",
                "task_always_eager": True,
                "beat_schedule": {},
            },
        })

    def setUp(self):
        self.client = self.app.test_client()

    def test_public_api_and_cdn_frontend(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"https://unpkg.com/vue@3.5.13", response.data)
        response.close()

        response = self.client.get("/api/public/stats")
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_protected_admin_task_sync_routes(self):
        response = self.client.post("/api/admin/tasks/daily-reminders", json={})
        self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/admin/tasks/monthly-report", json={})
        self.assertEqual(response.status_code, 401)

    def test_student_activity_report_downloads_html_and_pdf(self):
        with self.app.app_context():
            suffix = uuid4().hex
            password = "secret123"
            student_email = f"report-student-{suffix}@example.com"
            company_user = User(
                user_name="Report Company",
                email_address=f"report-company-{suffix}@example.com",
                user_role="company",
                is_approved=True,
                is_active=True,
            )
            company_user.set_password(password)
            student_user = User(
                user_name="Report Student",
                email_address=student_email,
                user_role="student",
                is_approved=True,
                is_active=True,
            )
            student_user.set_password(password)
            db.session.add_all([company_user, student_user])
            db.session.flush()
            company = CompanyProfile(
                user_id=company_user.user_id,
                company_name=f"Report Labs {suffix}",
                industry="Technology",
            )
            student = StudentProfile(
                user_id=student_user.user_id,
                roll_number=f"REP{suffix[:8]}",
                course="B.Tech",
                branch="CSE",
                graduation_year=2099,
                cgpa=8.5,
            )
            db.session.add_all([company, student])
            db.session.flush()
            drive = JobPosition(
                company_id=company.company_id,
                title="Report Engineer",
                job_type="full-time",
                description="Build reports.",
                application_deadline=date.today() + timedelta(days=10),
                status="approved",
                is_active=True,
            )
            db.session.add(drive)
            db.session.flush()
            db.session.add(Application(
                student_id=student.student_id,
                job_id=drive.job_id,
                status="shortlisted",
            ))
            db.session.commit()

        login = self.client.post("/api/auth/login", json={
            "email": student_email,
            "password": password,
            "role": "student",
        })
        self.assertEqual(login.status_code, 200)

        html_response = self.client.get("/api/student/report?format=html")
        self.assertEqual(html_response.status_code, 200)
        self.assertIn("text/html", html_response.headers["Content-Type"])
        self.assertIn("Student Placement Activity Report", html_response.get_data(as_text=True))
        self.assertIn("Report Engineer", html_response.get_data(as_text=True))

        pdf_response = self.client.get("/api/student/report?format=pdf")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response.headers["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.data.startswith(b"%PDF-"))

    def test_jobs_and_new_tables_are_registered(self):
        expected_tasks = {
            "tasks.send_daily_deadline_reminders",
            "tasks.send_monthly_activity_report",
            "tasks.export_student_applications_csv",
        }
        self.assertTrue(expected_tasks.issubset(self.app.extensions["celery"].tasks))
        with self.app.app_context():
            self.assertIn("export_jobs", db.metadata.tables)

    def test_daily_deadline_reminder_uses_all_channels(self):
        with self.app.app_context():
            suffix = uuid4().hex
            student_email = f"reminder-student-{suffix}@example.com"
            company_user = User(
                user_name="Reminder Company",
                email_address=f"reminder-company-{suffix}@example.com",
                user_role="company",
                is_approved=True,
                is_active=True,
            )
            company_user.set_password("secret123")
            student_user = User(
                user_name="Reminder Student",
                email_address=student_email,
                user_role="student",
                is_approved=True,
                is_active=True,
            )
            student_user.set_password("secret123")
            db.session.add_all([company_user, student_user])
            db.session.flush()
            company = CompanyProfile(
                user_id=company_user.user_id,
                company_name=f"Reminder Labs {suffix}",
                industry="Technology",
            )
            student = StudentProfile(
                user_id=student_user.user_id,
                roll_number=f"REM{suffix[:8]}",
                course="B.Tech",
                branch="CSE",
                graduation_year=2099,
                cgpa=8.5,
            )
            db.session.add_all([company, student])
            db.session.flush()
            db.session.add(JobPosition(
                company_id=company.company_id,
                title="Deadline Engineer",
                job_type="full-time",
                description="Build reminder systems.",
                application_deadline=date.today() + timedelta(days=1),
                status="approved",
                is_active=True,
            ))
            db.session.commit()

            with patch("backend.tasks.reminders.send_chat_webhook", return_value=(True, "sent")) as chat:
                result = send_daily_deadline_reminders()

            self.assertGreaterEqual(result["students_notified"], 1)
            self.assertGreaterEqual(result["chat_sent"], 1)
            self.assertTrue(any("Deadline Reminder for Students" in call.args[0] for call in chat.call_args_list))

    def test_monthly_activity_report_emails_admin_html_summary(self):
        with self.app.app_context():
            suffix = uuid4().hex
            admin_email = f"admin-report-{suffix}@example.com"
            latest_drive = JobPosition.query.order_by(JobPosition.created_at.desc()).first()
            latest_year = latest_drive.created_at.year if latest_drive else 2097
            report_year = max(latest_year + 1, 2098)
            period_start = date(report_year, 6, 1)
            period_end = date(report_year, 7, 1)
            created_at = date(report_year, 6, 12)
            company_user = User(
                user_name="Monthly Report Company",
                email_address=f"monthly-company-{suffix}@example.com",
                user_role="company",
                is_approved=True,
                is_active=True,
            )
            company_user.set_password("secret123")
            first_student_user = User(
                user_name="Monthly Applicant",
                email_address=f"monthly-student-a-{suffix}@example.com",
                user_role="student",
                is_approved=True,
                is_active=True,
            )
            first_student_user.set_password("secret123")
            second_student_user = User(
                user_name="Monthly Selected",
                email_address=f"monthly-student-b-{suffix}@example.com",
                user_role="student",
                is_approved=True,
                is_active=True,
            )
            second_student_user.set_password("secret123")
            db.session.add_all([company_user, first_student_user, second_student_user])
            db.session.flush()
            company = CompanyProfile(
                user_id=company_user.user_id,
                company_name=f"Monthly Labs {suffix}",
                industry="Technology",
            )
            first_student = StudentProfile(
                user_id=first_student_user.user_id,
                roll_number=f"MONA{suffix[:8]}",
                course="B.Tech",
                branch="CSE",
                graduation_year=2099,
                cgpa=8.5,
            )
            second_student = StudentProfile(
                user_id=second_student_user.user_id,
                roll_number=f"MONB{suffix[:8]}",
                course="B.Tech",
                branch="CSE",
                graduation_year=2099,
                cgpa=8.7,
            )
            db.session.add_all([company, first_student, second_student])
            db.session.flush()
            drive = JobPosition(
                company_id=company.company_id,
                title="Monthly Engineer",
                job_type="full-time",
                description="Build monthly reports.",
                application_deadline=date(report_year, 6, 25),
                status="approved",
                is_active=True,
                created_at=created_at,
            )
            db.session.add(drive)
            db.session.flush()
            db.session.add_all([
                Application(
                    student_id=first_student.student_id,
                    job_id=drive.job_id,
                    applied_at=date(report_year, 6, 13),
                    status="applied",
                    status_updated_at=date(report_year, 6, 13),
                ),
                Application(
                    student_id=second_student.student_id,
                    job_id=drive.job_id,
                    applied_at=date(report_year, 5, 28),
                    status="selected",
                    status_updated_at=date(report_year, 6, 18),
                ),
            ])
            db.session.commit()

            previous_admin_email = self.app.config["ADMIN_EMAIL"]
            self.app.config["ADMIN_EMAIL"] = admin_email
            try:
                with patch("backend.tasks.monthly_report._date_range_for_previous_month", return_value=(period_start, period_end)), \
                        patch("backend.tasks.monthly_report.send_email", return_value=(True, "sent")) as email:
                    result = send_monthly_activity_report()
            finally:
                self.app.config["ADMIN_EMAIL"] = previous_admin_email

            self.assertTrue(result["admin_sent"])
            admin_call = email.call_args_list[0]
            self.assertEqual(admin_call.args[0], admin_email)
            self.assertIn(f"Institute monthly placement activity report - June {report_year}", admin_call.args[1])
            self.assertIn("Monthly Placement Activity Report", admin_call.args[2])
            self.assertIn("<th align=\"left\">Drives conducted</th><td>1</td>", admin_call.args[2])
            self.assertIn("<th align=\"left\">Students applied</th><td>1</td>", admin_call.args[2])
            self.assertIn("<th align=\"left\">Students selected</th><td>1</td>", admin_call.args[2])

    def test_student_export_route_creates_csv_and_completion_alert(self):
        with tempfile.TemporaryDirectory() as export_dir:
            previous_export_dir = self.app.config["EXPORT_DIR"]
            self.app.config["EXPORT_DIR"] = export_dir
            suffix = uuid4().hex
            student_email = f"export-student-{suffix}@example.com"
            password = "secret123"
            try:
                with self.app.app_context():
                    company_user = User(
                        user_name="Export Company",
                        email_address=f"export-company-{suffix}@example.com",
                        user_role="company",
                        is_approved=True,
                        is_active=True,
                    )
                    company_user.set_password(password)
                    student_user = User(
                        user_name="Export Student",
                        email_address=student_email,
                        contact_number="9999999999",
                        user_role="student",
                        is_approved=True,
                        is_active=True,
                    )
                    student_user.set_password(password)
                    db.session.add_all([company_user, student_user])
                    db.session.flush()
                    company = CompanyProfile(
                        user_id=company_user.user_id,
                        company_name=f"Export Labs {suffix}",
                        industry="Technology",
                    )
                    student_identifier = f"EXP{suffix[:8]}"
                    student = StudentProfile(
                        user_id=student_user.user_id,
                        roll_number=student_identifier,
                        course="B.Tech",
                        branch="CSE",
                        graduation_year=2099,
                        cgpa=8.5,
                    )
                    db.session.add_all([company, student])
                    db.session.flush()
                    drive = JobPosition(
                        company_id=company.company_id,
                        title="Export Engineer",
                        job_type="full-time",
                        description="Build export systems.",
                        application_deadline=date.today() + timedelta(days=10),
                        status="approved",
                        is_active=True,
                    )
                    db.session.add(drive)
                    db.session.flush()
                    application = Application(
                        student_id=student.student_id,
                        job_id=drive.job_id,
                        status="shortlisted",
                    )
                    db.session.add(application)
                    db.session.commit()
                    student_id = student.student_id
                    user_id = student_user.user_id

                login = self.client.post("/api/auth/login", json={
                    "email": student_email,
                    "password": password,
                    "role": "student",
                })
                self.assertEqual(login.status_code, 200)

                with patch("backend.tasks.export_csv.send_email", return_value=(True, "sent")), \
                        patch("backend.tasks.export_csv.send_chat_webhook", return_value=(True, "sent")):
                    response = self.client.post("/api/student/export")

                self.assertEqual(response.status_code, 202)
                payload = response.get_json()
                self.assertEqual(payload["data"]["status"], "completed")
                self.assertTrue(payload["data"]["file_url"].endswith(".csv"))

                with self.app.app_context():
                    export = ExportJob.query.filter_by(student_id=student_id).order_by(ExportJob.export_id.desc()).first()
                    self.assertEqual(export.status, "completed")
                    self.assertIn("ready", export.message.lower())
                    self.assertIsNotNone(Notification.query.filter_by(
                        user_id=user_id,
                        title="Export ready",
                        category="export",
                    ).first())
                    csv_path = os.path.join(export_dir, os.path.basename(export.file_path))

                with open(csv_path, newline="", encoding="utf-8") as csv_file:
                    rows = list(csv.reader(csv_file))
                self.assertEqual(rows[0][:7], [
                    "Student ID",
                    "Company Name",
                    "Drive Title",
                    "Application Status",
                    "Applied Date",
                    "Deadline Date",
                    "Updated At",
                ])
                self.assertEqual(rows[1][0], student_identifier)
                self.assertEqual(rows[1][1], f"Export Labs {suffix}")
                self.assertEqual(rows[1][2], "Export Engineer")
                self.assertEqual(rows[1][3], "shortlisted")
            finally:
                self.app.config["EXPORT_DIR"] = previous_export_dir


if __name__ == "__main__":
    unittest.main()
