import io
import unittest

from backend.app import create_app
from backend.extensions import db


class ApiWorkflowTests(unittest.TestCase):
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

    def login(self, client, role, email, password):
        response = client.post("/api/auth/login", json={
            "role": role, "email": email, "password": password,
        })
        self.assertEqual(response.status_code, 200, response.get_json())

    def test_complete_role_workflow(self):
        admin = self.app.test_client()
        company = self.app.test_client()
        student = self.app.test_client()

        response = company.post("/api/auth/register/company", json={
            "company_name": "Workflow Labs",
            "industry": "Technology",
            "email": "workflow-company@example.com",
            "password": "secret123",
            "hr_first_name": "Hiring",
            "hr_last_name": "Manager",
            "hr_email": "hr@workflow.example.com",
            "address_line1": "1 Technology Park",
            "pincode": "560001",
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India",
        })
        self.assertEqual(response.status_code, 201, response.get_json())

        self.login(admin, "admin", "admin@placementportal.com", "admin123")
        companies = admin.get("/api/admin/companies?q=Workflow").get_json()["data"]
        company_id = companies[0]["id"]
        self.assertEqual(
            admin.patch(f"/api/admin/companies/{company_id}/status", json={"action": "approve"}).status_code,
            200,
        )

        self.login(company, "company", "workflow-company@example.com", "secret123")
        response = company.post("/api/company/drives", json={
            "title": "Graduate Engineer",
            "job_type": "full-time",
            "deadline": "2099-12-01",
            "location": "Hybrid",
            "salary": 12,
            "openings": 2,
            "min_cgpa": 7,
            "eligible_degrees": "B.Tech",
            "eligible_branches": "CSE",
            "eligible_years": "2099",
            "skills_required": "Python, SQL, Vue",
            "experience_required": "0-1 years",
            "benefits": "Health insurance",
            "description": "Build placement software and APIs.",
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        drive_id = response.get_json()["data"]["id"]
        self.assertEqual(
            admin.patch(f"/api/admin/drives/{drive_id}/status", json={"action": "approve"}).status_code,
            200,
        )
        response = company.post("/api/company/drives", json={
            "title": "Backend Engineer",
            "job_type": "full-time",
            "deadline": "2099-12-01",
            "location": "Hybrid",
            "salary": 10,
            "openings": 1,
            "min_cgpa": 7,
            "eligible_degrees": "B.Tech",
            "eligible_branches": "CSE",
            "eligible_years": "2099",
            "skills_required": "Python, SQL",
            "experience_required": "0-1 years",
            "benefits": "Health insurance",
            "description": "Build backend services.",
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        second_drive_id = response.get_json()["data"]["id"]
        self.assertEqual(
            admin.patch(f"/api/admin/drives/{second_drive_id}/status", json={"action": "approve"}).status_code,
            200,
        )

        response = student.post("/api/auth/register/student", data={
            "first_name": "Workflow",
            "last_name": "Student",
            "email": "workflow-student@example.com",
            "password": "secret123",
            "contact": "9999999998",
            "course": "B.Tech",
            "branch": "CSE",
            "graduation_year": "2099",
            "cgpa": "8.5",
            "skills": "Python, SQL, Vue",
            "experience": "API project",
            "address_line1": "2 Student Avenue",
            "pincode": "560001",
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India",
            "resume": (io.BytesIO(b"sample resume"), "resume.pdf"),
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        self.login(student, "student", "workflow-student@example.com", "secret123")

        drives = student.get("/api/student/drives?q=Python&eligible=1").get_json()["data"]
        self.assertIn(drive_id, [drive["id"] for drive in drives])
        self.assertIn(second_drive_id, [drive["id"] for drive in drives])
        response = student.post(f"/api/student/drives/{drive_id}/apply", json={})
        self.assertEqual(response.status_code, 201, response.get_json())
        application_id = response.get_json()["data"]["id"]
        response = student.post(f"/api/student/drives/{second_drive_id}/apply", json={})
        self.assertEqual(response.status_code, 201, response.get_json())
        second_application_id = response.get_json()["data"]["id"]

        response = company.patch(f"/api/company/applications/{application_id}", json={
            "status": "shortlisted",
            "feedback": "Shortlisted for interview.",
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        response = company.post(f"/api/company/applications/{application_id}/interviews", json={
            "scheduled_at": "2099-11-01T10:30",
            "mode": "online",
            "location_or_link": "https://meet.example.com/interview",
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        response = company.patch(f"/api/company/applications/{application_id}", json={
            "status": "placed",
            "feedback": "Strong technical interview.",
            "joining_date": "2099-12-15",
            "offer_notes": "Welcome to Workflow Labs.",
        })
        self.assertEqual(response.status_code, 200, response.get_json())

        applications = student.get("/api/student/applications").get_json()["data"]
        applications_by_id = {application["id"]: application for application in applications}
        self.assertEqual(applications_by_id[application_id]["status"], "placed")
        self.assertEqual(applications_by_id[application_id]["feedback"], "Strong technical interview.")
        self.assertEqual(applications_by_id[second_application_id]["status"], "rejected")
        self.assertEqual(
            applications_by_id[second_application_id]["feedback"],
            "Already placed at a different role",
        )
        letter_url = applications_by_id[application_id]["placement"]["offer_letter_url"]
        letter = student.get(letter_url)
        self.assertEqual(letter.status_code, 200)
        self.assertEqual(letter.data[:5], b"%PDF-")


if __name__ == "__main__":
    unittest.main()
