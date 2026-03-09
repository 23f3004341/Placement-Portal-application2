import base64
import io
import os
from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / "data" / ".matplotlib"))
import matplotlib
from sqlalchemy import case, func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from forms import (
    CompanyAdminEditForm,
    CompanyDriveForm,
    CompanyProfileEditForm,
    CompanyRegistrationForm,
    LoginForm,
    StudentFullProfileEditForm,
    StudentRegistrationForm,
)
from init import db
from models import AccountRestriction, Application, CompanyProfile, JobPosition, Placement, StudentProfile, User

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


def _admin_placement_stats():
    by_status = dict(
        db.session.query(Placement.placement_status, func.count(Placement.placement_id))
        .group_by(Placement.placement_status)
        .all()
    )
    by_application_status = dict(
        db.session.query(Application.status, func.count(Application.application_id))
        .group_by(Application.status)
        .all()
    )
    by_month_rows = (
        db.session.query(
            func.strftime("%Y-%m", Placement.created_at).label("month_key"),
            func.count(Placement.placement_id),
        )
        .group_by("month_key")
        .order_by("month_key")
        .all()
    )
    by_month = [{"month": row[0], "count": row[1]} for row in by_month_rows if row[0]]
    drive_outcome_rows = (
        db.session.query(
            JobPosition.job_id,
            JobPosition.title,
            CompanyProfile.company_name,
            func.sum(case((Application.status == "shortlisted", 1), else_=0)).label("shortlisted"),
            func.sum(case((Application.status == "selected", 1), else_=0)).label("selected"),
            func.sum(case((Application.status == "rejected", 1), else_=0)).label("rejected"),
        )
        .join(CompanyProfile, CompanyProfile.company_id == JobPosition.company_id)
        .outerjoin(Application, Application.job_id == JobPosition.job_id)
        .group_by(JobPosition.job_id, JobPosition.title, CompanyProfile.company_name)
        .order_by(JobPosition.job_id.asc())
        .all()
    )
    drive_outcomes = [
        {
            "job_id": row[0],
            "title": row[1],
            "company_name": row[2],
            "shortlisted": int(row[3] or 0),
            "selected": int(row[4] or 0),
            "rejected": int(row[5] or 0),
        }
        for row in drive_outcome_rows
    ]
    return {
        "placement_status_counts": by_status,
        "application_status_counts": by_application_status,
        "placements_by_month": by_month,
        "drive_outcomes": drive_outcomes,
    }


def _fig_to_base64(figure):
    buffer = io.BytesIO()
    figure.tight_layout()
    figure.savefig(buffer, format="png", dpi=120)
    plt.close(figure)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")


def _build_pie_chart_image(
    labels,
    values,
    title,
    colors,
    show_legend=False,
    legend_loc="upper right",
):
    figure, axis = plt.subplots(figsize=(4.4, 3.4))
    if sum(values) > 0:
        pie_labels = None if show_legend else labels
        axis.pie(
            values,
            labels=pie_labels,
            autopct=lambda pct: f"{pct:.0f}%" if pct > 0 else "",
            startangle=90,
            colors=colors,
        )
        if show_legend:
            legend_handles = [
                Patch(facecolor=colors[index % len(colors)], edgecolor="none", label=label)
                for index, label in enumerate(labels)
            ]
            axis.legend(
                handles=legend_handles,
                loc=legend_loc,
                fontsize=8,
                frameon=True,
                framealpha=0.95,
                borderpad=0.4,
                handlelength=0.9,
                handletextpad=0.4,
                labelspacing=0.3,
            )
        axis.axis("equal")
    else:
        axis.text(0.5, 0.5, "No data available", ha="center", va="center")
        axis.axis("off")
    axis.set_title(title)
    return _fig_to_base64(figure)


def _build_bar_chart_image(labels, values, title):
    figure, axis = plt.subplots(figsize=(8, 2.8))
    if values:
        axis.bar(labels, values, color="#4f79ab")
        axis.set_ylabel("Count")
        axis.tick_params(axis="x", rotation=25)
        axis.grid(axis="y", linestyle="--", alpha=0.35)
    else:
        axis.text(0.5, 0.5, "No data available", ha="center", va="center")
        axis.axis("off")
    axis.set_title(title)
    return _fig_to_base64(figure)


