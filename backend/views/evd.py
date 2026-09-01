from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from database import db
from models import (
    GovernmentActivity, PartnerContribution, Partner,
    SubActivity, ActivityComment,
)

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

    total_cost       = sum(a.total_cost_usd or 0 for a in activities)
    total_committed  = sum(a.total_committed for a in activities)
    total_disbursed  = sum(a.total_disbursed for a in activities)
    total_executed   = sum(a.budget_executed_usd or 0 for a in activities)
    commitment_gap   = max(0, total_cost - total_committed)
    disbursement_gap = max(0, total_cost - total_disbursed)
    coverage         = round(min(100, total_committed / total_cost * 100), 1) if total_cost else 0
    execution_rate   = round(total_executed / total_disbursed * 100, 1) if total_disbursed else 0

    return render_template(
        "evd/activities.html",
        active_page="evd_activities",
        grouped=grouped,
        technical_areas=_TA,
        total_cost=total_cost,
        total_committed=total_committed,
        total_disbursed=total_disbursed,
        total_executed=total_executed,
        total_gap=commitment_gap,
        commitment_gap=commitment_gap,
        disbursement_gap=disbursement_gap,
        coverage=coverage,
        execution_rate=execution_rate,
        can_edit=current_user.role in ("admin", "editor"),
    )


@evd_view_bp.route("/evd/contributions")
def contributions_page():
    q = request.args.get("q", "").strip().lower()

    all_activities = GovernmentActivity.query.order_by(
        GovernmentActivity.technical_area_number,
        GovernmentActivity.activity_number,
    ).all()

    if q:
        activities = [a for a in all_activities if
                      q in (a.activity_name or "").lower() or
                      q in (a.activity_number or "").lower() or
                      q in (a.technical_area or "").lower()]
    else:
        activities = all_activities

    selected_id = request.args.get("activity_id", type=int)
    selected    = GovernmentActivity.query.get(selected_id) if selected_id else None

    existing_contribs = {}
    if selected:
        for c in selected.partner_contributions:
            existing_contribs[c.partner_name] = c

    partners = [
        p.name for p in Partner.query.filter(Partner.status != "Inactive").order_by(Partner.name).all()
    ]

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
        q=q,
        can_edit=current_user.role in ("admin", "editor"),
    )


@evd_view_bp.route("/evd/contributions/search")
def search_activities():
    q = request.args.get("q", "").strip().lower()
    selected_id = request.args.get("selected_activity_id", type=int)
    selected = GovernmentActivity.query.get(selected_id) if selected_id else None

    activities = GovernmentActivity.query.order_by(
        GovernmentActivity.technical_area_number,
        GovernmentActivity.activity_number,
    ).all()

    if q:
        activities = [a for a in activities if
                      q in (a.activity_name or "").lower() or
                      q in (a.activity_number or "").lower() or
                      q in (a.technical_area or "").lower()]

    return render_template("evd/_activity_list.html",
                           activities=activities,
                           selected=selected,
                           q=q)


