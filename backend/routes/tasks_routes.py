from . import *


@main.post("/api/student/export-applications")
@role_required("student")
def trigger_student_export():
    export = ExportJob(student_id=current_user.student_profile.student_id, status="queued", message="CSV export queued.")
    db.session.add(export)
    db.session.flush()
    db.session.commit()
    task = export_student_applications_csv.delay(export.export_id)
    export.task_id = task.id
    db.session.commit()
    return api_ok(export_json(export), "Export started.", 202)


@main.get("/api/student/export-status")
@role_required("student")
def student_export_task_status():
    export = ExportJob.query.filter_by(student_id=current_user.student_profile.student_id).order_by(ExportJob.created_at.desc()).first()
    export = complete_stale_export(export, export_student_applications_csv)
    return api_ok(export_json(export))