def _build_drive_outcomes_chart_image(outcomes):
    labels = [f"{item['company_name']} | {item['title']}" for item in outcomes]
    shortlisted = [item["shortlisted"] for item in outcomes]
    selected = [item["selected"] for item in outcomes]
    rejected = [item["rejected"] for item in outcomes]

    figure_height = max(3.2, 1.0 + len(labels) * 0.55)
    figure, axis = plt.subplots(figsize=(10.5, figure_height))
    if labels:
        positions = list(range(len(labels)))
        axis.barh(positions, shortlisted, color="#fdd49e", label="Shortlisted")
        axis.barh(positions, selected, left=shortlisted, color="#a1d99b", label="Selected (Placed)")
        left_for_rejected = [shortlisted[i] + selected[i] for i in positions]
        axis.barh(positions, rejected, left=left_for_rejected, color="#fdae6b", label="Rejected")
        totals = [shortlisted[i] + selected[i] + rejected[i] for i in positions]
        for idx, total in enumerate(totals):
            axis.text(total + 0.05, idx, str(total), va="center", fontsize=8, color="#3b4f6a")
        axis.set_yticks(positions)
        axis.set_yticklabels(labels, fontsize=8)
        axis.set_xlabel("Students")
        axis.grid(axis="x", linestyle="--", alpha=0.35)
        axis.legend(loc="lower right", fontsize=8)
        axis.invert_yaxis()
    else:
        axis.text(0.5, 0.5, "No drives available", ha="center", va="center")
        axis.axis("off")
    axis.set_title("Drive Outcomes by Company and Role")
    return _fig_to_base64(figure)


def _admin_chart_images(stats):
    application_status = stats["application_status_counts"]
    drive_outcomes = stats["drive_outcomes"]
    status_order = ["applied", "selected", "shortlisted", "withdrawn", "rejected"]
    status_colors = {
        "applied": "#4f8bd6",     
        "selected": "#a8d68ec4",     
        "shortlisted": "#f2c84cd6",  
        "withdrawn": "#c0c0c0",    
        "rejected": "#e74c3c",     
    }
    labels = status_order
    values = [application_status.get(status, 0) for status in labels]
    colors = [status_colors[status] for status in labels]
    return {
        "application_status_chart": _build_pie_chart_image(
            labels,
            values,
            "Application Status",
            colors,
            show_legend=True,
            legend_loc="upper right",
        ),
        "drive_outcomes_chart": _build_drive_outcomes_chart_image(drive_outcomes),
    }


def _admin_next_redirect(fallback_endpoint):
    next_path = (request.form.get("next") or "").strip()
    if next_path.startswith("/dashboard/admin"):
        return redirect(next_path)
    return redirect(url_for(fallback_endpoint))


def _student_profile_for_current_user():
    return StudentProfile.query.filter_by(user_id=current_user.user_id).first_or_404()


def _next_student_roll_number():
    assigned_rolls = db.session.query(StudentProfile.roll_number).all()
    numeric_rolls = []
    for (roll_number,) in assigned_rolls:
        roll_text = (roll_number or "").strip()
        if roll_text.isdigit():
            numeric_rolls.append(int(roll_text))
    max_assigned = max(numeric_rolls, default=1000)
    return str(max_assigned + 1)


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
        Application.query.filter(
            Application.job_id.in_(drive_ids),
            Application.status != "withdrawn",
        ).count()
        if drive_ids
        else 0
    )
    return {
        "drives_total": len(drives),
        "active_drives_total": sum(1 for drive in drives if drive.is_active and drive.status == "approved"),
        "applications_total": applications_total,
    }


def _company_chart_images(company_profile):
    drive_status_rows = (
        db.session.query(JobPosition.status, func.count(JobPosition.job_id))
        .filter(JobPosition.company_id == company_profile.company_id)
        .group_by(JobPosition.status)
        .all()
    )
    app_status_rows = (
        db.session.query(Application.status, func.count(Application.application_id))
        .join(JobPosition, Application.job_id == JobPosition.job_id)
        .filter(
            JobPosition.company_id == company_profile.company_id,
            Application.status != "withdrawn",
        )
        .group_by(Application.status)
        .all()
    )
    drive_status_counts = {row[0]: row[1] for row in drive_status_rows}
    app_status_counts = {row[0]: row[1] for row in app_status_rows}

    drive_status_order = ["approved", "pending", "rejected", "closed"]
    application_status_order = ["applied", "shortlisted", "selected", "rejected"]
    return {
        "company_drive_status_chart": _build_pie_chart_image(
            drive_status_order,
            [drive_status_counts.get(status, 0) for status in drive_status_order],
            "Drive Status Distribution",
            ["#8dd3c7", "#80b1d3", "#fdb462", "#fb8072"],
            show_legend=True,
            legend_loc="upper right",
        ),
        "company_application_status_chart": _build_pie_chart_image(
            application_status_order,
            [app_status_counts.get(status, 0) for status in application_status_order],
            "Applicant Progress",
            ["#9ecae1", "#fdd49e", "#a1d99b", "#fdae6b", "#dadaeb"],
            show_legend=True,
            legend_loc="upper right",
        ),
    }