@evd_view_bp.route("/evd/contributions/preview", methods=["POST"])
def preview_contributions():
    aid = request.form.get("government_activity_id", type=int)
    if not aid:
        return ""
    activity = GovernmentActivity.query.get(aid)
    if not activity:
        return ""

    partners = [
        p.name for p in Partner.query.filter(Partner.status != "Inactive").order_by(Partner.name).all()
    ]

    total_committed = sum(
        float(request.form.get(f"committed_{pname}") or 0) for pname in partners
    )
    total_cost = activity.total_cost_usd or 0
    gap        = max(0, total_cost - total_committed)
    coverage   = min(100, total_committed / total_cost * 100) if total_cost else 0
    cov_class  = "text-success" if coverage >= 75 else ("text-warning" if coverage >= 40 else "text-danger")

    return (
        f'<div class="col-md-3 text-center">'
        f'<div class="small text-muted">Govt Cost</div>'
        f'<div class="fw-bold">${total_cost:,.0f}</div>'
        f'</div>'
        f'<div class="col-md-3 text-center">'
        f'<div class="small text-muted">Committed</div>'
        f'<div class="fw-bold text-success">${total_committed:,.0f}</div>'
        f'</div>'
        f'<div class="col-md-3 text-center">'
        f'<div class="small text-muted">Gap</div>'
        f'<div class="fw-bold text-danger">${gap:,.0f}</div>'
        f'</div>'
        f'<div class="col-md-3 text-center">'
        f'<div class="small text-muted">Coverage</div>'
        f'<div class="fw-bold {cov_class}">{coverage:.1f}%</div>'
        f'</div>'
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


# ── Activity detail: sub-activities + comments (HTMX) ─────────────────────────

def _can_edit():
    return current_user.is_authenticated and current_user.role in ("admin", "editor")


def _editor_only():
    if not _can_edit():
        abort(403)


def _render_detail(activity, edit_sub=None, edit_comment=None):
    return render_template(
        "evd/_activity_detail.html",
        a=activity,
        sub_statuses=SubActivity.STATUSES,
        impl_statuses=ActivityComment.IMPL_STATUSES,
        can_edit=_can_edit(),
        is_admin=current_user.is_authenticated and current_user.role == "admin",
        current_user_id=current_user.id if current_user.is_authenticated else None,
        edit_sub=edit_sub,
        edit_comment=edit_comment,
        ncols=15 if _can_edit() else 14,
    )


@evd_view_bp.route("/evd/activities/<int:aid>/detail")
def activity_detail(aid):
    activity = GovernmentActivity.query.get_or_404(aid)
    if request.args.get("collapse"):
        ncols = 15 if _can_edit() else 14
        return (f'<tr id="detail-{aid}" class="detail-row d-none">'
                f'<td colspan="{ncols}" class="p-0"></td></tr>')
    return _render_detail(
        activity,
        edit_sub=request.args.get("edit_sub", type=int),
        edit_comment=request.args.get("edit_comment", type=int),
    )


# ---- sub-activities ----

@evd_view_bp.route("/evd/activities/<int:aid>/subactivities", methods=["POST"])
def add_subactivity(aid):
    _editor_only()
    activity = GovernmentActivity.query.get_or_404(aid)
    name = (request.form.get("name") or "").strip()
    if name:
        status = request.form.get("status") or "Planned"
        if status not in SubActivity.STATUSES:
            status = "Planned"
        last = max((s.sort_order or 0 for s in activity.sub_activities), default=0)
        db.session.add(SubActivity(
            government_activity_id=aid,
            name=name,
            status=status,
            notes=(request.form.get("notes") or "").strip(),
            sort_order=last + 1,
        ))
        db.session.commit()
    return _render_detail(activity)


@evd_view_bp.route("/evd/subactivities/<int:sid>/update", methods=["POST"])
def update_subactivity(sid):
    _editor_only()
    sub = SubActivity.query.get_or_404(sid)
    if "name" in request.form:
        name = (request.form.get("name") or "").strip()
        if name:
            sub.name = name
    if "status" in request.form and request.form["status"] in SubActivity.STATUSES:
        sub.status = request.form["status"]
    if "notes" in request.form:
        sub.notes = (request.form.get("notes") or "").strip()
    db.session.commit()
    return _render_detail(sub.government_activity)


@evd_view_bp.route("/evd/subactivities/<int:sid>/delete", methods=["POST"])
def delete_subactivity(sid):
    _editor_only()
    sub = SubActivity.query.get_or_404(sid)
    activity = sub.government_activity
    db.session.delete(sub)
    db.session.commit()
    return _render_detail(activity)


# ---- comments ----

@evd_view_bp.route("/evd/activities/<int:aid>/comments", methods=["POST"])
def add_comment(aid):
    activity = GovernmentActivity.query.get_or_404(aid)
    body = (request.form.get("body") or "").strip()
    if body:
        impl = request.form.get("impl_status") or "On track"
        if impl not in ActivityComment.IMPL_STATUSES:
            impl = "On track"
        db.session.add(ActivityComment(
            government_activity_id=aid,
            author_id=current_user.id,
            author_name=current_user.name,
            body=body,
            impl_status=impl,
        ))
        db.session.commit()
    return _render_detail(activity)


@evd_view_bp.route("/evd/comments/<int:cid>/update", methods=["POST"])
def update_comment(cid):
    c = ActivityComment.query.get_or_404(cid)
    if not c.can_modify(current_user):
        abort(403)
    body = (request.form.get("body") or "").strip()
    if body:
        c.body = body
    if request.form.get("impl_status") in ActivityComment.IMPL_STATUSES:
        c.impl_status = request.form["impl_status"]
    c.edited = True
    db.session.commit()
    return _render_detail(c.government_activity)


@evd_view_bp.route("/evd/comments/<int:cid>/delete", methods=["POST"])
def delete_comment(cid):
    c = ActivityComment.query.get_or_404(cid)
    if not c.can_modify(current_user):
        abort(403)
    activity = c.government_activity
    db.session.delete(c)
    db.session.commit()
    return _render_detail(activity)
