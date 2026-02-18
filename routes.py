from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from forms import (
    CompanyDriveForm,
    CompanyProfileEditForm,
    CompanyRegistrationForm,
    LoginForm,
    StudentProfileEditForm,
    StudentRegistrationForm,
)
from init import db
from models import Application, CompanyProfile, JobPosition, Placement, StudentProfile, User

main = Blueprint("main", __name__)
ALLOWED_LOGIN_ROLES = {"admin", "student", "company"}
ROLE_DASHBOARD_ENDPOINTS = {
    "admin": "main.admin_dashboard",
    "student": "main.student_dashboard",
    "company": "main.company_dashboard",
}


def _redirect_to_dashboard_for(user):
    endpoint = ROLE_DASHBOARD_ENDPOINTS.get(user.user_role, "main.home")
    return redirect(url_for(endpoint))


def _require_role(expected_role):
    if current_user.user_role != expected_role:
        flash("You are not authorized to access that page.", "danger")
        return _redirect_to_dashboard_for(current_user)
    return None


def _admin_metrics():
    return {
        "students_total": StudentProfile.query.count(),
        "companies_total": CompanyProfile.query.count(),
        "applications_total": Application.query.count(),
        "drives_total": JobPosition.query.count(),
    }


def _admin_next_redirect(fallback_endpoint):
    next_path = (request.form.get("next") or "").strip()
    if next_path.startswith("/dashboard/admin"):
        return redirect(next_path)
    return redirect(url_for(fallback_endpoint))


def _student_profile_for_current_user():
    return StudentProfile.query.filter_by(user_id=current_user.user_id).first_or_404()


def _student_metrics(student_profile):
    applications_count = Application.query.filter_by(student_id=student_profile.student_id).count()
    placements_count = len(student_profile.placements)
    approved_drives_count = JobPosition.query.filter_by(status="approved", is_active=True).count()
    return {
        "approved_drives_total": approved_drives_count,
        "applied_drives_total": applications_count,
        "placements_total": placements_count,
    }


def _save_student_resume(resume_file, user_id):
    if not resume_file or not resume_file.filename:
        return None, None

    safe_name = secure_filename(resume_file.filename)
    if not safe_name:
        return None, None

    max_mb = int(current_app.config.get("RESUME_MAX_MB", 2))
    max_bytes = max_mb * 1024 * 1024
    try:
        resume_file.stream.seek(0, 2)
        file_size = resume_file.stream.tell()
        resume_file.stream.seek(0)
    except Exception:
        file_size = None
    if file_size is not None and file_size > max_bytes:
        return None, f"Resume must be {max_mb} MB or smaller."

    suffix = Path(safe_name).suffix.lower()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    final_name = f"student_{user_id}_{timestamp}{suffix}"
    upload_dir = Path(current_app.root_path) / "static" / "uploads" / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)
    resume_file.save(upload_dir / final_name)
    return final_name, None


def _company_profile_for_current_user():
    return CompanyProfile.query.filter_by(user_id=current_user.user_id).first_or_404()


def _company_metrics(company_profile):
    drives = JobPosition.query.filter_by(company_id=company_profile.company_id).all()
    drive_ids = [drive.job_id for drive in drives]
    applications_total = (
        Application.query.filter(Application.job_id.in_(drive_ids)).count() if drive_ids else 0
    )
    return {
        "drives_total": len(drives),
        "active_drives_total": sum(1 for drive in drives if drive.is_active and drive.status == "approved"),
        "applications_total": applications_total,
    }


def _company_next_redirect(fallback_endpoint, **kwargs):
    next_path = (request.form.get("next") or "").strip()
    if next_path.startswith("/dashboard/company"):
        return redirect(next_path)
    return redirect(url_for(fallback_endpoint, **kwargs))


@main.route("/")
def home():
    return render_template("home.html")


