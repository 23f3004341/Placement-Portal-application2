from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    DateField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    URL,
    ValidationError,
)

from models import CompanyProfile, StudentProfile, User

DEGREE_CHOICES = [
    ("", "Select Degree"),
    ("B.Tech", "B.Tech"),
    ("M.Tech", "M.Tech"),
    ("B.S.", "B.S."),
    ("M.S.", "M.S."),
    ("B.Tech + M.Tech (Dual Degree)", "B.Tech + M.Tech (Dual Degree)"),
    ("B.S. + M.S. (Dual Degree)", "B.S. + M.S. (Dual Degree)"),
    ("Ph.D.", "Ph.D."),
    ("B.E.", "B.E."),
    ("M.E.", "M.E."),
    ("MCA", "MCA"),
    ("Other Technical Degree", "Other Technical Degree"),
]

BRANCH_CHOICES = [
    ("", "Select Branch"),
    ("Computer Science Engineering", "Computer Science Engineering"),
    ("Data Science", "Data Science"),
    ("AI/ML", "AI/ML"),
    ("Electronics and Communication Engineering", "Electronics and Communication Engineering"),
    ("Electrical Engineering", "Electrical Engineering"),
    ("Mathematics and Computing", "Mathematics and Computing"),
    ("Chemical Engineering", "Chemical Engineering"),
    ("Mechanical Engineering", "Mechanical Engineering"),
    ("Civil Engineering", "Civil Engineering"),
    ("Engineering Physics", "Engineering Physics"),
    ("Mining Engineering", "Mining Engineering"),
    ("Metallurgical Engineering", "Metallurgical Engineering"),
    ("Aerospace Engineering", "Aerospace Engineering"),
    ("Aeronautical Engineering", "Aeronautical Engineering"),
    ("Biotechnology", "Biotechnology"),
    ("Information Technology", "Information Technology"),
    ("Electronics Engineering", "Electronics Engineering"),
    ("Instrumentation Engineering", "Instrumentation Engineering"),
    ("Production Engineering", "Production Engineering"),
    ("Other Technical Branch", "Other Technical Branch"),
]