def _company_next_redirect(fallback_endpoint, **kwargs):
    next_path = (request.form.get("next") or "").strip()
    if next_path.startswith("/dashboard/company"):
        return redirect(next_path)
    return redirect(url_for(fallback_endpoint, **kwargs))


def _selected_placement_statuses():
    return {"offered", "accepted", "joined"}


def _existing_company_selection(student_id, company_id, exclude_application_id=None):
    query = Placement.query.filter(
        Placement.student_id == student_id,
        Placement.company_id == company_id,
        Placement.placement_status.in_(_selected_placement_statuses()),
    )
    if exclude_application_id is not None:
        query = query.filter(Placement.application_id != exclude_application_id)
    return query.first()


def _reject_other_company_applications(student_id, company_id, selected_application_id):
    other_apps = (
        Application.query.join(JobPosition)
        .filter(
            Application.student_id == student_id,
            JobPosition.company_id == company_id,
            Application.application_id != selected_application_id,
        )
        .all()
    )
    for other_app in other_apps:
        other_app.status = "rejected"
        other_placement = Placement.query.filter_by(application_id=other_app.application_id).first()
        if other_placement:
            db.session.delete(other_placement)


def _status_locked_for_progression(current_status):
    return (current_status or "").strip().lower() in {"selected", "rejected", "withdrawn"}


def _set_account_restriction(email_address, reason):
    email = (email_address or "").strip().lower()
    if not email:
        return
    row = AccountRestriction.query.filter_by(email_address=email).first()
    if row:
        row.reason = reason
    else:
        row = AccountRestriction(email_address=email, reason=reason)
        db.session.add(row)


def _clear_account_restriction(email_address):
    email = (email_address or "").strip().lower()
    if not email:
        return
    row = AccountRestriction.query.filter_by(email_address=email).first()
    if row:
        db.session.delete(row)


def _restriction_reason_map(emails):
    cleaned = [email.strip().lower() for email in emails if email]
    if not cleaned:
        return {}
    rows = AccountRestriction.query.filter(AccountRestriction.email_address.in_(cleaned)).all()
    return {row.email_address: row.reason for row in rows}


def _join_multi_select(values):
    cleaned = [value.strip() for value in (values or []) if value and value.strip()]
    return ",".join(cleaned) if cleaned else None


def _split_multi_select(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_full_name(full_name):
    parts = [part for part in (full_name or "").strip().split() if part]
    if not parts:
        return "", "", ""
    if len(parts) == 1:
        return parts[0], "", ""
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]


def _split_stored_address(address_text):
    lines = [line.strip() for line in (address_text or "").splitlines() if line.strip()]
    parsed = {
        "address_line1": lines[0] if lines else "",
        "address_line2": "",
        "landmark": "",
        "city": "",
        "state": "",
        "country": "",
        "pincode": "",
    }
    if not lines:
        return parsed

    location_line = lines[-1] if "," in lines[-1] else ""
    detail_lines = lines[:-1] if location_line else lines
    if len(detail_lines) > 1:
        parsed["address_line2"] = detail_lines[1]
    if len(detail_lines) > 2:
        parsed["landmark"] = detail_lines[2]

    if location_line:
        city_state_country = [item.strip() for item in location_line.split(",")]
        if len(city_state_country) >= 3:
            parsed["city"] = city_state_country[0]
            parsed["state"] = city_state_country[1]
            country_pin = city_state_country[2]
            country_parts = country_pin.rsplit(" ", 1)
            if len(country_parts) == 2 and country_parts[1].isdigit() and len(country_parts[1]) == 6:
                parsed["country"] = country_parts[0].strip()
                parsed["pincode"] = country_parts[1].strip()
            else:
                parsed["country"] = country_pin
    return parsed


def _student_meets_drive_eligibility(student_profile, drive):
    eligible_degrees = {item.casefold() for item in _split_multi_select(drive.eligible_degrees)}
    eligible_branches = {item.casefold() for item in _split_multi_select(drive.eligible_branches)}
    student_degree = (student_profile.course or "").strip().casefold()
    student_branch = (student_profile.branch or "").strip().casefold()

    if eligible_degrees and student_degree not in eligible_degrees:
        return False
    if eligible_branches and student_branch not in eligible_branches:
        return False
    return True


