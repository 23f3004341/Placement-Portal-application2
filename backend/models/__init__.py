from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..init import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(120), nullable=False)
    email_address = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    gender = db.Column(db.String(30))
    dob = db.Column(db.Date)

    user_role = db.Column(db.String(20), nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    admin_profile = db.relationship(
        "AdminProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    company_profile = db.relationship(
        "CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    student_profile = db.relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return f"<User {self.user_id} {self.email_address} ({self.user_role})>"


class AdminProfile(db.Model):
    __tablename__ = "admin_profiles"

    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    employee_code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    office_name = db.Column(db.String(150), nullable=False, default="Placement Cell")

    user = db.relationship("User", back_populates="admin_profile")

    def __repr__(self):
        return f"<AdminProfile {self.admin_id} user={self.user_id}>"


class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    company_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    company_name = db.Column(db.String(180), nullable=False, unique=True, index=True)
    website = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    description = db.Column(db.Text)
    headquarters = db.Column(db.String(150))
    hr_name = db.Column(db.String(120))
    hr_email = db.Column(db.String(120))
    hr_phone = db.Column(db.String(20))

    user = db.relationship("User", back_populates="company_profile")
    job_positions = db.relationship(
        "JobPosition", back_populates="company", cascade="all, delete-orphan"
    )
    placements = db.relationship(
        "Placement", back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CompanyProfile {self.company_id} {self.company_name}>"


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    student_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    roll_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    course = db.Column(db.String(120), nullable=False)
    branch = db.Column(db.String(120), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float)
    resume_filename = db.Column(db.String(255))
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship(
        "Application", back_populates="student", cascade="all, delete-orphan"
    )
    placements = db.relationship(
        "Placement", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<StudentProfile {self.student_id} roll={self.roll_number}>"


class JobPosition(db.Model):
    __tablename__ = "job_positions"

    job_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("company_profiles.company_id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(150), nullable=False)
    job_type = db.Column(db.String(40), nullable=False, default="full-time")
    location = db.Column(db.String(120))
    salary_lpa = db.Column(db.Float)
    salary_unit = db.Column(db.String(20), nullable=False, default="lpa")
    openings = db.Column(db.Integer, nullable=False, default=1)
    min_cgpa = db.Column(db.Float)
    eligible_degrees = db.Column(db.Text)
    eligible_branches = db.Column(db.Text)
    eligible_years = db.Column(db.Text)
    skills_required = db.Column(db.Text)
    experience_required = db.Column(db.String(255))
    benefits = db.Column(db.Text)
    description = db.Column(db.Text)
    application_deadline = db.Column(db.Date)

    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    company = db.relationship("CompanyProfile", back_populates="job_positions")
    applications = db.relationship(
        "Application", back_populates="job_position", cascade="all, delete-orphan"
    )
    placements = db.relationship(
        "Placement", back_populates="job_position", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<JobPosition {self.job_id} {self.title}>"


class Application(db.Model):
    __tablename__ = "applications"

    application_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id = db.Column(
        db.Integer, db.ForeignKey("job_positions.job_id", ondelete="CASCADE"), nullable=False, index=True
    )
    applied_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cover_letter = db.Column(db.Text)
    company_feedback = db.Column(db.Text)
    status_updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    status = db.Column(db.String(20), nullable=False, default="applied", index=True)

    student = db.relationship("StudentProfile", back_populates="applications")
    job_position = db.relationship("JobPosition", back_populates="applications")
    placement = db.relationship(
        "Placement", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    interviews = db.relationship(
        "Interview", back_populates="application", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "job_id", name="uq_student_job_application"),
    )

    def __repr__(self):
        return f"<Application {self.application_id} student={self.student_id} job={self.job_id}>"


class Placement(db.Model):
    __tablename__ = "placements"

    placement_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.application_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("company_profiles.company_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id = db.Column(
        db.Integer, db.ForeignKey("job_positions.job_id", ondelete="CASCADE"), nullable=False, index=True
    )
    offered_package_lpa = db.Column(db.Float)
    offer_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    joining_date = db.Column(db.Date)
    offer_notes = db.Column(db.Text)

    placement_status = db.Column(db.String(20), nullable=False, default="offered", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    application = db.relationship("Application", back_populates="placement")
    student = db.relationship("StudentProfile", back_populates="placements")
    company = db.relationship("CompanyProfile", back_populates="placements")
    job_position = db.relationship("JobPosition", back_populates="placements")

    def __repr__(self):
        return f"<Placement {self.placement_id} student={self.student_id} job={self.job_id}>"


class ExportJob(db.Model):
    __tablename__ = "export_jobs"

    export_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id = db.Column(db.String(120), index=True)
    status = db.Column(db.String(20), nullable=False, default="queued", index=True)
    file_path = db.Column(db.String(255))
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    student = db.relationship("StudentProfile", backref=db.backref("export_jobs", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ExportJob {self.export_id} student={self.student_id} status={self.status}>"


class CompanyExportJob(db.Model):
    __tablename__ = "company_export_jobs"

    export_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("company_profiles.company_id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id = db.Column(db.String(120), index=True)
    status = db.Column(db.String(20), nullable=False, default="queued", index=True)
    file_path = db.Column(db.String(255))
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    company = db.relationship(
        "CompanyProfile", backref=db.backref("export_jobs", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<CompanyExportJob {self.export_id} company={self.company_id} status={self.status}>"


class Interview(db.Model):
    __tablename__ = "interviews"

    interview_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_at = db.Column(db.DateTime, nullable=False, index=True)
    mode = db.Column(db.String(30), nullable=False, default="online")
    location_or_link = db.Column(db.String(500))
    notes = db.Column(db.Text)
    feedback = db.Column(db.Text)
    result = db.Column(db.String(20))
    status = db.Column(db.String(20), nullable=False, default="scheduled", index=True)
    reminder_sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    application = db.relationship("Application", back_populates="interviews")

    def __repr__(self):
        return f"<Interview {self.interview_id} application={self.application_id} at={self.scheduled_at}>"


class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(40), nullable=False, default="info", index=True)
    link_url = db.Column(db.String(255))
    source_key = db.Column(db.String(120), index=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.notification_id} user={self.user_id} read={self.is_read}>"


class AccountRestriction(db.Model):
    __tablename__ = "account_restrictions"

    restriction_id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(120), unique=True, nullable=False, index=True)
    reason = db.Column(db.String(30), nullable=False, index=True) 
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<AccountRestriction {self.email_address} {self.reason}>"