ELIGIBLE_DEGREE_CHOICES = [choice for choice in DEGREE_CHOICES if choice[0]]
ELIGIBLE_BRANCH_CHOICES = [choice for choice in BRANCH_CHOICES if choice[0]]


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
        validators=[DataRequired()],
    )
    dob = DateField("Date of Birth", format="%Y-%m-%d", validators=[DataRequired()])

    course = SelectField("Degree", choices=DEGREE_CHOICES, validators=[DataRequired()])
    branch = SelectField("Branch", choices=BRANCH_CHOICES, validators=[DataRequired()])
    graduation_year = IntegerField("Graduation Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    cgpa = FloatField("CGPA", validators=[DataRequired(), NumberRange(min=0, max=10)])
    resume = FileField(
        "Resume (PDF/DOC/DOCX)",
        validators=[
            FileRequired("Resume is required."),
            FileAllowed(["pdf", "doc", "docx"], "Upload PDF, DOC, or DOCX only."),
        ],
    )

    submit = SubmitField("Register as Student")

    def validate_email_address(self, field):
        existing = User.query.filter_by(email_address=field.data.strip().lower()).first()
        if existing:
            raise ValidationError("Email already registered.")

    def validate_dob(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Date of birth cannot be in the future.")


class CompanyRegistrationForm(FlaskForm):
    email_address = StringField("Company Email ID", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
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
    website = StringField("Website", validators=[DataRequired(), URL(), Length(max=255)])
    industry = StringField("Industry", validators=[DataRequired(), Length(max=100)])
    headquarters = StringField("Headquarters", validators=[DataRequired(), Length(max=150)])
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

    def validate_hr_email(self, field):
        hr_email = field.data.strip().lower()
        company_email = (self.email_address.data or "").strip().lower()
        if hr_email == company_email:
            raise ValidationError("HR Email must be different from Company Email ID.")
        existing = User.query.filter_by(email_address=hr_email).first()
        if existing:
            raise ValidationError("Email already registered.")

    def validate_company_name(self, field):
        existing = CompanyProfile.query.filter(
            CompanyProfile.company_name.ilike(field.data.strip())
        ).first()
        if existing:
            raise ValidationError("Company name already exists.")


class CompanyAdminEditForm(FlaskForm):
    company_name = StringField("Company Name", validators=[DataRequired(), Length(max=180)])
    email_address = StringField("Company Email ID", validators=[DataRequired(), Email(), Length(max=120)])
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
    website = StringField("Website", validators=[DataRequired(), URL(), Length(max=255)])
    industry = StringField("Industry", validators=[DataRequired(), Length(max=100)])
    headquarters = StringField("Headquarters", validators=[DataRequired(), Length(max=150)])
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
    submit = SubmitField("Update Company")

    def __init__(self, original_email=None, original_company_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = (original_email or "").strip().lower()
        self.original_company_name = (original_company_name or "").strip().lower()

    def validate_email_address(self, field):
        email = (field.data or "").strip().lower()
        existing = User.query.filter_by(email_address=email).first()
        if existing and email != self.original_email:
            raise ValidationError("Email already registered.")

    def validate_company_name(self, field):
        company_name = (field.data or "").strip().lower()
        existing = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(field.data.strip())).first()
        if existing and company_name != self.original_company_name:
            raise ValidationError("Company name already exists.")

    def validate_hr_email(self, field):
        hr_email = (field.data or "").strip().lower()
        company_email = (self.email_address.data or "").strip().lower()
        if hr_email == company_email:
            raise ValidationError("HR Email must be different from Company Email ID.")


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
    course = SelectField("Degree", choices=DEGREE_CHOICES, validators=[DataRequired()])
    branch = SelectField("Branch", choices=BRANCH_CHOICES, validators=[DataRequired()])
    graduation_year = IntegerField("Graduation Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    cgpa = FloatField("CGPA", validators=[DataRequired(), NumberRange(min=0, max=10)])
    resume = FileField(
        "Resume (PDF/DOC/DOCX)",
        validators=[Optional(), FileAllowed(["pdf", "doc", "docx"], "Upload PDF, DOC, or DOCX only.")],
    )
    submit = SubmitField("Update Profile")


class StudentFullProfileEditForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=60)])
    middle_name = StringField("Middle Name (Optional)", validators=[Optional(), Length(max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=60)])
    email_address = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("New Password (Optional)", validators=[Optional(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[Optional(), EqualTo("password", message="Passwords must match.")],
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
        validators=[DataRequired()],
    )
    dob = DateField("Date of Birth", format="%Y-%m-%d", validators=[DataRequired()])
    course = SelectField("Degree", choices=DEGREE_CHOICES, validators=[DataRequired()])
    branch = SelectField("Branch", choices=BRANCH_CHOICES, validators=[DataRequired()])
    graduation_year = IntegerField("Graduation Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    cgpa = FloatField("CGPA", validators=[DataRequired(), NumberRange(min=0, max=10)])
    resume = FileField(
        "Resume (PDF/DOC/DOCX)",
        validators=[Optional(), FileAllowed(["pdf", "doc", "docx"], "Upload PDF, DOC, or DOCX only.")],
    )
    submit = SubmitField("Update Profile")

    def __init__(self, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = (original_email or "").strip().lower()

    def validate_email_address(self, field):
        email = (field.data or "").strip().lower()
        existing = User.query.filter_by(email_address=email).first()
        if existing and email != self.original_email:
            raise ValidationError("Email already registered.")

    def validate_dob(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Date of birth cannot be in the future.")


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
    location = StringField("Location", validators=[DataRequired(), Length(max=120)])
    salary_lpa = FloatField("Salary", validators=[InputRequired(), NumberRange(min=0)])
    salary_unit = SelectField(
        "Unit",
        choices=[
            ("lpa", "LPA"),
            ("k_month", "K/month"),
        ],
        validators=[DataRequired()],
        default="lpa",
    )
    openings = IntegerField("Openings", validators=[DataRequired(), NumberRange(min=1, max=10000)])
    min_cgpa = FloatField("Minimum CGPA", validators=[InputRequired(), NumberRange(min=0, max=10)])
    eligible_degrees = SelectMultipleField(
        "Eligible Degrees",
        choices=ELIGIBLE_DEGREE_CHOICES,
        validators=[DataRequired()],
    )
    eligible_branches = SelectMultipleField(
        "Eligible Branches",
        choices=ELIGIBLE_BRANCH_CHOICES,
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=3000)])
    application_deadline = DateField("Application Deadline", format="%Y-%m-%d", validators=[DataRequired()])
    submit = SubmitField("Save Drive")
