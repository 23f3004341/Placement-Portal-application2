from . import *


def admin_dashboard_summary():
    return {
        "companies": CompanyProfile.query.count(),
        "drives": JobPosition.query.count(),
        "students": StudentProfile.query.count(),
        "applications": Application.query.filter(Application.status != "withdrawn").count(),
    }


@main.get("/api/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    summary = admin_dashboard_summary()
    companies = CompanyProfile.query.order_by(func.lower(CompanyProfile.company_name)).all()
    status_keys = ["applied", "shortlisted", "placed", "rejected"]
    company_counts = {company.company_id: Counter() for company in companies}
    rows = (
        db.session.query(JobPosition.company_id, Application.status, func.count(Application.application_id))
        .join(JobPosition, Application.job_id == JobPosition.job_id)
        .filter(Application.status.in_(status_keys))
        .group_by(JobPosition.company_id, Application.status)
        .all()
    )
    for company_id, status, count in rows:
        company_counts.setdefault(company_id, Counter())[status] = count
    return api_ok({
        "metrics": summary,
        "summary": summary,
        "company_analytics": {
            "labels": [company.company_name for company in companies],
            "statuses": status_keys,
            "series": {
                status: [company_counts[company.company_id][status] for company in companies]
                for status in status_keys
            },
            "overall": {
                status: sum(company_counts[company.company_id][status] for company in companies)
                for status in status_keys
            },
        },
    })


@main.get("/api/admin/dashboard/summary-chart.png")
@role_required("admin")
def admin_dashboard_summary_chart():
    companies = CompanyProfile.query.order_by(func.lower(CompanyProfile.company_name)).all()
    labels = [company.company_name for company in companies]
    status_groups = {
        "Applied": {"applied"},
        "Shortlisted": {"shortlisted"},
        "Placed": {"placed"},
        "Rejected": {"rejected"},
    }
    company_counts = {company.company_id: Counter() for company in companies}
    rows = (
        db.session.query(JobPosition.company_id, Application.status, func.count(Application.application_id))
        .join(JobPosition, Application.job_id == JobPosition.job_id)
        .filter(Application.status != "withdrawn")
        .group_by(JobPosition.company_id, Application.status)
        .all()
    )
    for company_id, status, count in rows:
        company_counts.setdefault(company_id, Counter())[status] = count
    try:
        mpl_cache = Path(current_app.instance_path) / "matplotlib-cache"
        mpl_cache.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(mpl_cache))
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt

        fig, (ax, pie_ax) = plt.subplots(
            1, 2, figsize=(12, 4.8), dpi=150,
            gridspec_kw={"width_ratios": [1.65, 1]},
        )
        colors = ["#b8c5d6", "#d8c6a5", "#9dbdaf", "#d4aeb2"]
        x = list(range(len(labels)))
        width = 0.18
        for index, (group, statuses) in enumerate(status_groups.items()):
            values = [sum(company_counts[company.company_id][status] for status in statuses) for company in companies]
            bars = ax.bar([value + (index - 1.5) * width for value in x], values, width, label=group, color=colors[index])
            ax.bar_label(bars, padding=2, fontsize=8, labels=[str(value) if value else "" for value in values])
        ax.set_xticks(x, labels, rotation=25, ha="right")
        ax.set_ylabel("Applications")
        ax.set_title("Company placement analytics", pad=14, fontsize=11, fontweight="normal", color="#495057")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#ece6e5", linewidth=0.8)
        ax.set_axisbelow(True)
        if not labels:
            ax.text(0.5, 0.5, "No company placement data yet", ha="center", va="center", transform=ax.transAxes)

        overall = [
            sum(
                company_counts[company.company_id][status]
                for company in companies
                for status in statuses
            )
            for statuses in status_groups.values()
        ]
        if sum(overall):
            pie_ax.pie(
                overall,
                labels=list(status_groups),
                colors=colors,
                autopct=lambda percent: f"{percent:.0f}%" if percent else "",
                startangle=90,
                wedgeprops={"linewidth": 1, "edgecolor": "white"},
                textprops={"fontsize": 9},
            )
        else:
            pie_ax.text(0.5, 0.5, "No application records yet", ha="center", va="center")
        pie_ax.set_title("Overall application record", pad=14, fontsize=11, fontweight="normal", color="#495057")
        handles, legend_labels = ax.get_legend_handles_labels()
        fig.legend(
            handles,
            legend_labels,
            loc="lower center",
            ncol=4,
            frameon=True,
            fancybox=True,
            framealpha=1,
            edgecolor="#d8dadd",
            facecolor="#f8f9fa",
            fontsize=8.5,
            borderpad=0.7,
            handlelength=1.5,
            columnspacing=1.5,
        )
        fig.tight_layout(rect=[0, 0.1, 1, 1])
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
