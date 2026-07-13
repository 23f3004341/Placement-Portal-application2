from . import *


@main.get("/api/student/dashboard")
@role_required("student")
def student_dashboard():
    student = current_user.student_profile
    applications = Application.query.filter_by(student_id=student.student_id).order_by(Application.application_id.desc()).all()
    changed = False
    for application in applications:
        if application.status == "placed":
            changed = ensure_placement_for_placed_application(application) or changed
            changed = reject_same_company_applications_after_placement(application) or changed
    if changed:
        db.session.commit()
        applications = Application.query.filter_by(student_id=student.student_id).order_by(Application.application_id.desc()).all()
    latest_export = ExportJob.query.filter_by(student_id=student.student_id).order_by(ExportJob.created_at.desc()).first()
    return api_ok({
        "student": student_json(student),
        "metrics": {
            "approved_drives": JobPosition.query.filter_by(status="approved", is_active=True).count(),
            "applications": len(applications),
            "interviews": sum(len([i for i in a.interviews if i.status == "scheduled"]) for a in applications),
            "placements": sum(1 for a in applications if a.placement),
        },
        "latest_export": export_json(latest_export),
        "recent_applications": [application_json(item) for item in applications[:5]],
    })


@main.patch("/api/student/profile")
@role_required("student")
def student_profile_update():
    student = current_user.student_profile
    payload = request.form
    try:
        full_name = compose_person_name(payload)
        if full_name:
            current_user.user_name = full_name
        elif (payload.get("name") or "").strip():
            current_user.user_name = payload.get("name").strip()

        email = (payload.get("email") or current_user.email_address).strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return api_error("A valid email is required.", 422)
        existing_email = User.query.filter(
            func.lower(User.email_address) == email,
            User.user_id != current_user.user_id,
        ).first()
        if existing_email:
            return api_error("This email is already registered.", 409)
        current_user.email_address = email

        contact = str(payload.get("contact") or "").strip()
        if contact and not re.fullmatch(r"\d{10}", contact):
            return api_error("Contact number must contain exactly 10 digits.", 422)
        current_user.contact_number = contact
        current_user.gender = (payload.get("gender") or "").strip() or None
        current_user.dob = parse_date(payload.get("dob"), "Date of birth")

        if any(key in payload for key in ("address_line1", "address_line2", "landmark", "pincode", "city", "state", "country")):
            current_user.address = compose_address(payload)
        else:
            current_user.address = (payload.get("address") or current_user.address or "").strip()

        roll_number = (payload.get("roll_number") or student.roll_number).strip().upper()
        if not roll_number:
            return api_error("Student ID is required.", 422)
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
        student.cgpa = float(payload.get("cgpa")) if payload.get("cgpa") not in (None, "") else student.cgpa
        student.experience = (payload.get("experience") or "").strip()
        resume = save_resume(request.files.get("resume"), current_user.user_id)
        if resume:
            student.resume_filename = resume
        db.session.commit()
        invalidate_caches()
        return api_ok(student_json(student), "Profile updated.")
    except ValueError as exc:
        db.session.rollback()
        return api_error(str(exc), 422)


@main.get("/api/student/drives")
@role_required("student")
@cache.cached(timeout=30, query_string=True, key_prefix="student_drives")
def student_drives():
    student = current_user.student_profile
    query_text = (request.args.get("q") or "").strip().lower()
    eligible_only = request.args.get("eligible") == "1"
    query = JobPosition.query.join(CompanyProfile).filter(JobPosition.status == "approved", JobPosition.is_active.is_(True))
    if query_text:
        like = f"{query_text}%"
        query = query.filter(or_(
            func.lower(JobPosition.title).like(like),
            func.lower(CompanyProfile.company_name).like(like),
            func.lower(JobPosition.skills_required).like(like),
        ))
    rows = query.order_by(func.lower(CompanyProfile.company_name), func.lower(JobPosition.title)).all()
    drives = [drive_json(row, student) for row in rows]
    if eligible_only:
        drives = [item for item in drives if item["eligible"]]
    applications = {a.job_id: a.status for a in Application.query.filter_by(student_id=student.student_id).all()}
    for drive in drives:
        drive["application_status"] = applications.get(drive["id"])
    return api_ok(drives)


