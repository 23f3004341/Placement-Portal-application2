from . import *


@main.get("/api/company/dashboard")
@role_required("company")
def company_dashboard():
    company = current_user.company_profile
    drives = JobPosition.query.filter_by(company_id=company.company_id).order_by(JobPosition.job_id.desc()).all()
    applications = Application.query.join(JobPosition).filter(JobPosition.company_id == company.company_id, Application.status != "withdrawn").all()
    return api_ok({
        "company": company_json(company),
        "metrics": {
            "active_drives": sum(1 for d in drives if d.is_active and d.status == "approved"),
            "applications": len(applications),
            "students": len({application.student_id for application in applications}),
            "placed": sum(1 for a in applications if a.status == "placed"),
        },
        "drives": [drive_json(drive) for drive in drives],
    })


@main.patch("/api/company/profile")
@role_required("company")
def company_profile_update():
    company = current_user.company_profile
    payload = request.get_json(silent=True) or {}
    company.company_name = (payload.get("name") or company.company_name).strip()
    for key in ("industry", "website", "headquarters", "description", "hr_name", "hr_email", "hr_phone"):
        if key in payload:
            setattr(company, key, (payload.get(key) or "").strip())
    current_user.user_name = company.company_name
    if "contact" in payload:
        current_user.contact_number = (payload.get("contact") or "").strip()
    db.session.commit()
    invalidate_caches()
    return api_ok(company_json(company), "Company profile updated.")


def apply_drive_payload(drive, payload):
    required = {
        "title": payload.get("title"),
        "job_type": payload.get("job_type"),
        "deadline": payload.get("deadline"),
        "location": payload.get("location"),
        "salary": payload.get("salary"),
        "openings": payload.get("openings"),
        "min_cgpa": payload.get("min_cgpa"),
        "eligible_degrees": payload.get("eligible_degrees"),
        "eligible_branches": payload.get("eligible_branches"),
        "eligible_years": payload.get("eligible_years"),
        "description": payload.get("description"),
    }
    missing = [key for key, value in required.items() if not str(value or "").strip()]
    if missing:
        raise ValueError(f"Required fields: {', '.join(missing)}.")
    drive.title = payload.get("title").strip()
    drive.job_type = (payload.get("job_type") or "full-time").strip()
    drive.location = (payload.get("location") or "").strip()
    drive.salary_lpa = float(payload.get("salary")) if payload.get("salary") not in (None, "") else None
    drive.salary_unit = (payload.get("salary_unit") or "lpa").strip()
    drive.openings = int(payload.get("openings") or 1)
    drive.min_cgpa = float(payload.get("min_cgpa")) if payload.get("min_cgpa") not in (None, "") else None
    drive.eligible_degrees = (payload.get("eligible_degrees") or "").strip()
    drive.eligible_branches = (payload.get("eligible_branches") or "").strip()
    drive.eligible_years = (payload.get("eligible_years") or "").strip()
    drive.skills_required = (payload.get("skills_required") or "").strip()
    drive.experience_required = (payload.get("experience_required") or "").strip()
    drive.benefits = ""
    drive.description = payload.get("description").strip()
    drive.application_deadline = parse_date(payload.get("deadline"), "Application deadline", True)
    if drive.application_deadline < date.today():
        raise ValueError("Application deadline cannot be in the past.")


@main.post("/api/company/drives")
@role_required("company")
def company_create_drive():
    payload = request.get_json(silent=True) or {}
    drive = JobPosition(company_id=current_user.company_profile.company_id, status="pending", is_active=True)
    try:
        apply_drive_payload(drive, payload)
    except (ValueError, TypeError) as exc:
        return api_error(str(exc), 422)
    db.session.add(drive)
    db.session.commit()
    invalidate_caches()
    return api_ok(drive_json(drive), "Drive submitted for admin approval.", 201)


@main.patch("/api/company/drives/<int:job_id>")
@role_required("company")
def company_update_drive(job_id):
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=current_user.company_profile.company_id).first_or_404()
    try:
        apply_drive_payload(drive, request.get_json(silent=True) or {})
    except (ValueError, TypeError) as exc:
        return api_error(str(exc), 422)
    drive.status = "pending"
    db.session.commit()
    invalidate_caches()
    return api_ok(drive_json(drive), "Drive updated and resubmitted.")


@main.patch("/api/company/drives/<int:job_id>/close")
@role_required("company")
def company_close_drive(job_id):
    drive = JobPosition.query.filter_by(job_id=job_id, company_id=current_user.company_profile.company_id).first_or_404()
    drive.status, drive.is_active = "closed", False
    db.session.commit()
    invalidate_caches()
    return api_ok(drive_json(drive), "Drive closed.")


