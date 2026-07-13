from . import *


def admin_dashboard_summary():
    return {
        "applications": Application.query.filter(Application.status != "withdrawn").count(),
        "drives": JobPosition.query.count(),
        "companies": CompanyProfile.query.count(),
        "placed": Application.query.filter_by(status="placed").count(),
        "rejected": Application.query.filter_by(status="rejected").count(),
        "shortlisted": Application.query.filter(Application.status.in_(("shortlisted", "interview"))).count(),
    }


@main.get("/api/admin/dashboard")
@role_required("admin")
@cache.cached(timeout=60, key_prefix="admin_dashboard")
def admin_dashboard():
    summary = admin_dashboard_summary()
    return api_ok({
        "metrics": summary,
        "summary": summary,
    })


@main.get("/api/admin/dashboard/summary-chart.png")
@role_required("admin")
def admin_dashboard_summary_chart():
    summary = admin_dashboard_summary()
    labels = ["Applications", "Drives", "Companies", "Placed", "Rejected", "Shortlisted"]
    values = [summary["applications"], summary["drives"], summary["companies"], summary["placed"], summary["rejected"], summary["shortlisted"]]
    try:
        mpl_cache = Path(current_app.instance_path) / "matplotlib-cache"
        mpl_cache.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(mpl_cache))
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt

        fig, ax = plt.subplots(figsize=(9, 3.8), dpi=150)
        colors = ["#cfe2ff", "#fff3cd", "#d1e7dd", "#badbcc", "#f8d7da", "#cff4fc"]
        bars = ax.barh(labels, values, color=colors, edgecolor="#adb5bd", linewidth=0.8)
        ax.invert_yaxis()
        ax.set_xlabel("Count")
        ax.set_title("Placement Portal Summary", pad=12, fontsize=13, fontweight="bold")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", color="#e9ecef", linewidth=0.8)
        ax.set_axisbelow(True)
        max_value = max(values) if values else 0
        ax.set_xlim(0, max_value + max(1, max_value * 0.18))
        for bar, value in zip(bars, values):
            ax.text(value + 0.04, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=10)
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buffer.seek(0)
        response = send_file(buffer, mimetype="image/png")
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        current_app.logger.warning("Matplotlib chart generation failed: %s", exc)
        return api_error("Unable to generate dashboard chart.", 500)


@main.post("/api/admin/tasks/daily-reminders")
@role_required("admin")
def admin_run_daily_reminders():
    result = send_daily_deadline_reminders()
    return api_ok(result, "Task (a) daily reminders synced with MailHog.")


@main.post("/api/admin/tasks/monthly-report")
@role_required("admin")
def admin_run_monthly_report():
    result = send_monthly_activity_report()
    return api_ok(result, "Task (b) monthly reports synced with MailHog.")


@main.get("/api/admin/companies")
@role_required("admin")
def admin_companies():
    query_text = (request.args.get("q") or "").strip().lower()
    query = CompanyProfile.query.join(User)
    if query_text:
        like = f"{query_text}%"
        query = query.filter(or_(func.lower(CompanyProfile.company_name).like(like), func.lower(CompanyProfile.industry).like(like)))
    companies = [company_json(item) for item in query.order_by(func.lower(CompanyProfile.company_name)).all()]
    return api_ok(companies)


