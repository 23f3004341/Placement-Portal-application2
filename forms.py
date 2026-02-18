from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, FloatField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    Regexp,
    URL,
    ValidationError,
)

from models import CompanyProfile, StudentProfile, User


class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    submit = SubmitField("Login")


class StudentRegistrationForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=60)])
    middle_name = StringField("Middle Name (Optional)", validators=[Optional(), Length(max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=60)])
    email_address = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    contact_number = StringField(
        "Contact Number",
        validators=[
            DataRequired(),
            Length(min=10, max=10),
            Regexp(r"^\d{10}$", message="Contact number must be 10 digits."),
        ],
    )
    address_line1 = StringField("Address Line 1", validators=[DataRequired(), Length(max=120)])
    address_line2 = StringField("Address Line 2", validators=[Optional(), Length(max=120)])
    landmark = StringField("Landmark (Optional)", validators=[Optional(), Length(max=120)])
    city = StringField("City", validators=[Optional(), Length(max=80)])
    state = StringField("State", validators=[Optional(), Length(max=80)])
    country = StringField("Country", validators=[Optional(), Length(max=80)])
    pincode = StringField(
        "Pincode",
        validators=[
            DataRequired(),
            Length(min=6, max=6),
            Regexp(r"^\d{6}$", message="Pincode must be 6 digits."),
        ],
    )
    gender = SelectField(
        "Gender",
        choices=[
            ("", "Select"),
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
            ("Not Specified", "Not Specified"),
        ],
        validators=[Optional()],
    )
    dob = DateField("Date of Birth", format="%Y-%m-%d", validators=[Optional()])

    roll_number = StringField("Roll Number", validators=[DataRequired(), Length(min=3, max=50)])
    course = StringField("Course", validators=[DataRequired(), Length(max=120)])
    branch = StringField("Branch", validators=[DataRequired(), Length(max=120)])
    graduation_year = IntegerField("Graduation Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    cgpa = FloatField("CGPA", validators=[Optional(), NumberRange(min=0, max=10)])
    skills = TextAreaField("Skills (Optional)", validators=[Optional(), Length(max=1000)])

    submit = SubmitField("Register as Student")

    def validate_email_address(self, field):
        existing = User.query.filter_by(email_address=field.data.strip().lower()).first()
        if existing:
            raise ValidationError("Email already registered.")

    def validate_roll_number(self, field):
        existing = StudentProfile.query.filter_by(roll_number=field.data.strip().upper()).first()
        if existing:
            raise ValidationError("Roll number already exists.")

    def validate_dob(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Date of birth cannot be in the future.")


class CompanyRegistrationForm(FlaskForm):
    email_address = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    contact_number = StringField(
        "Contact Number",
        validators=[
            DataRequired(),
            Length(min=10, max=10),
            Regexp(r"^\d{10}$", message="Contact number must be 10 digits."),
        ],
    )
    address_line1 = StringField("Address Line 1", validators=[DataRequired(), Length(max=120)])
    address_line2 = StringField("Address Line 2", validators=[Optional(), Length(max=120)])
    landmark = StringField("Landmark (Optional)", validators=[Optional(), Length(max=120)])
    city = StringField("City", validators=[Optional(), Length(max=80)])
    state = StringField("State", validators=[Optional(), Length(max=80)])
    country = StringField("Country", validators=[Optional(), Length(max=80)])
    pincode = StringField(
        "Pincode",
        validators=[
            DataRequired(),
            Length(min=6, max=6),
            Regexp(r"^\d{6}$", message="Pincode must be 6 digits."),
        ],
    )

    company_name = StringField("Company Name", validators=[DataRequired(), Length(max=180)])
    website = StringField("Website", validators=[Optional(), URL(), Length(max=255)])
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])
    headquarters = StringField("Headquarters", validators=[Optional(), Length(max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    hr_name = StringField("HR Name", validators=[DataRequired(), Length(max=120)])
    hr_email = StringField("HR Email", validators=[DataRequired(), Email(), Length(max=120)])
    hr_phone = StringField(
        "HR Phone",
        validators=[
            DataRequired(),
            Length(min=10, max=10),
            Regexp(r"^\d{10}$", message="HR contact number must be 10 digits."),
        ],
    )

    submit = SubmitField("Register Company")

    def validate_email_address(self, field):
        existing = User.query.filter_by(email_address=field.data.strip().lower()).first()
        if existing:
            raise ValidationError("Email already registered.")

    def validate_company_name(self, field):
        existing = CompanyProfile.query.filter(
            CompanyProfile.company_name.ilike(field.data.strip())
        ).first()
        if existing:
            raise ValidationError("Company name already exists.")


class StudentProfileEditForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    contact_number = StringField(
        "Contact Number",
        validators=[
            DataRequired(),
            Length(min=10, max=10),
            Regexp(r"^\d{10}$", message="Contact number must be 10 digits."),
        ],
    )
    address = TextAreaField("Address", validators=[DataRequired(), Length(min=10, max=500)])
    course = StringField("Course", validators=[DataRequired(), Length(max=120)])
    branch = StringField("Branch", validators=[DataRequired(), Length(max=120)])
    graduation_year = IntegerField("Graduation Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    cgpa = FloatField("CGPA", validators=[Optional(), NumberRange(min=0, max=10)])
    skills = TextAreaField("Skills", validators=[Optional(), Length(max=1000)])
    resume = FileField(
        "Resume (PDF/DOC/DOCX)",
        validators=[Optional(), FileAllowed(["pdf", "doc", "docx"], "Upload PDF, DOC, or DOCX only.")],
    )
    submit = SubmitField("Update Profile")


class CompanyProfileEditForm(FlaskForm):
    company_name = StringField("Company Name", validators=[DataRequired(), Length(max=180)])
    website = StringField("Website", validators=[Optional(), URL(), Length(max=255)])
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])
    headquarters = StringField("Headquarters", validators=[Optional(), Length(max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    hr_name = StringField("HR Name", validators=[Optional(), Length(max=120)])
    hr_email = StringField("HR Email", validators=[Optional(), Email(), Length(max=120)])
    hr_phone = StringField("HR Phone", validators=[Optional(), Length(max=20)])
    submit = SubmitField("Update Company Profile")


class CompanyDriveForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired(), Length(max=150)])
    job_type = SelectField(
        "Job Type",
        choices=[
            ("full-time", "Full-Time"),
            ("internship", "Internship"),
            ("contract", "Contract"),
        ],
        validators=[DataRequired()],
    )
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    salary_lpa = FloatField("Salary (LPA)", validators=[Optional(), NumberRange(min=0)])
    openings = IntegerField("Openings", validators=[DataRequired(), NumberRange(min=1, max=10000)])
    min_cgpa = FloatField("Minimum CGPA", validators=[Optional(), NumberRange(min=0, max=10)])
    eligible_branches = TextAreaField("Eligible Branches", validators=[Optional(), Length(max=1000)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=3000)])
    application_deadline = DateField("Application Deadline", format="%Y-%m-%d", validators=[Optional()])
    submit = SubmitField("Save Drive")
