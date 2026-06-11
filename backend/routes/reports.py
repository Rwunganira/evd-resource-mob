from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
from collections import Counter
from sqlalchemy import func
from database import db
from models import SituationReport, OutbreakPhase, Partner, Resource, Activity, FundingGap, PartnerReport

reports_bp = Blueprint("reports", __name__)


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


def _parse_date(val):
    if not val:
        return date.today()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return date.today()


def _current_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


@reports_bp.route("/api/sitreps", methods=["GET"])
def list_sitreps():
    sitreps = SituationReport.query.order_by(SituationReport.report_date.desc()).all()
    return success([s.to_dict() for s in sitreps])


@reports_bp.route("/api/sitreps/latest", methods=["GET"])
def latest_sitrep():
    sitrep = SituationReport.query.order_by(SituationReport.report_date.desc()).first()
    if not sitrep:
        return error("No situation reports found", 404)
    return success(sitrep.to_dict())


@reports_bp.route("/api/sitreps", methods=["POST"])
def create_sitrep():
    data = request.get_json() or {}
    outbreak_day = data.get("outbreak_day")
    if not outbreak_day:
        return error("outbreak_day is required")
    confirmed = int(data.get("confirmed_cases", 0))
    deaths = int(data.get("deaths", 0))
    if deaths > confirmed:
        return error("deaths cannot exceed confirmed_cases")

    sitrep = SituationReport(
        report_date=_parse_date(data.get("report_date")),
        outbreak_day=int(outbreak_day),
        confirmed_cases=confirmed,
        deaths=deaths,
        healthcare_workers_affected=int(data.get("healthcare_workers_affected", 0)),
        etus_operational=int(data.get("etus_operational", 0)),
        total_funding_mobilized=float(data.get("total_funding_mobilized", 0)),
        funding_gap=float(data.get("funding_gap", 0)),
        notes=data.get("notes", ""),
        created_by=data.get("created_by", ""),
    )
    db.session.add(sitrep)
    db.session.commit()
    return success(sitrep.to_dict(), "Situation report created", 201)


@reports_bp.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    # ── Partners ──────────────────────────────────────────────────────────────
    total_partners = Partner.query.filter(Partner.status != "Inactive").count()
    active_partners = Partner.query.filter_by(status="Active").count()

    # ── Funding (from Resource table) ─────────────────────────────────────────
    total_funding = (
        db.session.query(func.sum(Resource.amount))
        .filter(Resource.resource_type == "Funding", Resource.currency == "USD",
                Resource.status.in_(["Committed", "Deployed"]))
        .scalar() or 0
    )
    deployed_funding = (
        db.session.query(func.sum(Resource.amount))
        .filter(Resource.resource_type == "Funding", Resource.currency == "USD",
                Resource.status == "Deployed")
        .scalar() or 0
    )

    # ── Activities ────────────────────────────────────────────────────────────
    ongoing_activities = Activity.query.filter_by(status="Ongoing").count()
    total_activities = Activity.query.count()

    # Most active location
    location_counts = (
        db.session.query(Activity.location, func.count(Activity.id).label("cnt"))
        .filter(Activity.status != "Completed")
        .group_by(Activity.location)
        .order_by(func.count(Activity.id).desc())
        .first()
    )
    most_active_location = location_counts[0] if location_counts else None

    # ── SitRep ────────────────────────────────────────────────────────────────
    latest = SituationReport.query.order_by(SituationReport.report_date.desc()).first()
    phase = OutbreakPhase.query.filter_by(is_current=True).first()

    estimated_need = 50_000_000
    if latest:
        estimated_need = latest.total_funding_mobilized + latest.funding_gap or estimated_need
    resource_gap = max(0, estimated_need - float(total_funding))

    # ── Funding Gap pillars ───────────────────────────────────────────────────
    gaps = FundingGap.query.all()
    funding_gap_total = sum(g.gap_usd for g in gaps)
    funding_gap_required = sum(g.amount_required_usd for g in gaps)
    funding_gap_funded = sum(g.amount_funded_usd for g in gaps)
    funding_coverage_pct = (
        round(funding_gap_funded / funding_gap_required * 100, 1)
        if funding_gap_required else 0
    )
    top_funded_pillar = (
        max(gaps, key=lambda g: g.coverage_pct).pillar_name if gaps else None
    )

    # ── Partner reporting (this week) ─────────────────────────────────────────
    week = _current_monday()
    active_partner_ids = {
        p.id for p in Partner.query.filter(Partner.status != "Inactive").all()
    }
    submitted_ids = {
        r.partner_id
        for r in PartnerReport.query.filter_by(report_week=week, submitted=True).all()
    }
    partners_reporting = len(submitted_ids & active_partner_ids)
    partners_overdue = len(active_partner_ids - submitted_ids)

    return success({
        "partners": {"total": total_partners, "active": active_partners},
        "funding": {
            "total_committed_usd": float(total_funding),
            "total_deployed_usd": float(deployed_funding),
            "estimated_need_usd": estimated_need,
            "gap_usd": resource_gap,
            "coverage_percent": round(float(total_funding) / estimated_need * 100, 1) if estimated_need else 0,
        },
        "activities": {"ongoing": ongoing_activities, "total": total_activities},
        "latest_sitrep": latest.to_dict() if latest else None,
        "current_phase": phase.to_dict() if phase else None,
        "etus_operational": latest.etus_operational if latest else 0,
        "outbreak_day": latest.outbreak_day if latest else 0,
        # ── NEW fields ────────────────────────────────────────────────────────
        "funding_gap_total_usd": funding_gap_total,
        "funding_coverage_pct": funding_coverage_pct,
        "partners_reporting_this_week": partners_reporting,
        "partners_overdue_this_week": partners_overdue,
        "top_funded_pillar": top_funded_pillar,
        "most_active_location": most_active_location,
    })
