from . import *


def assign_role(user, role_name):
    role = Role.query.filter_by(name=role_name).first()
    if role and role not in user.roles:
        user.roles.append(role)


@main.get("/")
def frontend_index():
    response = send_from_directory(FRONTEND_DIR, "index.html")
    response.headers["Cache-Control"] = "no-store"
    return response


@main.get("/<path:path>")
def frontend_file(path):
    if path.startswith("api/"):
        return api_error("Resource not found.", 404)
    file_path = Path(FRONTEND_DIR) / path
    if file_path.is_file():
        return send_from_directory(file_path.parent, file_path.name)
    return send_from_directory(FRONTEND_DIR, "index.html")


@main.get("/api/auth/me")
def auth_me():
    return api_ok({"user": user_json(current_user) if current_user.is_authenticated else None})


@main.get("/api/mailhog")
def mailhog_config():
    url = (
        url_for("main.mailhog_current_user_inbox")
        if current_user.is_authenticated
        else mailhog_url()
    )
    return api_ok({"url": url, "available": True})


@main.get("/api/mailhog/inbox")
@login_required
def mailhog_current_user_inbox():
    return make_response(render_filtered_inbox(current_user))


@main.post("/api/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = (payload.get("role") or "").strip().lower()
    user = User.query.filter(func.lower(User.email_address) == email).first()
    if not user or not user.check_password(password) or user.user_role != role:
        return api_error("Invalid email, password, or role.", 401)
    restriction = AccountRestriction.query.filter(func.lower(AccountRestriction.email_address) == email).first()
    if restriction:
        return api_error("You have been blacklisted by the admin.", 403)
    if not user.is_active:
        return api_error("This account is inactive.", 403)
    if role == "company" and not user.is_approved:
        return api_error("Company registration is awaiting admin approval.", 403)
    login_user(user)
    return api_ok({"user": user_json(user)}, "Login successful.")


@main.post("/api/auth/logout")
@login_required
def auth_logout():
    logout_user()
    return api_ok(message="Logged out.")


def validate_registration(payload, company=False):
    errors = {}
    if company:
        if len((payload.get("company_name") or "").strip()) < 2:
            errors["company_name"] = "A valid company name is required."
        if not (payload.get("industry") or "").strip():
            errors["industry"] = "Industry is required."
        if not (payload.get("hr_first_name") or "").strip() and len((payload.get("hr_name") or "").strip()) < 2:
            errors["hr_first_name"] = "HR first name is required."
        if not (payload.get("hr_last_name") or "").strip() and len((payload.get("hr_name") or "").strip()) < 2:
            errors["hr_last_name"] = "HR last name is required."
        hr_email = (payload.get("hr_email") or "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", hr_email):
            errors["hr_email"] = "A valid HR email is required."
        hr_phone = str(payload.get("hr_phone") or "").strip()
        if hr_phone and not re.fullmatch(r"\d{10}", hr_phone):
            errors["hr_phone"] = "HR phone must contain exactly 10 digits."
    else:
        if not (payload.get("first_name") or "").strip() and len((payload.get("name") or "").strip()) < 2:
            errors["first_name"] = "First name is required."
        if not (payload.get("last_name") or "").strip() and len((payload.get("name") or "").strip()) < 2:
            errors["last_name"] = "Last name is required."
    email = (payload.get("email") or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors["email"] = "A valid email is required."
    if len(payload.get("password") or "") < 6:
        errors["password"] = "Password must contain at least 6 characters."
    if payload.get("confirm_password") is not None and payload.get("password") != payload.get("confirm_password"):
        errors["confirm_password"] = "Passwords do not match."
    if User.query.filter(func.lower(User.email_address) == email).first():
        errors["email"] = "This email is already registered."
    contact = str(payload.get("contact") or "").strip()
    if contact and not re.fullmatch(r"\d{10}", contact):
        errors["contact"] = "Contact number must contain exactly 10 digits."
    for field in ("address_line1", "pincode", "city", "state", "country"):
        if not (payload.get(field) or "").strip():
            errors[field] = f"{field.replace('_', ' ').title()} is required."
    if payload.get("pincode") and not re.fullmatch(r"\d{6}", str(payload.get("pincode")).strip()):
        errors["pincode"] = "Pincode must contain exactly 6 digits."
    return errors


@main.post("/api/auth/register/student")
def register_student():
    payload = request.form
    errors = validate_registration(payload)
    required = {
        "course": payload.get("course"),
        "branch": payload.get("branch"),
        "graduation_year": payload.get("graduation_year"),
        "contact": payload.get("contact"),
        "cgpa": payload.get("cgpa"),
    }
    for key, value in required.items():
        if not value:
            errors[key] = f"{key.replace('_', ' ').title()} is required."
    if not request.files.get("resume") or not request.files["resume"].filename:
        errors["resume"] = "Resume is required."
    if errors:
        return api_error("Please correct the registration form.", 422, errors)
    try:
        year = int(payload.get("graduation_year"))
        cgpa = float(payload.get("cgpa")) if payload.get("cgpa") else None
        user = User(
            user_name=compose_person_name(payload),
            email_address=payload.get("email").strip().lower(),
            contact_number=(payload.get("contact") or "").strip(),
            address=compose_address(payload),
            gender=(payload.get("gender") or "").strip() or None,
            dob=parse_date(payload.get("dob"), "Date of birth"),
            user_role="student",
            is_active=True,
            is_approved=True,
        )
        user.set_password(payload.get("password"))
        assign_role(user, "student")
        db.session.add(user)
        db.session.flush()
        existing_rolls = {
            int(match.group(1))
            for (roll_number,) in db.session.query(StudentProfile.roll_number).all()
            if roll_number and (match := re.fullmatch(r"STU(\d+)", roll_number.strip().upper()))
        }
        next_roll_number = 1
        while next_roll_number in existing_rolls:
            next_roll_number += 1
        roll = f"STU{next_roll_number:02d}"
        student = StudentProfile(
            user_id=user.user_id,
            roll_number=roll,
            course=payload.get("course").strip(),
            branch=payload.get("branch").strip(),
            graduation_year=year,
            cgpa=cgpa,
            skills="",
            experience=(payload.get("experience") or "").strip(),
        )
        db.session.add(student)
        db.session.flush()
        student.resume_filename = save_resume(request.files.get("resume"), user.user_id)
        db.session.commit()
        invalidate_caches()
        return api_ok(message="Student registration completed.", status=201)
    except (ValueError, IntegrityError) as exc:
        db.session.rollback()
        return api_error(str(exc) if isinstance(exc, ValueError) else "Registration data already exists.", 422)


@main.post("/api/auth/register/company")
def register_company():
    payload = request.get_json(silent=True) or {}
    errors = validate_registration(payload, company=True)
    if errors:
        return api_error("Please correct the registration form.", 422, errors)
    user = User(
        user_name=payload.get("company_name").strip(),
        email_address=payload.get("email").strip().lower(),
        contact_number=(payload.get("contact") or "").strip(),
        address=compose_address(payload),
        user_role="company",
        is_active=True,
        is_approved=False,
    )
    user.set_password(payload.get("password"))
    assign_role(user, "company")
    company = CompanyProfile(
        user=user,
        company_name=payload.get("company_name").strip(),
        industry=(payload.get("industry") or "").strip(),
        website=(payload.get("website") or "").strip(),
        headquarters=(payload.get("headquarters") or "").strip(),
        hr_name=compose_person_name(payload, "hr_"),
        hr_email=(payload.get("hr_email") or "").strip(),
        hr_phone=(payload.get("hr_phone") or "").strip(),
        description=(payload.get("description") or "").strip(),
    )
    try:
        db.session.add_all([user, company])
        db.session.commit()
        invalidate_caches()
        return api_ok(message="Company registered and awaiting admin approval.", status=201)
    except IntegrityError:
        db.session.rollback()
        return api_error("Company name or email already exists.", 409)