@main.post("/api/student/drives/<int:job_id>/apply")
@role_required("student")
def student_apply(job_id):
    student = current_user.student_profile
    drive = JobPosition.query.get_or_404(job_id)
    details = drive_json(drive, student)
    if drive.status != "approved" or not drive.is_active or (drive.application_deadline and drive.application_deadline < date.today()):
        return api_error("This drive is not open for applications.", 409)
    if not details["eligible"]:
        return api_error(f"Eligibility not met: {', '.join(details['eligibility_reasons'])}.", 422)
    existing = Application.query.filter_by(student_id=student.student_id, job_id=job_id).first()
    if existing:
        if existing.status == "withdrawn":
            existing.status, existing.applied_at = "applied", datetime.utcnow()
            existing.status_updated_at = datetime.utcnow()
            db.session.commit()
            invalidate_caches()
            return api_ok(application_json(existing), "Application restored.")
        return api_error("You have already applied to this drive.", 409)
    application = Application(
        student_id=student.student_id,
        job_id=job_id,
        cover_letter=((request.get_json(silent=True) or {}).get("cover_letter") or "").strip(),
        status="applied",
    )
    db.session.add(application)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error("You have already applied to this drive.", 409)
    send_chat_message(
        f"{current_app.config.get('UNIVERSITY_NAME', 'Northbridge University')}\n"
        f"Application confirmation for {student.user.user_name}\n\n"
        f"Your application for {drive.title} at {drive.company.company_name} was submitted successfully.\n"
        f"Application deadline: {drive.application_deadline:%d-%m-%Y}"
    )
    invalidate_caches()
    return api_ok(application_json(application), "Application submitted.", 201)


@main.get("/api/student/applications")
@role_required("student")
def student_applications():
    rows = Application.query.filter_by(student_id=current_user.student_profile.student_id).order_by(Application.application_id.desc()).all()
    changed = False
    for application in rows:
        if application.status == "placed":
            changed = ensure_placement_for_placed_application(application) or changed
            changed = reject_same_company_applications_after_placement(application) or changed
    if changed:
        db.session.commit()
        rows = Application.query.filter_by(student_id=current_user.student_profile.student_id).order_by(Application.application_id.desc()).all()
    return api_ok([application_json(item) for item in rows])


@main.patch("/api/student/applications/<int:application_id>/withdraw")
@role_required("student")
def student_withdraw(application_id):
    application = Application.query.filter_by(application_id=application_id, student_id=current_user.student_profile.student_id).first_or_404()
    if application.status != "applied":
        return api_error("Only an unprocessed application can be withdrawn.", 409)
    application.status, application.status_updated_at = "withdrawn", datetime.utcnow()
    db.session.commit()
    invalidate_caches()
    return api_ok(application_json(application), "Application withdrawn.")


@main.post("/api/student/export")
@role_required("student")
def student_export():
    export = ExportJob(student_id=current_user.student_profile.student_id, status="queued", message="CSV export queued.")
    db.session.add(export)
    db.session.flush()
    add_notification(
        current_user.user_id,
        "Export queued",
        "Your application CSV export has been queued.",
        "export",
        "#dashboard",
        f"student-export:{export.export_id}:queued",
    )
    db.session.commit()
    try:
        task = export_student_applications_csv.delay(export.export_id)
        db.session.refresh(export)
        export.task_id = task.id
        if export.status == "queued":
            export.status, export.message = "running", "CSV export is running."
        db.session.commit()
    except Exception as exc:
        export.status, export.message, export.completed_at = "failed", str(exc)[:255], datetime.utcnow()
        db.session.commit()
        return api_error(export.message, 503)
    return api_ok(export_json(export), "Export started.", 202)


@main.get("/api/student/export")
@role_required("student")
def student_export_status():
    export = ExportJob.query.filter_by(student_id=current_user.student_profile.student_id).order_by(ExportJob.created_at.desc()).first()
    export = complete_stale_export(export, export_student_applications_csv)
    return api_ok(export_json(export))