@main.get("/api/company/applications")
@role_required("company")
def company_applications():
    query = Application.query.join(JobPosition).filter(
        JobPosition.company_id == current_user.company_profile.company_id,
        Application.status != "withdrawn",
    )
    job_id = request.args.get("job_id", type=int)
    if job_id:
        query = query.filter(Application.job_id == job_id)
    rows = query.order_by(Application.application_id.desc()).all()
    changed = False
    for application in rows:
        if application.status == "placed":
            changed = reject_same_company_applications_after_placement(application) or changed
    if changed:
        db.session.commit()
        rows = query.order_by(Application.application_id.desc()).all()
    return api_ok([application_json(item) for item in rows])


@main.patch("/api/company/applications/<int:application_id>")
@role_required("company")
def company_application_status(application_id):
    application = Application.query.join(JobPosition).filter(
        Application.application_id == application_id,
        JobPosition.company_id == current_user.company_profile.company_id,
    ).first_or_404()
    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") or "").lower()
    if status not in {"shortlisted", "rejected", "placed"}:
        return api_error("Invalid application status.")
    application.status = status
    application.company_feedback = (payload.get("feedback") or application.company_feedback or "").strip()
    application.status_updated_at = datetime.utcnow()
    placement = application.placement
    if status == "placed":
        if not placement:
            placement = Placement(
                application=application,
                student_id=application.student_id,
                company_id=application.job_position.company_id,
                job_id=application.job_id,
                offered_package_lpa=application.job_position.salary_lpa,
                offer_date=date.today(),
            )
            db.session.add(placement)
        placement.placement_status = "placed"
        placement.offer_notes = (payload.get("offer_notes") or placement.offer_notes or "").strip()
        if payload.get("joining_date"):
            try:
                placement.joining_date = parse_date(payload.get("joining_date"), "Joining date")
            except ValueError as exc:
                return api_error(str(exc), 422)
        reject_same_company_applications_after_placement(application)
    elif placement:
        db.session.delete(placement)
    title = "Application updated"
    message = f"{application.job_position.company.company_name} updated your {application.job_position.title} application to {status}."
    if status == "placed":
        title = "Placement confirmed"
        message = f"{application.job_position.company.company_name} marked your {application.job_position.title} application as {status}."
    elif status == "rejected":
        title = "Application decision"
    add_notification(
        application.student.user_id,
        title,
        message,
        "success" if status == "placed" else "info",
        "#student-applications",
        f"application-status:{application.application_id}:{status}:{application.status_updated_at.isoformat()}",
    )
    student = application.student
    company = application.job_position.company
    status_label = status.replace("_", " ").title()
    student_message = (
        f"Hello {student.user.user_name},\n\n"
        f"Your application status has been updated.\n\n"
        f"Company: {company.company_name}\n"
        f"Role: {application.job_position.title}\n"
        f"Status: {status_label}\n"
    )
    if application.company_feedback:
        student_message += f"Feedback: {application.company_feedback}\n"
    send_student_email(student, f"Application status update - {company.company_name}", student_message)
    send_chat_message(
        f"{current_app.config.get('UNIVERSITY_NAME', 'Northbridge University')}\n"
        f"Status update for {student.user.user_name}\n"
        f"{company.company_name} - {application.job_position.title}: {status_label}"
    )
    db.session.commit()
    invalidate_caches()
    return api_ok(application_json(application), "Application updated.")


@main.post("/api/company/applications/<int:application_id>/interviews")
@role_required("company")
def company_schedule_interview(application_id):
    application = Application.query.join(JobPosition).filter(
        Application.application_id == application_id,
        JobPosition.company_id == current_user.company_profile.company_id,
    ).first_or_404()
    student_already_placed = (
        Application.query.filter(
            Application.student_id == application.student_id,
            Application.status.in_(("selected", "placed")),
        ).first() is not None
        or Placement.query.filter_by(student_id=application.student_id, placement_status="placed").first() is not None
    )
    if student_already_placed or application.status in {"selected", "placed"} or (
        application.placement and application.placement.placement_status == "placed"
    ):
        return api_error("An interview cannot be scheduled after the student has been selected or placed.", 409)
    if application.status != "shortlisted":
        return api_error("Shortlist the application before scheduling an interview.", 409)
    if application.interviews:
        scheduled_at = sorted(application.interviews, key=lambda item: item.scheduled_at)[0].scheduled_at
        return api_error(f"Interview already scheduled at {scheduled_at:%Y-%m-%d %H:%M}.", 409)
    payload = request.get_json(silent=True) or {}
    try:
        scheduled_at = parse_datetime(payload.get("scheduled_at"))
    except ValueError as exc:
        return api_error(str(exc), 422)
    if scheduled_at <= datetime.now():
        return api_error("Interview must be scheduled in the future.", 422)
    interview = Interview(
        application=application,
        scheduled_at=scheduled_at,
        mode=(payload.get("mode") or "online").strip(),
        location_or_link=(payload.get("location_or_link") or "").strip(),
        notes=(payload.get("notes") or "").strip(),
    )
    application.status = "interview"
    application.status_updated_at = datetime.utcnow()
    db.session.add(interview)
    add_notification(
        application.student.user_id,
        "Interview scheduled",
        (
            f"{application.job_position.company.company_name} scheduled an interview for "
            f"{application.job_position.title} on {scheduled_at:%Y-%m-%d at %H:%M}."
        ),
        "interview",
        "#student-applications",
        f"interview:{interview.interview_id}",
    )
    student = application.student
    company = application.job_position.company
    interview_message = (
        f"Hello {student.user.user_name},\n\n"
        f"Your interview has been scheduled.\n\n"
        f"Company: {company.company_name}\n"
        f"Role: {application.job_position.title}\n"
        f"Date and time: {scheduled_at:%Y-%m-%d at %H:%M}\n"
        f"Mode: {interview.mode}\n"
        f"Location/Link: {interview.location_or_link or '-'}\n"
    )
    if interview.notes:
        interview_message += f"Notes: {interview.notes}\n"
    send_student_email(student, f"Interview scheduled - {company.company_name}", interview_message)
    send_chat_message(
        f"{current_app.config.get('UNIVERSITY_NAME', 'Northbridge University')}\n"
        f"Interview scheduled for {student.user.user_name}\n"
        f"{company.company_name} - {application.job_position.title}\n"
        f"When: {scheduled_at:%d-%m-%Y %H:%M}"
    )
    db.session.commit()
    invalidate_caches()
    return api_ok(interview_json(interview), "Interview scheduled.", 201)


