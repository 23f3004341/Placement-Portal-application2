from . import *


def public_analytics():
    trend_rows = db.session.query(
        func.strftime("%Y-%m", Placement.created_at), func.count(Placement.placement_id)
    ).group_by(func.strftime("%Y-%m", Placement.created_at)).order_by(func.strftime("%Y-%m", Placement.created_at)).all()[-12:]
    funnel_rows = db.session.query(Application.status, func.count(Application.application_id)).filter(
        Application.status != "withdrawn"
    ).group_by(Application.status).all()
    text = " ".join(f"{drive.title} {drive.skills_required or ''} {drive.description or ''}".lower() for drive in JobPosition.query.filter_by(status="approved").all())
    counts = Counter({skill: text.count(skill) for skill in SKILL_TERMS})
    skills = [(key, value) for key, value in counts.most_common(8) if value]
    data = {
        "totals": {
            "students": StudentProfile.query.count(),
            "companies": CompanyProfile.query.join(User).filter(User.is_approved.is_(True)).count(),
            "drives": JobPosition.query.filter_by(status="approved", is_active=True).count(),
            "placements": Placement.query.count(),
        },
        "trends": {"labels": [r[0] for r in trend_rows], "values": [r[1] for r in trend_rows]},
        "funnel": {"labels": [r[0].title() for r in funnel_rows], "values": [r[1] for r in funnel_rows]},
        "skills": {"labels": [r[0].title() for r in skills], "values": [r[1] for r in skills]},
    }
    return data


@main.get("/api/public/stats")
def public_stats():
    return api_ok(public_analytics())


@main.get("/api/public/pincode/<pincode>")
def public_pincode_lookup(pincode):
    if not re.fullmatch(r"\d{6}", pincode):
        return api_error("Pincode must contain exactly 6 digits.", 422)
    try:
        with urlrequest.urlopen(f"https://api.postalpincode.in/pincode/{pincode}", timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return api_error("Pincode service is temporarily unavailable.", 502)
    if not payload or payload[0].get("Status") != "Success" or not payload[0].get("PostOffice"):
        return api_error("No city or state was found for this pincode.", 404)
    post_office = payload[0]["PostOffice"][0]
    result = {
        "city": post_office.get("District") or post_office.get("Name") or "",
        "state": post_office.get("State") or "",
        "country": post_office.get("Country") or "India",
    }
    return api_ok(result)
