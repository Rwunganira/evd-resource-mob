from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
from database import db
from models import PartnerReport, Partner

partner_reports_bp = Blueprint("partner_reports", __name__)

VALID_TYPES = {"Weekly", "Sitrep", "Flash", "Donor"}


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _current_monday() -> date:
    return _monday_of(date.today())


@partner_reports_bp.route("/api/partner-reports", methods=["GET"])
def list_reports():
    q = PartnerReport.query
    week = request.args.get("week")
    partner_id = request.args.get("partner_id")
    submitted = request.args.get("submitted")
    if week:
        try:
            q = q.filter_by(report_week=datetime.strptime(week, "%Y-%m-%d").date())
        except ValueError:
            pass
    if partner_id:
        q = q.filter_by(partner_id=int(partner_id))
    if submitted is not None:
        q = q.filter_by(submitted=(submitted.lower() == "true"))
    reports = q.order_by(PartnerReport.report_week.desc()).all()
    return success([r.to_dict() for r in reports])


@partner_reports_bp.route("/api/partner-reports", methods=["POST"])
def log_report():
    data = request.get_json() or {}
    partner_id = data.get("partner_id")
    if not partner_id or not Partner.query.get(int(partner_id)):
        return error("Valid partner_id is required")
    rtype = data.get("report_type", "Weekly")
    if rtype not in VALID_TYPES:
        return error(f"report_type must be one of {sorted(VALID_TYPES)}")

    week_str = data.get("report_week")
    if week_str:
        try:
            report_week = datetime.strptime(week_str, "%Y-%m-%d").date()
        except ValueError:
            report_week = _current_monday()
    else:
        report_week = _current_monday()

    # Upsert: update if already exists for this partner/week/type
    existing = PartnerReport.query.filter_by(
        partner_id=int(partner_id), report_week=report_week, report_type=rtype
    ).first()
    if existing:
        existing.submitted = bool(data.get("submitted", True))
        existing.submitted_at = datetime.utcnow() if data.get("submitted", True) else None
        existing.notes = data.get("notes", existing.notes)
        db.session.commit()
        return success(existing.to_dict(), "Report updated")

    report = PartnerReport(
        partner_id=int(partner_id),
        report_week=report_week,
        submitted=bool(data.get("submitted", True)),
        submitted_at=datetime.utcnow() if data.get("submitted", True) else None,
        report_type=rtype,
        notes=data.get("notes"),
    )
    db.session.add(report)
    db.session.commit()
    return success(report.to_dict(), "Report logged", 201)


@partner_reports_bp.route("/api/partner-reports/overdue", methods=["GET"])
def overdue_reports():
    week = _current_monday()
    active = Partner.query.filter(Partner.status != "Inactive").all()
    submitted_ids = {
        r.partner_id
        for r in PartnerReport.query.filter_by(report_week=week, submitted=True).all()
    }
    overdue = [p for p in active if p.id not in submitted_ids]
    return success({
        "week": week.isoformat(),
        "overdue_count": len(overdue),
        "total_active": len(active),
        "compliance_pct": round((len(active) - len(overdue)) / len(active) * 100, 1) if active else 0,
        "overdue_partners": [
            {"id": p.id, "name": p.name,
             "contact_email": p.contact_email, "contact_person": p.contact_person}
            for p in overdue
        ],
    })


@partner_reports_bp.route("/api/partner-reports/compliance", methods=["GET"])
def compliance():
    today = date.today()
    weeks = [_monday_of(today) - timedelta(weeks=i) for i in range(3, -1, -1)]
    active = Partner.query.filter(Partner.status != "Inactive").all()
    all_reports = PartnerReport.query.filter(
        PartnerReport.report_week >= weeks[0]
    ).all()

    report_map = {(r.partner_id, r.report_week): r.submitted for r in all_reports}

    by_partner = []
    for p in active:
        weeks_submitted = sum(1 for w in weeks if report_map.get((p.id, w), False))
        by_partner.append({
            "partner_id": p.id,
            "partner_name": p.name,
            "contact_email": p.contact_email,
            "weeks_submitted": weeks_submitted,
            "weeks_total": len(weeks),
            "compliance_pct": round(weeks_submitted / len(weeks) * 100, 1),
            "by_week": {w.isoformat(): report_map.get((p.id, w), False) for w in weeks},
        })

    by_week = []
    for w in weeks:
        submitted = sum(1 for p in active if report_map.get((p.id, w), False))
        by_week.append({
            "week": w.isoformat(),
            "submitted": submitted,
            "total": len(active),
            "compliance_pct": round(submitted / len(active) * 100, 1) if active else 0,
        })

    current_week = _current_monday()
    this_week_submitted = sum(
        1 for p in active if report_map.get((p.id, current_week), False)
    )
    return success({
        "weeks": [w.isoformat() for w in weeks],
        "by_partner": by_partner,
        "by_week": by_week,
        "this_week_submitted": this_week_submitted,
        "this_week_overdue": len(active) - this_week_submitted,
        "total_active_partners": len(active),
    })
