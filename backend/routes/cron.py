import os

from . import *


def check_cron_secret():
    secret = os.environ.get("CRON_SECRET", "")
    if not secret:
        return None
    if request.headers.get("X-Cron-Secret", "") != secret:
        return api_error("Unauthorized cron request.", 401)
    return None


@main.post("/api/cron/daily-reminders")
def cron_daily_reminders():
    error = check_cron_secret()
    if error:
        return error
    result = send_daily_deadline_reminders()
    return api_ok(result, "Daily reminders executed.")


@main.post("/api/cron/monthly-report")
def cron_monthly_report():
    error = check_cron_secret()
    if error:
        return error
    result = send_monthly_activity_report()
    return api_ok(result, "Monthly report executed.")