@main.patch("/api/admin/companies/<int:company_id>/status")
@role_required("admin")
def admin_company_status(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    action = ((request.get_json(silent=True) or {}).get("action") or "").lower()
    if action == "approve":
        company.user.is_approved, company.user.is_active = True, True
        restriction = AccountRestriction.query.filter_by(email_address=company.user.email_address).first()
        if restriction:
            db.session.delete(restriction)
    elif action == "reject":
        company.user.is_approved = False
        company.user.is_active = False
    elif action in {"blacklist", "deactivate"}:
        company.user.is_active = False
        restriction = AccountRestriction.query.filter_by(email_address=company.user.email_address).first()
        if not restriction:
            db.session.add(AccountRestriction(email_address=company.user.email_address, reason="blacklisted"))
    elif action in {"activate", "unblacklist"}:
        company.user.is_active = True
        restriction = AccountRestriction.query.filter_by(email_address=company.user.email_address).first()
        if restriction:
            db.session.delete(restriction)
    else:
        return api_error("Invalid company action.")
    db.session.commit()
    invalidate_caches()
    return api_ok(company_json(company), "Company status updated.")


@main.delete("/api/admin/companies/<int:company_id>")
@role_required("admin")
def admin_delete_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    db.session.delete(company.user)
    db.session.commit()
    invalidate_caches()
    return api_ok(message="Company removed.")


@main.get("/api/admin/students")
@role_required("admin")
def admin_students():
    query_text = (request.args.get("q") or "").strip().lower()
    query = StudentProfile.query.join(User)
    if query_text:
        like = f"{query_text}%"
        query = query.filter(or_(
            func.lower(User.user_name).like(like),
            func.lower(StudentProfile.roll_number).like(like),
            func.lower(User.contact_number).like(like),
        ))
    students = [student_json(item) for item in query.order_by(func.lower(User.user_name)).all()]
    return api_ok(students)


@main.patch("/api/admin/students/<int:student_id>")
@role_required("admin")
def admin_update_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    payload = request.get_json(silent=True) or {}
    try:
        name = (payload.get("name") or student.user.user_name).strip()
        if len(name) < 2:
            return api_error("Student name is required.", 422)
        student.user.user_name = name

        email = (payload.get("email") or student.user.email_address).strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return api_error("A valid email is required.", 422)
        existing_email = User.query.filter(
            func.lower(User.email_address) == email,
            User.user_id != student.user_id,
        ).first()
        if existing_email:
            return api_error("This email is already registered.", 409)
        student.user.email_address = email

        contact = str(payload.get("contact") or "").strip()
        if contact and not re.fullmatch(r"\d{10}", contact):
            return api_error("Contact number must contain exactly 10 digits.", 422)
        student.user.contact_number = contact

        roll_number = (payload.get("roll_number") or student.roll_number).strip().upper()
        existing_roll = StudentProfile.query.filter(
            func.lower(StudentProfile.roll_number) == roll_number.lower(),
            StudentProfile.student_id != student.student_id,
        ).first()
        if existing_roll:
            return api_error("This Student ID is already registered.", 409)
        student.roll_number = roll_number

        student.course = (payload.get("course") or student.course).strip()
        student.branch = (payload.get("branch") or student.branch).strip()
        student.graduation_year = int(payload.get("graduation_year") or student.graduation_year)
        if payload.get("cgpa") not in (None, ""):
            student.cgpa = float(payload.get("cgpa"))

        db.session.commit()
        invalidate_caches()
        return api_ok(student_json(student), "Student details updated.")
    except ValueError as exc:
        db.session.rollback()
        return api_error(str(exc), 422)


@main.patch("/api/admin/students/<int:student_id>/status")
@role_required("admin")
def admin_student_status(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    action = ((request.get_json(silent=True) or {}).get("action") or "").lower()
    if action in {"blacklist", "deactivate"}:
        student.user.is_active = False
        if not AccountRestriction.query.filter_by(email_address=student.user.email_address).first():
            db.session.add(AccountRestriction(email_address=student.user.email_address, reason="blacklisted"))
    elif action in {"activate", "unblacklist"}:
        student.user.is_active = True
        restriction = AccountRestriction.query.filter_by(email_address=student.user.email_address).first()
        if restriction:
            db.session.delete(restriction)
    else:
        return api_error("Invalid student action.")
    db.session.commit()
    invalidate_caches()
    return api_ok(student_json(student), "Student status updated.")


@main.delete("/api/admin/students/<int:student_id>")
@role_required("admin")
def admin_delete_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    db.session.delete(student.user)
    db.session.commit()
    invalidate_caches()
    return api_ok(message="Student removed.")


@main.get("/api/admin/drives")
@role_required("admin")
def admin_drives():
    query_text = (request.args.get("q") or "").strip().lower()
    query = JobPosition.query.join(CompanyProfile)
    if query_text:
        like = f"{query_text}%"
        query = query.filter(or_(func.lower(JobPosition.title).like(like), func.lower(CompanyProfile.company_name).like(like), func.lower(JobPosition.skills_required).like(like)))
    return api_ok([drive_json(item) for item in query.order_by(func.lower(CompanyProfile.company_name), func.lower(JobPosition.title)).all()])


@main.patch("/api/admin/drives/<int:job_id>/status")
@role_required("admin")
def admin_drive_status(job_id):
    drive = JobPosition.query.get_or_404(job_id)
    action = ((request.get_json(silent=True) or {}).get("action") or "").lower()
    if action not in {"approve", "reject", "close", "activate"}:
        return api_error("Invalid drive action.")
    if action in {"approve", "activate"} and drive.application_deadline < date.today():
        return api_error("A job with a past application deadline cannot be approved or activated.", 422)
    was_approved = drive.status == "approved" and drive.is_active
    drive.status = {"approve": "approved", "reject": "rejected", "close": "closed", "activate": "approved"}[action]
    drive.is_active = action in {"approve", "activate"}
    db.session.commit()
    response_message = "Drive status updated."
    if action in {"approve", "activate"} and not was_approved:
        salary = f"{drive.salary_lpa:g} {drive.salary_unit}" if drive.salary_lpa else "Not disclosed"
        chat_ok, chat_result = send_chat_message(
            f"{current_app.config.get('UNIVERSITY_NAME', 'Northbridge University')}\n"
            f"New Placement Opportunity\n\n"
            f"{drive.company.company_name} has posted a new job for eligible students.\n\n"
            f"Role: {drive.title}\n"
            f"Location: {drive.location or 'Not specified'}\n"
            f"Openings: {drive.openings}\n"
            f"Package: {salary}\n"
            f"Minimum CGPA: {drive.min_cgpa if drive.min_cgpa is not None else 'Not specified'}\n"
            f"Skills: {drive.skills_required or 'Not specified'}\n"
            f"Deadline: {drive.application_deadline:%d-%m-%Y}"
        )
        response_message = (
            "Drive approved and the GSpace announcement was delivered."
            if chat_ok
            else f"Drive approved, but the GSpace announcement failed: {chat_result}."
        )
    invalidate_caches()
    return api_ok(drive_json(drive), response_message)


@main.delete("/api/admin/drives/<int:job_id>")
@role_required("admin")
def admin_delete_drive(job_id):
    drive = JobPosition.query.get_or_404(job_id)
    db.session.delete(drive)
    db.session.commit()
    invalidate_caches()
    return api_ok(message="Drive removed.")


@main.get("/api/admin/applications")
@role_required("admin")
def admin_applications():
    return api_ok([application_json(item) for item in Application.query.order_by(Application.application_id.desc()).all()])