@main.patch("/api/company/interviews/<int:interview_id>")
@role_required("company")
def company_interview_result(interview_id):
    interview = Interview.query.join(Application).join(JobPosition).filter(
        Interview.interview_id == interview_id,
        JobPosition.company_id == current_user.company_profile.company_id,
    ).first_or_404()
    if interview.application.status in {"selected", "placed"} or (
        interview.application.placement and interview.application.placement.placement_status == "placed"
    ):
        return api_error("Interview feedback cannot be changed after the student has been placed.", 409)
    payload = request.get_json(silent=True) or {}
    interview.feedback = (payload.get("feedback") or "").strip()
    result = (payload.get("result") or "").lower()
    if result not in {"", "placed", "rejected"}:
        return api_error("Interview result must be placed or rejected.")
    interview.result = result or None
    interview.status = "completed" if result else interview.status
    if result:
        interview.application.status = result
        interview.application.company_feedback = interview.feedback
        interview.application.status_updated_at = datetime.utcnow()
        if result == "placed" and not interview.application.placement:
            db.session.add(Placement(
                application=interview.application,
                student_id=interview.application.student_id,
                company_id=interview.application.job_position.company_id,
                job_id=interview.application.job_id,
                offered_package_lpa=interview.application.job_position.salary_lpa,
                offer_date=date.today(),
                placement_status="placed",
            ))
        add_notification(
            interview.application.student.user_id,
            "Interview result updated",
            (
                f"{interview.application.job_position.company.company_name} marked your "
                f"{interview.application.job_position.title} interview result as {result}."
            ),
            "success" if result == "placed" else "info",
            "#student-applications",
            f"interview-result:{interview.interview_id}:{result}",
        )
        student = interview.application.student
        company = interview.application.job_position.company
        result_label = result.title()
        result_message = (
            f"Hello {student.user.user_name},\n\n"
            f"Your interview result has been updated.\n\n"
            f"Company: {company.company_name}\n"
            f"Role: {interview.application.job_position.title}\n"
            f"Result: {result_label}\n"
        )
        if interview.feedback:
            result_message += f"Feedback: {interview.feedback}\n"
        send_student_email(student, f"Interview result - {company.company_name}", result_message)
        send_chat_message(
            f"{current_app.config.get('UNIVERSITY_NAME', 'Northbridge University')}\n"
            f"Interview result for {student.user.user_name}\n"
            f"{company.company_name} - {interview.application.job_position.title}: {result_label}"
        )
    elif interview.feedback:
        student = interview.application.student
        company = interview.application.job_position.company
        add_notification(
            student.user_id,
            "Interview feedback received",
            f"{company.company_name} submitted feedback for your {interview.application.job_position.title} interview.",
            "info",
            "#student-applications",
            f"interview-feedback:{interview.interview_id}:{datetime.utcnow().isoformat()}",
        )
        feedback_message = (
            f"Hello {student.user.user_name},\n\n"
            f"{company.company_name} submitted feedback for your interview for "
            f"{interview.application.job_position.title}.\n\n"
            f"Feedback: {interview.feedback}\n"
        )
        send_student_email(student, f"Interview feedback - {company.company_name}", feedback_message)
        send_chat_message(
            f"{current_app.config.get('UNIVERSITY_NAME', 'Northbridge University')}\n"
            f"Interview feedback for {student.user.user_name}\n\n"
            f"{company.company_name} submitted feedback for {interview.application.job_position.title}.\n"
            f"Feedback: {interview.feedback}"
        )
    db.session.commit()
    invalidate_caches()
    return api_ok(interview_json(interview), "Interview feedback saved.")
