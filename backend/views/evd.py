from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from database import db
from models import GovernmentActivity, PartnerContribution, Partner

evd_view_bp = Blueprint("evd_view", __name__)

_TA = {
    1: "Leadership and Coordination",
    2: "Epidemiological Surveillance",
    3: "Laboratory and Diagnostics",
    4: "Case Management, IPC/WASH and SDB",
    5: "Risk Communication and Community Engagement",
    6: "Operational Support and Logistics",
    7: "Research and Strategic Information",
}

@evd_view_bp.before_request
@login_required
def require_login():
    pass


@evd_view_bp.route("/evd/activities")
def activities_page():
    activities = GovernmentActivity.query.order_by(
        GovernmentActivity.technical_area_number,
        GovernmentActivity.activity_number,
    ).all()

    grouped = []
    current_ta = None
    for a in activities:
        if a.technical_area_number != current_ta:
            current_ta = a.technical_area_number
            grouped.append({"number": current_ta, "name": a.technical_area, "activities": []})
        grouped[-1]["activities"].append(a)

    total_cost      = sum(a.total_cost_usd or 0 for a in activities)
    total_committed = sum(a.total_committed for a in activities)
    total_gap       = sum(a.funding_gap for a in activities)
    coverage        = round(total_committed / total_cost * 100, 1) if total_cost else 0

    return render_template(
        "evd/activities.html",
        active_page="evd_activities",
        grouped=grouped,
        technical_areas=_TA,
        total_cost=total_cost,
        total_committed=total_committed,
        total_gap=total_gap,
        coverage=coverage,
        can_edit=current_user.role in ("admin", "editor"),
    )


@evd_view_bp.route("/evd/contributions")
def contributions_page():
    activities = GovernmentActivity.query.order_by(
        GovernmentActivity.technical_area_number,
        GovernmentActivity.activity_number,
    ).all()

    selected_id = request.args.get("activity_id", type=int)
    selected    = GovernmentActivity.query.get(selected_id) if selected_id else None

    existing_contribs = {}
    if selected:
        for c in selected.partner_contributions:
            existing_contribs[c.partner_name] = c

    # All active partners from DB, sorted by name
    partners = [
        p.name for p in Partner.query.filter(Partner.status != "Inactive").order_by(Partner.name).all()
    ]

    # Per-partner totals across all activities
    all_contribs = PartnerContribution.query.all()
    partner_totals = {}
    for c in all_contribs:
        partner_totals[c.partner_name] = (
            partner_totals.get(c.partner_name, 0) + (c.amount_committed_usd or 0)
        )

    return render_template(
        "evd/contributions.html",
        active_page="evd_contributions",
        activities=activities,
        selected=selected,
        existing_contribs=existing_contribs,
        partners=partners,
        partner_totals=partner_totals,
        can_edit=current_user.role in ("admin", "editor"),
    )


@evd_view_bp.route("/evd/contributions/bulk", methods=["POST"])
def save_contributions_bulk():
    aid = request.form.get("government_activity_id", type=int)
    if not aid:
        return '<div class="alert alert-danger mt-2">Missing activity ID</div>'

    activity = GovernmentActivity.query.get(aid)
    if not activity:
        return '<div class="alert alert-danger mt-2">Activity not found</div>'

    partners = [
        p for p in Partner.query.filter(Partner.status != "Inactive").order_by(Partner.name).all()
    ]

    for p in partners:
        pname     = p.name
        committed = float(request.form.get(f"committed_{pname}") or 0)
        available = float(request.form.get(f"available_{pname}") or 0)
        mobilize  = float(request.form.get(f"mobilize_{pname}") or 0)
        disbursed = float(request.form.get(f"disbursed_{pname}") or 0)
        status    = request.form.get(f"status_{pname}") or "Committed"

        existing = PartnerContribution.query.filter_by(
            government_activity_id=aid, partner_name=pname
        ).first()

        if existing:
            existing.amount_committed_usd   = committed
            existing.amount_available_usd   = available
            existing.amount_to_mobilize_usd = mobilize
            existing.amount_disbursed_usd   = disbursed
            existing.status                 = status
        else:
            db.session.add(PartnerContribution(
                government_activity_id=aid,
                partner_name=pname,
                partner_id=p.id,
                amount_committed_usd=committed,
                amount_available_usd=available,
                amount_to_mobilize_usd=mobilize,
                amount_disbursed_usd=disbursed,
                modality="Direct Implementation",
                status=status,
            ))

    db.session.commit()
    return f'<div class="alert alert-success mt-2"><i class="bi bi-check-circle me-1"></i>{len(partners)} contributions saved</div>'
