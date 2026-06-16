from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_login import login_required
from database import db
from models import PartnerContribution, GovernmentActivity, Partner

partner_contributions_bp = Blueprint("partner_contributions", __name__)

VALID_STATUSES = {"Committed", "Pledged", "Available", "Disbursed", "Conditional", "Cancelled"}
VALID_MODALITIES = {
    "Direct Implementation", "Transfer to Government",
    "In-kind", "Co-implementation",
}


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


@partner_contributions_bp.route("/api/partner-contributions", methods=["GET"])
def list_contributions():
    q = PartnerContribution.query

    activity_id    = request.args.get("activity_id")
    partner_id     = request.args.get("partner_id")
    technical_area = request.args.get("technical_area")
    status         = request.args.get("status")

    if activity_id:
        q = q.filter(PartnerContribution.government_activity_id == int(activity_id))
    if partner_id:
        q = q.filter(PartnerContribution.partner_id == int(partner_id))
    if status:
        q = q.filter(PartnerContribution.status == status)
    if technical_area:
        q = q.join(GovernmentActivity).filter(
            GovernmentActivity.technical_area.ilike(f"%{technical_area}%")
        )

    contribs = q.all()
    return success([c.to_dict() for c in contribs])


@partner_contributions_bp.route("/api/partner-contributions", methods=["POST"])
@login_required
def create_contribution():
    data        = request.get_json() or {}
    activity_id = data.get("government_activity_id")
    partner_id  = data.get("partner_id")

    if not activity_id or not GovernmentActivity.query.get(int(activity_id)):
        return error("Valid government_activity_id is required")
    if not partner_id or not Partner.query.get(int(partner_id)):
        return error("Valid partner_id is required")

    existing = PartnerContribution.query.filter_by(
        government_activity_id=int(activity_id),
        partner_id=int(partner_id),
    ).first()
    if existing:
        return error(
            "Contribution from this partner to this activity already exists. "
            "Use PUT /api/partner-contributions/<id> to update.",
            409,
        )

    status   = data.get("status", "Committed")
    if status not in VALID_STATUSES:
        return error(f"status must be one of {sorted(VALID_STATUSES)}")
    modality = data.get("modality", "Direct Implementation")

    contrib = PartnerContribution(
        government_activity_id=int(activity_id),
        partner_id=int(partner_id),
        amount_committed_usd=float(data.get("amount_committed_usd", 0) or 0),
        amount_available_usd=float(data.get("amount_available_usd", 0) or 0),
        amount_to_mobilize_usd=float(data.get("amount_to_mobilize_usd", 0) or 0),
        amount_disbursed_usd=float(data.get("amount_disbursed_usd", 0) or 0),
        modality=modality,
        status=status,
        notes=data.get("notes", ""),
    )
    db.session.add(contrib)
    db.session.commit()
    return success(contrib.to_dict(), "Contribution created", 201)


@partner_contributions_bp.route("/api/partner-contributions/<int:contrib_id>", methods=["PUT"])
@login_required
def update_contribution(contrib_id):
    contrib = PartnerContribution.query.get_or_404(contrib_id)
    data    = request.get_json() or {}

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return error(f"status must be one of {sorted(VALID_STATUSES)}")
        contrib.status = data["status"]

    for field in ("amount_committed_usd", "amount_available_usd",
                  "amount_to_mobilize_usd", "amount_disbursed_usd"):
        if field in data:
            setattr(contrib, field, float(data[field] or 0))

    if "modality" in data:
        contrib.modality = data["modality"]
    if "notes" in data:
        contrib.notes = data["notes"]

    contrib.updated_at = datetime.utcnow()
    db.session.commit()
    return success(contrib.to_dict(), "Contribution updated")


@partner_contributions_bp.route("/api/partner-contributions/<int:contrib_id>", methods=["DELETE"])
@login_required
def delete_contribution(contrib_id):
    contrib = PartnerContribution.query.get_or_404(contrib_id)
    db.session.delete(contrib)
    db.session.commit()
    return success({"id": contrib_id}, "Contribution deleted")