def student_activity_report_data(student):
    applications = (
        Application.query.filter_by(student_id=student.student_id)
        .order_by(Application.applied_at.asc(), Application.application_id.asc())
        .all()
    )
    status_counts = Counter(application.status for application in applications)
    return {
        "student": student,
        "applications": applications,
        "status_counts": status_counts,
        "generated_at": datetime.utcnow(),
        "metrics": {
            "Applications": len(applications),
            "Interviews": sum(len(application.interviews) for application in applications),
            "Offers": sum(1 for application in applications if application.placement),
            "Placements": sum(1 for application in applications if application.placement and application.placement.placement_status == "placed"),
        },
    }


def student_activity_report_html(report):
    student = report["student"]
    rows = []
    for application in report["applications"]:
        drive = application.job_position
        placement = application.placement
        rows.append(
            "<tr>"
            f"<td>{html.escape(student.roll_number)}</td>"
            f"<td>{html.escape(drive.company.company_name)}</td>"
            f"<td>{html.escape(drive.title)}</td>"
            f"<td>{html.escape(application.status.title())}</td>"
            f"<td>{application.applied_at:%Y-%m-%d}</td>"
            f"<td>{drive.application_deadline.strftime('%Y-%m-%d') if drive.application_deadline else '-'}</td>"
            f"<td>{html.escape(placement.placement_status.title()) if placement else '-'}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan=\"7\">No applications yet.</td></tr>")

    metric_rows = "".join(
        f"<tr><th align=\"left\">{html.escape(label)}</th><td>{value}</td></tr>"
        for label, value in report["metrics"].items()
    )
    status_rows = "".join(
        f"<tr><th align=\"left\">{html.escape(status.title())}</th><td>{count}</td></tr>"
        for status, count in sorted(report["status_counts"].items())
    ) or "<tr><td colspan=\"2\">No status history yet.</td></tr>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Student Placement Activity Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #1f2937; margin: 32px; }}
    h1 {{ margin-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; font-size: 13px; }}
    th {{ background: #f3f4f6; }}
    .muted {{ color: #6b7280; }}
  </style>
</head>
<body>
  <h1>Student Placement Activity Report</h1>
  <p class="muted">Generated at {report["generated_at"]:%Y-%m-%d %H:%M UTC}</p>
  <p><strong>Student:</strong> {html.escape(student.user.user_name)}<br>
  <strong>Student ID:</strong> {html.escape(student.roll_number)}</p>
  <h2>Summary</h2>
  <table>{metric_rows}</table>
  <h2>Status Breakdown</h2>
  <table>{status_rows}</table>
  <h2>Application History</h2>
  <table>
    <thead><tr><th>Student ID</th><th>Company</th><th>Drive</th><th>Status</th><th>Applied</th><th>Deadline</th><th>Placement</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>"""


def student_activity_report_pdf(report):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 48
    student = report["student"]
    pdf.setTitle("Student Placement Activity Report")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(48, y, "Student Placement Activity Report")
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(48, y, f"Generated: {report['generated_at']:%Y-%m-%d %H:%M UTC}")
    y -= 18
    pdf.drawString(48, y, f"Student: {student.user.user_name}")
    y -= 18
    pdf.drawString(48, y, f"Student ID: {student.roll_number}")
    y -= 28
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Summary")
    y -= 18
    pdf.setFont("Helvetica", 10)
    for label, value in report["metrics"].items():
        pdf.drawString(58, y, f"{label}: {value}")
        y -= 15
    y -= 10
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Application History")
    y -= 18
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(48, y, "Company")
    pdf.drawString(150, y, "Drive")
    pdf.drawString(290, y, "Status")
    pdf.drawString(365, y, "Applied")
    pdf.drawString(430, y, "Deadline")
    pdf.drawString(500, y, "Placement")
    y -= 12
    pdf.setFont("Helvetica", 8)
    for application in report["applications"]:
        if y < 60:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 8)
        drive = application.job_position
        placement = application.placement
        pdf.drawString(48, y, drive.company.company_name[:22])
        pdf.drawString(150, y, drive.title[:30])
        pdf.drawString(290, y, application.status.title()[:14])
        pdf.drawString(365, y, f"{application.applied_at:%Y-%m-%d}")
        pdf.drawString(430, y, drive.application_deadline.strftime("%Y-%m-%d") if drive.application_deadline else "-")
        pdf.drawString(500, y, placement.placement_status.title()[:12] if placement else "-")
        y -= 13
    if not report["applications"]:
        pdf.drawString(48, y, "No applications yet.")
    pdf.drawRightString(width - 48, 32, "Generated by Placement Portal")
    pdf.save()
    output.seek(0)
    return output


@main.get("/api/student/report")
@role_required("student")
def student_activity_report():
    report_format = (request.args.get("format") or "html").strip().lower()
    if report_format not in {"html", "pdf"}:
        return api_error("Report format must be html or pdf.", 422)
    report = student_activity_report_data(current_user.student_profile)
    filename = f"student-{current_user.student_profile.student_id}-placement-report"
    if report_format == "pdf":
        return send_file(
            student_activity_report_pdf(report),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{filename}.pdf",
        )
    response = make_response(student_activity_report_html(report))
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.html"
    return response


@main.get("/api/student/placements/<int:placement_id>/offer-letter")
@role_required("student")
def student_offer_letter(placement_id):
    placement = Placement.query.filter_by(placement_id=placement_id, student_id=current_user.student_profile.student_id).first_or_404()
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def money_label(value, unit):
        if value in (None, ""):
            return "Not disclosed"
        unit_label = {"lpa": "LPA", "k_month": "K/month"}.get(unit, unit or "")
        return f"{value:g} {unit_label}".strip()

    def safe(value):
        return html.escape(str(value or "-"))

    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=24 * mm,
        leftMargin=24 * mm,
        topMargin=24 * mm,
        bottomMargin=22 * mm,
        title="Placement Offer Letter",
    )
    styles = getSampleStyleSheet()
    company_style = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        alignment=1,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Congratulations",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#047857"),
        spaceAfter=18,
    )
    body_style = ParagraphStyle(
        "OfferBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#374151"),
        spaceAfter=12,
    )
    label_style = ParagraphStyle(
        "DetailLabel",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#111827"),
    )
    value_style = ParagraphStyle(
        "DetailValue",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
    )
    footer_style = ParagraphStyle(
        "OfferFooter",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#6b7280"),
    )

    details = [
        ("Date", f"{placement.offer_date:%B %d, %Y}"),
        ("Student", placement.student.user.user_name),
        ("Student ID", placement.student.roll_number),
        ("Company", placement.company.company_name),
        ("Position", placement.job_position.title),
        ("Package", money_label(placement.offered_package_lpa, placement.job_position.salary_unit)),
        ("Joining date", placement.joining_date.strftime("%B %d, %Y") if placement.joining_date else "To be confirmed"),
        ("Status", placement.placement_status.title()),
    ]
    detail_table = Table(
        [
            [Paragraph(safe(label), label_style), Paragraph(safe(value), value_style)]
            for label, value in details
        ],
        colWidths=[38 * mm, 104 * mm],
        hAlign="LEFT",
    )
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    notes = placement.offer_notes or "Please contact the company HR for onboarding details."
    story = [
        Paragraph(safe(placement.company.company_name), company_style),
        Paragraph("Congratulations, you have been placed!", subtitle_style),
        Paragraph(
            f"Dear {safe(placement.student.user.user_name)},",
            body_style,
        ),
        Paragraph(
            "We are pleased to confirm your placement through the Institute Placement Portal. "
            "Your placement details are listed below for your reference.",
            body_style,
        ),
        Spacer(1, 8),
        detail_table,
        Spacer(1, 16),
        Paragraph(f"<b>Notes:</b> {safe(notes)}", body_style),
        Spacer(1, 36),
        Paragraph("This document was generated by the Institute Placement Portal.", footer_style),
    ]
    document.build(story)
    output.seek(0)
    response = send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"offer-letter-{placement.placement_id}-{datetime.utcnow():%Y%m%d%H%M%S}.pdf",
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response