def _student_meets_drive_cgpa(student_profile, drive):
    if drive.min_cgpa is None:
        return True
    if student_profile.cgpa is None:
        return False
    return float(student_profile.cgpa) >= float(drive.min_cgpa)


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
        restriction = AccountRestriction.query.filter_by(email_address=email).first()
        if restriction:
            if restriction.reason == "removed":
                flash("You were removed by the admin.", "danger")
            elif restriction.reason == "blacklisted":
                flash("You were blacklisted by the admin.", "danger")
            else:
                flash("Your account is restricted.", "danger")
            return render_template("login.html", form=form, selected_role=selected_role)
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
    stats = _admin_placement_stats()
    return render_template(
        "admin_dashboard.html",
        active_page="dashboard",
        **_admin_metrics(),
        **_admin_chart_images(stats),
    )


@main.route("/dashboard/admin/company-approvals")
@login_required
def admin_company_approvals():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    company_query = (request.args.get("company_q") or "").strip()
    pending_companies = (
        CompanyProfile.query.join(User)
        .filter(User.user_role == "company", User.is_approved.is_(False), User.is_active.is_(True))
        .order_by(CompanyProfile.company_id.asc())
        .all()
    )
    reviewed_query = CompanyProfile.query.join(User).filter(
        User.user_role == "company",
        or_(User.is_approved.is_(True), User.is_active.is_(False)),
    )
    if company_query:
        escaped = company_query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"{escaped}%"
        reviewed_query = reviewed_query.filter(
            func.lower(CompanyProfile.company_name).like(like, escape="\\")
        )
    reviewed_companies = reviewed_query.order_by(CompanyProfile.company_id.asc()).all()
    return render_template(
        "admin_company_approvals.html",
        active_page="company_approvals",
        pending_companies=pending_companies,
        reviewed_companies=reviewed_companies,
        company_query=company_query,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/company-approvals/<int:user_id>")
@login_required
def admin_company_approval_detail(user_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    company_user = User.query.filter_by(user_id=user_id, user_role="company").first_or_404()
    company_profile_obj = CompanyProfile.query.filter_by(user_id=company_user.user_id).first_or_404()
    return render_template(
        "admin_company_approval_detail.html",
        active_page="company_approvals",
        company_user=company_user,
        company_profile=company_profile_obj,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/drive-approvals")
@login_required
def admin_drive_approvals():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    return redirect(url_for("main.admin_all_drives"))


@main.route("/dashboard/admin/drives")
@login_required
def admin_all_drives():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    drives = JobPosition.query.order_by(JobPosition.job_id.asc()).all()
    return render_template(
        "admin_all_drives.html",
        active_page="all_drives",
        drives=drives,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/drives/<int:job_id>")
@login_required
def admin_drive_detail(job_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    drive = JobPosition.query.get_or_404(job_id)
    applicant_count = Application.query.filter_by(job_id=drive.job_id).count()
    return render_template(
        "admin_drive_detail.html",
        active_page="all_drives",
        drive=drive,
        applicant_count=applicant_count,
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
        .order_by(Application.application_id.asc())
        .all()
    )
    placements = Placement.query.order_by(Placement.placement_id.asc()).all()
    return render_template(
        "admin_applications.html",
        active_page="applications_placements",
        applications=applications,
        placements=placements,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/placements")
@login_required
def admin_all_placements():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    return redirect(url_for("main.admin_all_applications"))


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
            )
        )
    students = students_query.order_by(StudentProfile.student_id.asc()).all()
    restriction_reasons = _restriction_reason_map([student.user.email_address for student in students])
    return render_template(
        "admin_student_search.html",
        active_page="search_students",
        students=students,
        student_query=student_query,
        restriction_reasons=restriction_reasons,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/students/<int:student_id>")
@login_required
def admin_student_profile_view(student_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    student_profile_obj = StudentProfile.query.get_or_404(student_id)
    applications = (
        Application.query.filter_by(student_id=student_profile_obj.student_id)
        .order_by(Application.application_id.asc())
        .all()
    )
    placements = (
        Placement.query.filter_by(student_id=student_profile_obj.student_id)
        .order_by(Placement.placement_id.asc())
        .all()
    )
    return render_template(
        "admin_student_profile_view.html",
        active_page="search_students",
        student_profile=student_profile_obj,
        applications=applications,
        placements=placements,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/search-companies")
@login_required
def admin_company_search():
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error
    company_query = (request.args.get("company_q") or "").strip()
    if company_query:
        return redirect(url_for("main.admin_company_approvals", company_q=company_query))
    return redirect(url_for("main.admin_company_approvals"))


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
        return _admin_next_redirect("main.admin_all_drives")

    db.session.commit()
    return _admin_next_redirect("main.admin_all_drives")


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

    if action in {"deactivate", "blacklist"}:
        target_user.is_active = False
        _set_account_restriction(target_user.email_address, "blacklisted")
        flash(f"{target_user.user_role.capitalize()} account blacklisted.", "warning")
    elif action == "activate":
        target_user.is_active = True
        _clear_account_restriction(target_user.email_address)
        flash(f"{target_user.user_role.capitalize()} account activated.", "success")
    else:
        flash("Invalid action.", "danger")
        return _admin_next_redirect("main.admin_dashboard")

    db.session.commit()
    return _admin_next_redirect("main.admin_dashboard")


@main.post("/admin/user/<int:user_id>/delete")
@login_required
def admin_user_delete(user_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error

    target_user = User.query.filter(
        User.user_id == user_id,
        User.user_role.in_(["student", "company"]),
    ).first_or_404()
    target_email = target_user.email_address
    target_role = target_user.user_role
    db.session.delete(target_user)
    _set_account_restriction(target_email, "removed")
    db.session.commit()
    flash(f"{target_role.capitalize()} removed successfully.", "warning")
    return _admin_next_redirect("main.admin_dashboard")


@main.route("/dashboard/admin/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_student(student_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error

    student_profile_obj = StudentProfile.query.get_or_404(student_id)
    form = StudentFullProfileEditForm(original_email=student_profile_obj.user.email_address)
    resume_max_mb = int(current_app.config.get("RESUME_MAX_MB", 2))

    if request.method == "GET":
        first_name, middle_name, last_name = _split_full_name(student_profile_obj.user.user_name)
        parsed_address = _split_stored_address(student_profile_obj.user.address)
        form.first_name.data = first_name
        form.middle_name.data = middle_name
        form.last_name.data = last_name
        form.email_address.data = student_profile_obj.user.email_address
        form.contact_number.data = student_profile_obj.user.contact_number or ""
        form.address_line1.data = parsed_address["address_line1"]
        form.address_line2.data = parsed_address["address_line2"]
        form.landmark.data = parsed_address["landmark"]
        form.city.data = parsed_address["city"]
        form.state.data = parsed_address["state"]
        form.country.data = parsed_address["country"]
        form.pincode.data = parsed_address["pincode"]
        form.gender.data = student_profile_obj.user.gender or ""
        form.dob.data = student_profile_obj.user.dob
        form.course.data = student_profile_obj.course
        form.branch.data = student_profile_obj.branch
        form.graduation_year.data = student_profile_obj.graduation_year
        form.cgpa.data = student_profile_obj.cgpa

    if form.validate_on_submit():
        student_profile_obj.user.user_name = " ".join(
            part.strip()
            for part in [form.first_name.data, form.middle_name.data, form.last_name.data]
            if part and part.strip()
        )
        student_profile_obj.user.email_address = form.email_address.data.strip().lower()
        student_profile_obj.user.contact_number = form.contact_number.data.strip()
        address_parts = [
            form.address_line1.data,
            form.address_line2.data,
            form.landmark.data,
            f"{form.city.data}, {form.state.data}, {form.country.data} {form.pincode.data}",
        ]
        student_profile_obj.user.address = "\n".join(
            part.strip() for part in address_parts if part and part.strip()
        )
        student_profile_obj.user.gender = form.gender.data or None
        student_profile_obj.user.dob = form.dob.data
        if form.password.data:
            student_profile_obj.user.set_password(form.password.data)
        student_profile_obj.course = form.course.data.strip()
        student_profile_obj.branch = form.branch.data.strip()
        student_profile_obj.graduation_year = form.graduation_year.data
        student_profile_obj.cgpa = form.cgpa.data

        resume_file = form.resume.data
        saved_resume, resume_error = _save_student_resume(resume_file, student_profile_obj.user.user_id)
        if resume_error:
            flash(resume_error, "danger")
            return render_template(
                "admin_edit_student.html",
                active_page="search_students",
                form=form,
                student_profile=student_profile_obj,
                resume_max_mb=resume_max_mb,
                **_admin_metrics(),
            )
        if saved_resume:
            student_profile_obj.resume_filename = saved_resume

        db.session.commit()
        flash("Student details updated successfully.", "success")
        return redirect(url_for("main.admin_student_search"))

    return render_template(
        "admin_edit_student.html",
        active_page="search_students",
        form=form,
        student_profile=student_profile_obj,
        resume_max_mb=resume_max_mb,
        **_admin_metrics(),
    )


@main.route("/dashboard/admin/companies/<int:company_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_company(company_id):
    auth_error = _require_role("admin")
    if auth_error:
        return auth_error

    company_profile_obj = CompanyProfile.query.get_or_404(company_id)
    form = CompanyAdminEditForm(
        original_email=company_profile_obj.user.email_address,
        original_company_name=company_profile_obj.company_name,
    )

    if request.method == "GET":
        parsed_address = _split_stored_address(company_profile_obj.user.address)
        form.company_name.data = company_profile_obj.company_name
        form.email_address.data = company_profile_obj.user.email_address
        form.website.data = company_profile_obj.website or ""
        form.industry.data = company_profile_obj.industry or ""
        form.headquarters.data = company_profile_obj.headquarters or ""
        form.description.data = company_profile_obj.description or ""
        form.hr_name.data = company_profile_obj.hr_name or ""
        form.hr_email.data = company_profile_obj.hr_email or ""
        form.hr_phone.data = company_profile_obj.hr_phone or ""
        form.address_line1.data = parsed_address["address_line1"]
        form.address_line2.data = parsed_address["address_line2"]
        form.landmark.data = parsed_address["landmark"]
        form.city.data = parsed_address["city"]
        form.state.data = parsed_address["state"]
        form.country.data = parsed_address["country"]
        form.pincode.data = parsed_address["pincode"]

    if form.validate_on_submit():
        address_parts = [
            form.address_line1.data,
            form.address_line2.data,
            form.landmark.data,
            f"{form.city.data}, {form.state.data}, {form.country.data} {form.pincode.data}",
        ]
        company_profile_obj.user.address = "\n".join(part.strip() for part in address_parts if part and part.strip())
        company_profile_obj.user.email_address = form.email_address.data.strip().lower()
        company_profile_obj.company_name = form.company_name.data.strip()
        company_profile_obj.website = (form.website.data or "").strip() or None
        company_profile_obj.industry = (form.industry.data or "").strip() or None
        company_profile_obj.headquarters = (form.headquarters.data or "").strip() or None
        company_profile_obj.description = (form.description.data or "").strip() or None
        company_profile_obj.hr_name = (form.hr_name.data or "").strip() or None
        company_profile_obj.hr_email = (form.hr_email.data or "").strip() or None
        company_profile_obj.hr_phone = (form.hr_phone.data or "").strip() or None
        db.session.commit()
        flash("Company details updated successfully.", "success")
        return redirect(url_for("main.admin_company_approvals"))

    return render_template(
        "admin_edit_company.html",
        active_page="company_approvals",
        form=form,
        company_profile=company_profile_obj,
        **_admin_metrics(),
    )


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
        .order_by(JobPosition.job_id.asc())
        .all()
    )
    student_apps = Application.query.filter_by(student_id=student_profile.student_id).all()
    application_meta_by_job = {
        app.job_id: {"application_id": app.application_id, "status": app.status}
        for app in student_apps
    }
    return render_template(
        "student_drives.html",
        active_page="drives",
        student_profile=student_profile,
        drives=approved_drives,
        application_meta_by_job=application_meta_by_job,
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
    if not _student_meets_drive_cgpa(student_profile, drive):
        flash("CGPA Criteria Not fulfilled", "danger")
        return redirect(url_for("main.student_drives"))
    if not _student_meets_drive_eligibility(student_profile, drive):
        flash("Your degree/branch is not eligible for this drive.", "danger")
        return redirect(url_for("main.student_drives"))
    if _existing_company_selection(student_profile.student_id, drive.company_id):
        flash("You are already selected for another role in this company.", "warning")
        return redirect(url_for("main.student_drives"))

    existing = Application.query.filter_by(student_id=student_profile.student_id, job_id=job_id).first()
    if existing:
        if existing.status == "withdrawn":
            existing.status = "applied"
            existing.applied_at = datetime.utcnow()
            existing.cover_letter = (request.form.get("cover_letter") or "").strip() or None
            db.session.commit()
            flash("Application submitted successfully.", "success")
            return redirect(url_for("main.student_drives"))
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


@main.post("/student/applications/<int:application_id>/withdraw")
@login_required
def student_withdraw_application(application_id):
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile = _student_profile_for_current_user()
    application = Application.query.filter_by(
        application_id=application_id,
        student_id=student_profile.student_id,
    ).first_or_404()

    if application.status in {"shortlisted", "selected", "rejected"}:
        flash("Cannot undo application after company has updated the status.", "warning")
    elif application.status == "withdrawn":
        flash("Application is already withdrawn.", "info")
    else:
        application.status = "withdrawn"
        db.session.commit()
        flash("Application undone successfully.", "success")

    next_path = (request.form.get("next") or "").strip()
    if next_path.startswith("/dashboard/student"):
        return redirect(next_path)
    return redirect(url_for("main.student_applications"))


@main.route("/dashboard/student/applications")
@login_required
def student_applications():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile = _student_profile_for_current_user()
    applications = (
        Application.query.filter_by(student_id=student_profile.student_id)
        .order_by(Application.application_id.asc())
        .all()
    )
    placements = (
        student_profile.placements
        if student_profile.placements
        else []
    )
    placements = sorted(placements, key=lambda item: item.placement_id)
    return render_template(
        "student_applications.html",
        active_page="applications",
        student_profile=student_profile,
        applications=applications,
        placements=placements,
        **_student_metrics(student_profile),
    )


@main.route("/dashboard/student/history")
@login_required
def student_history():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    return redirect(url_for("main.student_applications"))


@main.route("/dashboard/student/profile", methods=["GET", "POST"])
@login_required
def student_profile():
    auth_error = _require_role("student")
    if auth_error:
        return auth_error
    student_profile_obj = _student_profile_for_current_user()
    form = StudentFullProfileEditForm(original_email=current_user.email_address)
    resume_max_mb = int(current_app.config.get("RESUME_MAX_MB", 2))

    if request.method == "GET":
        first_name, middle_name, last_name = _split_full_name(current_user.user_name)
        parsed_address = _split_stored_address(current_user.address)
        form.first_name.data = first_name
        form.middle_name.data = middle_name
        form.last_name.data = last_name
        form.email_address.data = current_user.email_address
        form.contact_number.data = current_user.contact_number or ""
        form.address_line1.data = parsed_address["address_line1"]
        form.address_line2.data = parsed_address["address_line2"]
        form.landmark.data = parsed_address["landmark"]
        form.city.data = parsed_address["city"]
        form.state.data = parsed_address["state"]
        form.country.data = parsed_address["country"]
        form.pincode.data = parsed_address["pincode"]
        form.gender.data = current_user.gender or ""
        form.dob.data = current_user.dob
        form.course.data = student_profile_obj.course
        form.branch.data = student_profile_obj.branch
        form.graduation_year.data = student_profile_obj.graduation_year
        form.cgpa.data = student_profile_obj.cgpa

    if form.validate_on_submit():
        current_user.user_name = " ".join(
            part.strip()
            for part in [form.first_name.data, form.middle_name.data, form.last_name.data]
            if part and part.strip()
        )
        current_user.email_address = form.email_address.data.strip().lower()
        current_user.contact_number = form.contact_number.data.strip()
        address_parts = [
            form.address_line1.data,
            form.address_line2.data,
            form.landmark.data,
            f"{form.city.data}, {form.state.data}, {form.country.data} {form.pincode.data}",
        ]
        current_user.address = "\n".join(part.strip() for part in address_parts if part and part.strip())
        current_user.gender = form.gender.data or None
        current_user.dob = form.dob.data
        if form.password.data:
            current_user.set_password(form.password.data)
        student_profile_obj.course = form.course.data.strip()
        student_profile_obj.branch = form.branch.data.strip()
        student_profile_obj.graduation_year = form.graduation_year.data
        student_profile_obj.cgpa = form.cgpa.data

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
        .order_by(JobPosition.job_id.asc())
        .all()
    )
    drive_ids = [drive.job_id for drive in drives]
    applicant_counts = {}
    if drive_ids:
        for app in Application.query.filter(
            Application.job_id.in_(drive_ids),
            Application.status != "withdrawn",
        ).all():
            applicant_counts[app.job_id] = applicant_counts.get(app.job_id, 0) + 1

    return render_template(
        "company_dashboard.html",
        active_page="dashboard",
        company_profile=company_profile,
        drives=drives,
        applicant_counts=applicant_counts,
        **_company_metrics(company_profile),
        **_company_chart_images(company_profile),
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
        .order_by(JobPosition.job_id.asc())
        .all()
    )
    applicant_counts = {}
    drive_ids = [drive.job_id for drive in drives]
    if drive_ids:
        for app in Application.query.filter(
            Application.job_id.in_(drive_ids),
            Application.status != "withdrawn",
        ).all():
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
        .filter(
            JobPosition.company_id == company_profile_obj.company_id,
            Application.status != "withdrawn",
        )
        .order_by(Application.application_id.asc())
        .all()
    )
    company_selected_student_ids = {
        row[0]
        for row in db.session.query(Placement.student_id)
        .filter(
            Placement.company_id == company_profile_obj.company_id,
            Placement.placement_status.in_(_selected_placement_statuses()),
        )
        .all()
    }
    return render_template(
        "company_applications.html",
        active_page="applications",
        company_profile=company_profile_obj,
        applications=applications,
        company_selected_student_ids=company_selected_student_ids,
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
            salary_unit=form.salary_unit.data,
            openings=form.openings.data,
            min_cgpa=form.min_cgpa.data,
            eligible_degrees=_join_multi_select(form.eligible_degrees.data),
            eligible_branches=_join_multi_select(form.eligible_branches.data),
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
        form.salary_unit.data = drive.salary_unit or "lpa"
        form.openings.data = drive.openings
        form.min_cgpa.data = drive.min_cgpa
        form.eligible_degrees.data = _split_multi_select(drive.eligible_degrees)
        form.eligible_branches.data = _split_multi_select(drive.eligible_branches)
        form.description.data = drive.description or ""
        form.application_deadline.data = drive.application_deadline

    if form.validate_on_submit():
        drive.title = form.title.data.strip()
        drive.job_type = form.job_type.data
        drive.location = (form.location.data or "").strip() or None
        drive.salary_lpa = form.salary_lpa.data
        drive.salary_unit = form.salary_unit.data
        drive.openings = form.openings.data
        drive.min_cgpa = form.min_cgpa.data
        drive.eligible_degrees = _join_multi_select(form.eligible_degrees.data)
        drive.eligible_branches = _join_multi_select(form.eligible_branches.data)
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
        Application.query.filter(
            Application.job_id == drive.job_id,
            Application.status != "withdrawn",
        )
        .order_by(Application.application_id.asc())
        .all()
    )
    company_selected_student_ids = {
        row[0]
        for row in db.session.query(Placement.student_id)
        .filter(
            Placement.company_id == company_profile_obj.company_id,
            Placement.placement_status.in_(_selected_placement_statuses()),
        )
        .all()
    }
    return render_template(
        "company_drive_applications.html",
        active_page="drives",
        company_profile=company_profile_obj,
        drive=drive,
        applications=applications,
        company_selected_student_ids=company_selected_student_ids,
        **_company_metrics(company_profile_obj),
    )


@main.route("/dashboard/company/students/<int:student_id>")
@login_required
def company_student_profile_view(student_id):
    auth_error = _require_role("company")
    if auth_error:
        return auth_error

    company_profile_obj = _company_profile_for_current_user()
    student_profile_obj = (
        StudentProfile.query.join(Application, Application.student_id == StudentProfile.student_id)
        .join(JobPosition, JobPosition.job_id == Application.job_id)
        .filter(
            StudentProfile.student_id == student_id,
            JobPosition.company_id == company_profile_obj.company_id,
            Application.status != "withdrawn",
        )
        .first_or_404()
    )

    student_company_apps = (
        Application.query.join(JobPosition)
        .filter(
            Application.student_id == student_id,
            JobPosition.company_id == company_profile_obj.company_id,
            Application.status != "withdrawn",
        )
        .order_by(Application.application_id.asc())
        .all()
    )
    return render_template(
        "company_student_profile_view.html",
        active_page="applications",
        company_profile=company_profile_obj,
        student_profile=student_profile_obj,
        student_company_apps=student_company_apps,
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
            Application.status != "withdrawn",
        )
        .first_or_404()
    )

    action = (request.form.get("action") or "").strip().lower()
    if action not in {"shortlisted", "selected", "rejected"}:
        flash("Invalid application status.", "danger")
        return _company_next_redirect("main.company_drive_applications", job_id=application.job_id)
    if (application.status or "").strip().lower() == "withdrawn":
        flash("Cannot update status for a withdrawn application.", "warning")
        return _company_next_redirect("main.company_drive_applications", job_id=application.job_id)

    if action in {"shortlisted", "selected"} and _status_locked_for_progression(application.status):
        flash("Shortlist/Select is not allowed after this application is finalized.", "warning")
        return _company_next_redirect("main.company_drive_applications", job_id=application.job_id)

    if action in {"shortlisted", "selected"}:
        existing_selection = _existing_company_selection(
            application.student_id,
            company_profile_obj.company_id,
            exclude_application_id=application.application_id,
        )
        if existing_selection:
            flash("This student is already selected for another role in your company.", "warning")
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
        _reject_other_company_applications(
            application.student_id,
            company_profile_obj.company_id,
            application.application_id,
        )
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
        resume_file = form.resume.data
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
            roll_number=_next_student_roll_number(),
            course=form.course.data.strip(),
            branch=form.branch.data.strip(),
            graduation_year=form.graduation_year.data,
            cgpa=form.cgpa.data,
        )

        db.session.add(student_user)
        db.session.add(student_profile)

        try:
            db.session.flush()
            saved_resume, resume_error = _save_student_resume(resume_file, student_user.user_id)
            if resume_error:
                db.session.rollback()
                flash(resume_error, "danger")
                return render_template("register_student.html", form=form)
            if not saved_resume:
                db.session.rollback()
                flash("Resume upload failed. Please try again with a valid file.", "danger")
                return render_template("register_student.html", form=form)
            student_profile.resume_filename = saved_resume
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
            contact_number=None,
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