@main.route("/login", defaults={"role": None}, methods=["GET", "POST"])
@main.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if current_user.is_authenticated:
        return _redirect_to_dashboard_for(current_user)

    selected_role = (role or "").strip().lower() or None
    if selected_role and selected_role not in ALLOWED_LOGIN_ROLES:
        flash("Invalid login role selected.", "danger")
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email_address=email).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form, selected_role=selected_role)

        if not user.is_active:
            flash("Your account is inactive. Contact admin.", "warning")
            return render_template("login.html", form=form, selected_role=selected_role)

        if user.user_role != "admin" and not user.is_approved:
            flash("Your account is pending admin approval.", "warning")
            return render_template("login.html", form=form, selected_role=selected_role)

        if selected_role and user.user_role != selected_role:
            flash(f"This account is not registered as {selected_role}.", "danger")
            return render_template("login.html", form=form, selected_role=selected_role)

        login_user(user)
        flash("Login successful.", "success")
        return _redirect_to_dashboard_for(user)

    return render_template("login.html", form=form, selected_role=selected_role)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@main.route("/dashboard")
@login_required
def dashboard():
    return _redirect_to_dashboard_for(current_user)


@main.route("/dashboard/admin")
@login_required
def admin_dashboard():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    return render_template(
        "admin_dashboard.html",
        active_page="dashboard",
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/company-approvals")
@login_required
def admin_company_approvals():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    pending_company_users = (
        User.query.filter_by(user_role="company", is_approved=False)
        .order_by(User.created_at.desc())
        .all()
    )
    return render_template(
        "admin_company_approvals.html",
        active_page="company_approvals",
        pending_company_users=pending_company_users,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/drive-approvals")
@login_required
def admin_drive_approvals():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    pending_drives = (
        JobPosition.query.filter_by(status="pending")
        .order_by(JobPosition.created_at.desc())
        .all()
    )
    return render_template(
        "admin_drive_approvals.html",
        active_page="drive_approvals",
        pending_drives=pending_drives,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/drives")
@login_required
def admin_all_drives():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    drives = JobPosition.query.order_by(JobPosition.created_at.desc()).all()
    return render_template(
        "admin_all_drives.html",
        active_page="all_drives",
        drives=drives,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/applications")
@login_required
def admin_all_applications():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    applications = (
        Application.query.join(JobPosition)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template(
        "admin_applications.html",
        active_page="all_applications",
        applications=applications,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/placements")
@login_required
def admin_all_placements():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    placements = Placement.query.order_by(Placement.created_at.desc()).all()
    return render_template(
        "admin_placements.html",
        active_page="all_placements",
        placements=placements,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/search-students")
@login_required
def admin_student_search():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    student_query = (request.args.get("student_q") or "").strip()
    students_query = StudentProfile.query.join(User)
    if student_query:
        escaped = student_query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"{escaped}%"
        students_query = students_query.filter(
            or_(
                func.lower(User.user_name).like(like, escape="\\"),
                func.lower(StudentProfile.roll_number).like(like, escape="\\"),
                func.lower(User.contact_number).like(like, escape="\\"),
                func.lower(User.email_address).like(like, escape="\\"),
            )
        )
    students = students_query.order_by(StudentProfile.student_id.desc()).all()
    return render_template(
        "admin_student_search.html",
        active_page="search_students",
        students=students,
        student_query=student_query,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/search-companies")
@login_required
def admin_company_search():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    company_query = (request.args.get("company_q") or "").strip()
    companies_query = CompanyProfile.query.join(User)
    if company_query:
        escaped = company_query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"{escaped}%"
        companies_query = companies_query.filter(
            func.lower(CompanyProfile.company_name).like(like, escape="\\")
        )
    companies = companies_query.order_by(CompanyProfile.company_id.desc()).all()
    return render_template(
        "admin_company_search.html",
        active_page="search_companies",
        companies=companies,
        company_query=company_query,
        **_admin_metrics(),
    )


@main.post("/admin/company/<int:user_id>/approval")
@login_required
def admin_company_approval(user_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error

    action = (request.form.get("action") or "").strip().lower()
    company_user = User.query.filter_by(user_id=user_id, user_role="company").first_or_404()

    if action == "approve":
        company_user.is_approved = True
        flash("Company registration approved.", "success")
    elif action == "reject":
        company_user.is_approved = False
        company_user.is_active = False
        flash("Company registration rejected and account deactivated.", "warning")
    else:
        flash("Invalid action.", "danger")
        return _admin_next_redirect("main.admin_company_approvals")

    db.session.commit()
    return _admin_next_redirect("main.admin_company_approvals")


@main.post("/admin/drive/<int:job_id>/approval")
@login_required
def admin_drive_approval(job_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error

    action = (request.form.get("action") or "").strip().lower()
    drive = JobPosition.query.get_or_404(job_id)

    if action == "approve":
        drive.status = "approved"
        flash("Placement drive approved.", "success")
    elif action == "reject":
        drive.status = "rejected"
        flash("Placement drive rejected.", "warning")
    else:
        flash("Invalid action.", "danger")
        return _admin_next_redirect("main.admin_drive_approvals")

    db.session.commit()
    return _admin_next_redirect("main.admin_drive_approvals")


@main.post("/admin/user/<int:user_id>/status")
@login_required
def admin_user_status(user_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error

    action = (request.form.get("action") or "").strip().lower()
    target_user = User.query.filter(
        User.user_id == user_id,
        User.user_role.in_(["student", "company"]),
    ).first_or_404()

    if action == "deactivate":
        target_user.is_active = False
        flash(f"{target_user.user_role.capitalize()} account deactivated.", "warning")
    elif action == "activate":
        target_user.is_active = True
        flash(f"{target_user.user_role.capitalize()} account activated.", "success")
    else:
        flash("Invalid action.", "danger")
        return _admin_next_redirect("main.admin_dashboard")

    db.session.commit()
    return _admin_next_redirect("main.admin_dashboard")


@main.route("/dashboard/student")
@login_required
def student_dashboard():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile = _student_profile_for_current_user()
    return render_template(
        "student_dashboard.html",
        active_page="dashboard",
        student_profile=student_profile,
        **_student_metrics(student_profile),
    )


@main.route("/dashboard/student/drives")
@login_required
def student_drives():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile = _student_profile_for_current_user()
    approved_drives = (
        JobPosition.query.filter_by(status="approved", is_active=True)
        .order_by(JobPosition.created_at.desc())
        .all()
    )
    applied_job_ids = {
        app.job_id for app in Application.query.filter_by(student_id=student_profile.student_id).all()
    }
    return render_template(
        "student_drives.html",
        active_page="drives",
        student_profile=student_profile,
        drives=approved_drives,
        applied_job_ids=applied_job_ids,
        today=date.today(),
        **_student_metrics(student_profile),
    )


@main.post("/student/drives/<int:job_id>/apply")
@login_required
def student_apply_drive(job_id):
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile = _student_profile_for_current_user()
    drive = JobPosition.query.get_or_404(job_id)

    if drive.status != "approved" or not drive.is_active:
        flash("This placement drive is not open for applications.", "warning")
        return redirect(url_for("main.student_drives"))

    if drive.application_deadline and drive.application_deadline < date.today():
        flash("Application deadline has passed for this drive.", "warning")
        return redirect(url_for("main.student_drives"))

    existing = Application.query.filter_by(student_id=student_profile.student_id, job_id=job_id).first()
    if existing:
        flash("You have already applied for this placement drive.", "info")
        return redirect(url_for("main.student_drives"))

    application = Application(
        student_id=student_profile.student_id,
        job_id=job_id,
        status="applied",
        cover_letter=(request.form.get("cover_letter") or "").strip() or None,
    )
    db.session.add(application)

    try:
        db.session.commit()
        flash("Application submitted successfully.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("You have already applied for this placement drive.", "info")

    return redirect(url_for("main.student_drives"))


@main.route("/dashboard/student/applications")
@login_required
def student_applications():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile = _student_profile_for_current_user()
    applications = (
        Application.query.filter_by(student_id=student_profile.student_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template(
        "student_applications.html",
        active_page="applications",
        student_profile=student_profile,
        applications=applications,
        **_student_metrics(student_profile),
    )


@main.route("/dashboard/student/history")
@login_required
def student_history():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile = _student_profile_for_current_user()
    placements = (
        student_profile.placements
        if student_profile.placements
        else []
    )
    placements = sorted(placements, key=lambda item: item.offer_date or date.min, reverse=True)
    return render_template(
        "student_history.html",
        active_page="history",
        student_profile=student_profile,
        placements=placements,
        **_student_metrics(student_profile),
    )


@main.route("/dashboard/student/profile", methods=["GET", "POST"])
@login_required
def student_profile():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile_obj = _student_profile_for_current_user()
    form = StudentProfileEditForm()
    resume_max_mb = int(current_app.config.get("RESUME_MAX_MB", 2))

    if request.method == "GET":
        form.full_name.data = current_user.user_name
        form.contact_number.data = current_user.contact_number or ""
        form.address.data = current_user.address or ""
        form.course.data = student_profile_obj.course
        form.branch.data = student_profile_obj.branch
        form.graduation_year.data = student_profile_obj.graduation_year
        form.cgpa.data = student_profile_obj.cgpa
        form.skills.data = student_profile_obj.skills or ""

    if form.validate_on_submit():
        current_user.user_name = form.full_name.data.strip()
        current_user.contact_number = form.contact_number.data.strip()
        current_user.address = form.address.data.strip()
        student_profile_obj.course = form.course.data.strip()
        student_profile_obj.branch = form.branch.data.strip()
        student_profile_obj.graduation_year = form.graduation_year.data
        student_profile_obj.cgpa = form.cgpa.data
        student_profile_obj.skills = (form.skills.data or "").strip() or None

        resume_file = form.resume.data
        saved_resume, resume_error = _save_student_resume(resume_file, current_user.user_id)
        if resume_error:
            flash(resume_error, "danger")
            return render_template(
                "student_profile.html",
                active_page="profile",
                student_profile=student_profile_obj,
                form=form,
                resume_max_mb=resume_max_mb,
                **_student_metrics(student_profile_obj),
            )
        if saved_resume:
            student_profile_obj.resume_filename = saved_resume

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("main.student_profile"))

    return render_template(
        "student_profile.html",
        active_page="profile",
        student_profile=student_profile_obj,
        form=form,
        resume_max_mb=resume_max_mb,
        **_student_metrics(student_profile_obj),
    )


@main.route("/dashboard/company")
@login_required
def company_dashboard():
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile = _company_profile_for_current_user()
    drives = (
        JobPosition.query.filter_by(company_id=company_profile.company_id)
        .order_by(JobPosition.created_at.desc())
        .all()
    )
    drive_ids = [drive.job_id for drive in drives]
    applicant_counts = {}
    if drive_ids:
        for app in Application.query.filter(Application.job_id.in_(drive_ids)).all():
            applicant_counts[app.job_id] = applicant_counts.get(app.job_id, 0) + 1

    return render_template(
        "company_dashboard.html",
        active_page="dashboard",
        company_profile=company_profile,
        drives=drives,
        applicant_counts=applicant_counts,
        **_company_metrics(company_profile),
    )


@main.route("/dashboard/company/profile", methods=["GET", "POST"])
@login_required
def company_profile():
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile_obj = _company_profile_for_current_user()
    form = CompanyProfileEditForm()

    if request.method == "GET":
        form.company_name.data = company_profile_obj.company_name
        form.website.data = company_profile_obj.website or ""
        form.industry.data = company_profile_obj.industry or ""
        form.headquarters.data = company_profile_obj.headquarters or ""
        form.description.data = company_profile_obj.description or ""
        form.hr_name.data = company_profile_obj.hr_name or ""
        form.hr_email.data = company_profile_obj.hr_email or ""
        form.hr_phone.data = company_profile_obj.hr_phone or ""

    if form.validate_on_submit():
        existing = CompanyProfile.query.filter(
            CompanyProfile.company_name.ilike(form.company_name.data.strip()),
            CompanyProfile.company_id != company_profile_obj.company_id,
        ).first()
        if existing:
            flash("Company name already exists.", "danger")
            return render_template(
                "company_profile.html",
                active_page="profile",
                company_profile=company_profile_obj,
                form=form,
                **_company_metrics(company_profile_obj),
            )

        company_profile_obj.company_name = form.company_name.data.strip()
        company_profile_obj.website = (form.website.data or "").strip() or None
        company_profile_obj.industry = (form.industry.data or "").strip() or None
        company_profile_obj.headquarters = (form.headquarters.data or "").strip() or None
        company_profile_obj.description = (form.description.data or "").strip() or None
        company_profile_obj.hr_name = (form.hr_name.data or "").strip() or None
        company_profile_obj.hr_email = (form.hr_email.data or "").strip() or None
        company_profile_obj.hr_phone = (form.hr_phone.data or "").strip() or None

        db.session.commit()
        flash("Company profile updated successfully.", "success")
        return redirect(url_for("main.company_profile"))

    return render_template(
        "company_profile.html",
        active_page="profile",
        company_profile=company_profile_obj,
        form=form,
        **_company_metrics(company_profile_obj),
    )


@main.route("/dashboard/company/drives")
@login_required
def company_drives():
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile_obj = _company_profile_for_current_user()
    drives = (
        JobPosition.query.filter_by(company_id=company_profile_obj.company_id)
        .order_by(JobPosition.created_at.desc())
        .all()
    )
    applicant_counts = {}
    drive_ids = [drive.job_id for drive in drives]
    if drive_ids:
        for app in Application.query.filter(Application.job_id.in_(drive_ids)).all():
            applicant_counts[app.job_id] = applicant_counts.get(app.job_id, 0) + 1

    return render_template(
        "company_drives.html",
        active_page="drives",
        company_profile=company_profile_obj,
        drives=drives,
        applicant_counts=applicant_counts,
        **_company_metrics(company_profile_obj),
    )


@main.route("/dashboard/company/applications")
@login_required
def company_applications():
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile_obj = _company_profile_for_current_user()
    applications = (
        Application.query.join(JobPosition)
        .filter(JobPosition.company_id == company_profile_obj.company_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template(
        "company_applications.html",
        active_page="applications",
        company_profile=company_profile_obj,
        applications=applications,
        **_company_metrics(company_profile_obj),
    )


@main.route("/dashboard/company/drives/create", methods=["GET", "POST"])
@login_required
def company_create_drive():
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    if not current_user.is_approved:
        flash("Drive creation is available only after admin approval.", "warning")
        return redirect(url_for("main.company_dashboard"))

    company_profile_obj = _company_profile_for_current_user()
    form = CompanyDriveForm()
    if form.validate_on_submit():
        drive = JobPosition(
            company_id=company_profile_obj.company_id,
            title=form.title.data.strip(),
            job_type=form.job_type.data,
            location=(form.location.data or "").strip() or None,
            salary_lpa=form.salary_lpa.data,
            openings=form.openings.data,
            min_cgpa=form.min_cgpa.data,
            eligible_branches=(form.eligible_branches.data or "").strip() or None,
            description=(form.description.data or "").strip() or None,
            application_deadline=form.application_deadline.data,
            status="pending",
            is_active=True,
        )
        db.session.add(drive)
        db.session.commit()
        flash("Placement drive created and submitted for admin approval.", "success")
        return redirect(url_for("main.company_drives"))

    return render_template(
        "company_drive_form.html",
        active_page="drives",
        company_profile=company_profile_obj,
        form=form,
        form_title="Create Placement Drive",
        **_company_metrics(company_profile_obj),
    )


@main.route("/dashboard/company/drives/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def company_edit_drive(job_id):
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile_obj = _company_profile_for_current_user()
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=company_profile_obj.company_id).first_or_404()

    form = CompanyDriveForm()
    if request.method == "GET":
        form.title.data = drive.title
        form.job_type.data = drive.job_type
        form.location.data = drive.location or ""
        form.salary_lpa.data = drive.salary_lpa
        form.openings.data = drive.openings
        form.min_cgpa.data = drive.min_cgpa
        form.eligible_branches.data = drive.eligible_branches or ""
        form.description.data = drive.description or ""
        form.application_deadline.data = drive.application_deadline

    if form.validate_on_submit():
        drive.title = form.title.data.strip()
        drive.job_type = form.job_type.data
        drive.location = (form.location.data or "").strip() or None
        drive.salary_lpa = form.salary_lpa.data
        drive.openings = form.openings.data
        drive.min_cgpa = form.min_cgpa.data
        drive.eligible_branches = (form.eligible_branches.data or "").strip() or None
        drive.description = (form.description.data or "").strip() or None
        drive.application_deadline = form.application_deadline.data
        if drive.status == "rejected":
            drive.status = "pending"
        db.session.commit()
        flash("Placement drive updated successfully.", "success")
        return redirect(url_for("main.company_drives"))

    return render_template(
        "company_drive_form.html",
        active_page="drives",
        company_profile=company_profile_obj,
        form=form,
        form_title=f"Edit Drive #{drive.job_id}",
        **_company_metrics(company_profile_obj),
    )


@main.post("/dashboard/company/drives/<int:job_id>/close")
@login_required
def company_close_drive(job_id):
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile_obj = _company_profile_for_current_user()
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=company_profile_obj.company_id).first_or_404()
    drive.is_active = False
    if drive.status == "approved":
        drive.status = "closed"
    db.session.commit()
    flash("Placement drive closed.", "warning")
    return _company_next_redirect("main.company_drives")


@main.post("/dashboard/company/drives/<int:job_id>/delete")
@login_required
def company_delete_drive(job_id):
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile_obj = _company_profile_for_current_user()
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=company_profile_obj.company_id).first_or_404()
    # Keep historical application/placement records intact.
    drive.is_active = False
    drive.status = "closed"
    db.session.commit()
    flash("Placement drive removed from active listings.", "warning")
    return _company_next_redirect("main.company_drives")


@main.route("/dashboard/company/drives/<int:job_id>/applications")
@login_required
def company_drive_applications(job_id):
    auth_error = _require_role("company")
    if auth_error:
        return auth_error
    company_profile_obj = _company_profile_for_current_user()
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=company_profile_obj.company_id).first_or_404()
    applications = (
        Application.query.filter_by(job_id=drive.job_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template(
        "company_drive_applications.html",
        active_page="drives",
        company_profile=company_profile_obj,
        drive=drive,
        applications=applications,
        **_company_metrics(company_profile_obj),
    )


@main.post("/dashboard/company/applications/<int:application_id>/status")
@login_required
def company_update_application_status(application_id):
    auth_error = _require_role("company")
    if auth_error:
        return auth_error

    company_profile_obj = _company_profile_for_current_user()
    application = (
        Application.query.join(JobPosition)
        .filter(
            Application.application_id == application_id,
            JobPosition.company_id == company_profile_obj.company_id,
        )
        .first_or_404()
    )

    action = (request.form.get("action") or "").strip().lower()
    if action not in {"shortlisted", "selected", "rejected"}:
        flash("Invalid application status.", "danger")
        return _company_next_redirect("main.company_drive_applications", job_id=application.job_id)

    application.status = action

    placement = Placement.query.filter_by(application_id=application.application_id).first()
    if action == "selected":
        if not placement:
            placement = Placement(
                application_id=application.application_id,
                student_id=application.student_id,
                company_id=company_profile_obj.company_id,
                job_id=application.job_id,
                offered_package_lpa=application.job_position.salary_lpa,
                offer_date=date.today(),
                placement_status="offered",
            )
            db.session.add(placement)
    elif placement:
        db.session.delete(placement)

    db.session.commit()
    flash(f"Application marked as {action}.", "success")
    return _company_next_redirect("main.company_drive_applications", job_id=application.job_id)


@main.route("/register/student", methods=["GET", "POST"])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = StudentRegistrationForm()
    if form.validate_on_submit():
        full_name = " ".join(
            part.strip()
            for part in [form.first_name.data, form.middle_name.data, form.last_name.data]
            if part and part.strip()
        )
        address_parts = [
            form.address_line1.data,
            form.address_line2.data,
            form.landmark.data,
            f"{form.city.data}, {form.state.data}, {form.country.data} {form.pincode.data}",
        ]
        student_user = User(
            user_name=full_name,
            email_address=form.email_address.data.strip().lower(),
            contact_number=(form.contact_number.data or "").strip() or None,
            address="\n".join(part.strip() for part in address_parts if part and part.strip()),
            gender=form.gender.data or None,
            dob=form.dob.data,
            user_role="student",
            is_active=True,
            is_approved=True,
        )
        student_user.set_password(form.password.data)

        student_profile = StudentProfile(
            user=student_user,
            roll_number=form.roll_number.data.strip().upper(),
            course=form.course.data.strip(),
            branch=form.branch.data.strip(),
            graduation_year=form.graduation_year.data,
            cgpa=form.cgpa.data,
            skills=(form.skills.data or "").strip() or None,
        )

        db.session.add(student_user)
        db.session.add(student_profile)

        try:
            db.session.commit()
            flash("Student registration successful. Please login.", "success")
            return redirect(url_for("main.login", role="student"))
        except IntegrityError:
            db.session.rollback()
            flash("Registration failed due to duplicate data. Please recheck form values.", "danger")

    return render_template("register_student.html", form=form)


@main.route("/register/company", methods=["GET", "POST"])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        company_name = form.company_name.data.strip()
        address_parts = [
            form.address_line1.data,
            form.address_line2.data,
            form.landmark.data,
            f"{form.city.data}, {form.state.data}, {form.country.data} {form.pincode.data}",
        ]
        company_user = User(
            user_name=company_name,
            email_address=form.email_address.data.strip().lower(),
            contact_number=(form.contact_number.data or "").strip() or None,
            address="\n".join(part.strip() for part in address_parts if part and part.strip()),
            gender=None,
            dob=None,
            user_role="company",
            is_active=True,
            is_approved=False,
        )
        company_user.set_password(form.password.data)

        company_profile = CompanyProfile(
            user=company_user,
            company_name=company_name,
            website=(form.website.data or "").strip() or None,
            industry=(form.industry.data or "").strip() or None,
            description=(form.description.data or "").strip() or None,
            headquarters=(form.headquarters.data or "").strip() or None,
            hr_name=(form.hr_name.data or "").strip() or None,
            hr_email=(form.hr_email.data or "").strip() or None,
            hr_phone=(form.hr_phone.data or "").strip() or None,
        )

        db.session.add(company_user)
        db.session.add(company_profile)

        try:
            db.session.commit()
            flash("Company registration submitted. Wait for admin approval.", "success")
            return redirect(url_for("main.login", role="company"))
        except IntegrityError:
            db.session.rollback()
            flash("Registration failed due to duplicate data. Please recheck form values.", "danger")

    return render_template("register_company.html", form=form)