@partner_contributions_bp.route("/api/partner-contributions/matrix", methods=["GET"])
def contributions_matrix():
    activities = (
        GovernmentActivity.query
        .filter(GovernmentActivity.status != "Suspended")
        .order_by(GovernmentActivity.technical_area_number, GovernmentActivity.activity_number)
        .all()
    )
    activity_ids = {a.id for a in activities}

    partners_with_contribs = (
        Partner.query
        .join(PartnerContribution)
        .filter(PartnerContribution.government_activity_id.in_(activity_ids))
        .distinct()
        .order_by(Partner.name)
        .all()
    )

    matrix: dict = {}
    row_totals: dict = {}

    for a in activities:
        matrix[a.id]     = {}
        row_totals[a.id] = 0
        for c in a.partner_contributions:
            matrix[a.id][c.partner_id] = {
                "amount_committed": c.amount_committed_usd or 0,
                "amount_disbursed": c.amount_disbursed_usd or 0,
                "balance":          c.balance_usd,
                "status":           c.status,
                "contribution_id":  c.id,
            }
            row_totals[a.id] += c.amount_committed_usd or 0

    col_totals: dict = {}
    for p in partners_with_contribs:
        col_totals[p.id] = sum(
            c.amount_committed_usd or 0
            for c in p.evd_contributions
            if c.government_activity_id in activity_ids
        )

    grand_total = sum(row_totals.values())

    return success({
        "activities": [a.to_dict() for a in activities],
        "partners":   [{"id": p.id, "name": p.name} for p in partners_with_contribs],
        "matrix":     {str(k): {str(pk): v for pk, v in pv.items()}
                       for k, pv in matrix.items()},
        "row_totals": {str(k): round(v, 2) for k, v in row_totals.items()},
        "col_totals": {str(k): round(v, 2) for k, v in col_totals.items()},
        "grand_total": round(grand_total, 2),
    })


@partner_contributions_bp.route("/api/partner-contributions/by-partner/<int:partner_id>",
                                methods=["GET"])
def contributions_by_partner(partner_id):
    partner  = Partner.query.get_or_404(partner_id)
    contribs = PartnerContribution.query.filter_by(partner_id=partner_id).all()

    by_ta: dict = {}
    for c in contribs:
        ta = c.government_activity.technical_area if c.government_activity else "Unknown"
        by_ta[ta] = by_ta.get(ta, 0) + (c.amount_committed_usd or 0)

    return success({
        "partner": {
            "id":   partner.id,
            "name": partner.name,
            "type": partner.partner_type,
        },
        "total_committed":  round(sum(c.amount_committed_usd or 0 for c in contribs), 2),
        "total_disbursed":  round(sum(c.amount_disbursed_usd or 0 for c in contribs), 2),
        "total_balance":    round(sum(c.balance_usd for c in contribs), 2),
        "activity_count":   len(contribs),
        "by_technical_area": by_ta,
        "contributions":    [c.to_dict() for c in contribs],
    })


@partner_contributions_bp.route("/api/partner-contributions/by-activity/<int:activity_id>",
                                methods=["GET"])
def contributions_by_activity(activity_id):
    activity = GovernmentActivity.query.get_or_404(activity_id)
    contribs = PartnerContribution.query.filter_by(
        government_activity_id=activity_id
    ).all()
    return success({
        "activity":      activity.to_dict(),
        "contributions": [c.to_dict() for c in contribs],
    })


@partner_contributions_bp.route("/api/partner-contributions/gaps", methods=["GET"])
def funding_gaps():
    activities = (
        GovernmentActivity.query
        .filter(
            GovernmentActivity.status != "Suspended",
            GovernmentActivity.total_cost_usd > 0,
        )
        .all()
    )

    gaps = [
        {
            "id":                    a.id,
            "activity_name":         a.activity_name,
            "technical_area":        a.technical_area,
            "technical_area_number": a.technical_area_number,
            "total_cost":            a.total_cost_usd or 0,
            "total_committed":       round(a.total_committed, 2),
            "gap":                   round(a.funding_gap, 2),
            "coverage_pct":          round(a.coverage_pct, 1),
            "status":                a.status,
            "priority":              a.priority,
        }
        for a in activities
    ]
    gaps.sort(key=lambda x: x["gap"], reverse=True)
    return success(gaps)
