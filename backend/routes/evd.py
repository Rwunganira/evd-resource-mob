from flask import Blueprint, jsonify, request
from flask_login import login_required
from database import db
from models import GovernmentActivity, PartnerContribution, Partner

evd_bp = Blueprint("evd", __name__, url_prefix="/api/evd")

_TA = {
    1: "Leadership and Coordination",
    2: "Epidemiological Surveillance",
    3: "Laboratory and Diagnostics",
    4: "Case Management, IPC/WASH and SDB",
    5: "Risk Communication and Community Engagement",
    6: "Operational Support and Logistics",
    7: "Research and Strategic Information",
}

def _ok(data, msg="ok", code=200):
    return jsonify({"status": "success", "data": data, "message": msg}), code

def _err(msg, code=400):
    return jsonify({"status": "error", "data": None, "message": msg}), code


# ── Summary ───────────────────────────────────────────────────────────────────
@evd_bp.route("/summary")
def summary():
    acts = GovernmentActivity.query.filter(GovernmentActivity.status != "Suspended").all()
    total_cost      = sum(a.total_cost_usd or 0 for a in acts)
    total_committed = sum(a.total_committed for a in acts)
    total_gap       = max(0, total_cost - total_committed)
    coverage        = min(100, total_committed / total_cost * 100) if total_cost else 0

    by_ta = []
    for n, name in _TA.items():
        ta_acts = [a for a in acts if a.technical_area_number == n]
        ta_cost = sum(a.total_cost_usd or 0 for a in ta_acts)
        ta_com  = sum(a.total_committed for a in ta_acts)
        ta_gap  = max(0, ta_cost - ta_com)
        by_ta.append({
            "technical_area_number": n,
            "technical_area": name,
            "total_cost": ta_cost,
            "total_committed": ta_com,
            "total_gap": ta_gap,
            "coverage_pct": round(min(100, ta_com / ta_cost * 100), 1) if ta_cost else 0,
            "activity_count": len(ta_acts),
        })

    return _ok({
        "total_activities": len(acts),
        "total_cost_usd": round(total_cost, 2),
        "total_committed_usd": round(total_committed, 2),
        "total_funding_gap": round(total_gap, 2),
        "coverage_pct": round(coverage, 1),
        "by_technical_area": by_ta,
    })


# ── Activities CRUD ───────────────────────────────────────────────────────────
@evd_bp.route("/activities", methods=["GET"])
def list_activities():
    ta_num  = request.args.get("technical_area_number", type=int)
    status  = request.args.get("status")
    priority = request.args.get("priority")

    q = GovernmentActivity.query.filter(GovernmentActivity.status != "Suspended")
    if ta_num:   q = q.filter(GovernmentActivity.technical_area_number == ta_num)
    if status:   q = q.filter(GovernmentActivity.status == status)
    if priority: q = q.filter(GovernmentActivity.priority == priority)

    acts = q.order_by(
        GovernmentActivity.technical_area_number,
        GovernmentActivity.activity_number,
    ).all()

    flat = [a.to_dict() for a in acts]

    grouped = []
    current_ta = None
    for a in acts:
        if a.technical_area_number != current_ta:
            current_ta = a.technical_area_number
            grouped.append({
                "technical_area_number": current_ta,
                "technical_area_name": a.technical_area or _TA.get(current_ta, ""),
                "activities": [],
            })
        grouped[-1]["activities"].append(a.to_dict())

    return _ok({"flat": flat, "grouped": grouped})


@evd_bp.route("/activities/<int:aid>", methods=["GET"])
def get_activity(aid):
    a = GovernmentActivity.query.get_or_404(aid)
    d = a.to_dict()
    d["contributions"] = [c.to_dict() for c in a.partner_contributions]
    return _ok(d)


@evd_bp.route("/activities", methods=["POST"])
@login_required
def create_activity():
    body = request.get_json() or {}
    name = (body.get("activity_name") or "").strip()
    if not name:
        return _err("activity_name is required", 422)

    ta_num = body.get("technical_area_number")
    ta     = body.get("technical_area") or _TA.get(ta_num, "")

    a = GovernmentActivity(
        activity_number=body.get("activity_number", ""),
        technical_area=ta,
        technical_area_number=ta_num,
        sub_section=body.get("sub_section", ""),
        activity_name=name,
        total_cost_usd=float(body.get("total_cost_usd") or 0),
        status=body.get("status", "Planned"),
        priority=body.get("priority", "Medium"),
        notes=body.get("notes", ""),
    )
    db.session.add(a)
    db.session.commit()
    return _ok(a.to_dict(), "Activity created", 201)


@evd_bp.route("/activities/<int:aid>", methods=["PUT"])
@login_required
def update_activity(aid):
    a    = GovernmentActivity.query.get_or_404(aid)
    body = request.get_json() or {}

    if "activity_number"       in body: a.activity_number       = body["activity_number"]
    if "technical_area"        in body: a.technical_area        = body["technical_area"]
    if "technical_area_number" in body: a.technical_area_number = body["technical_area_number"]
    if "sub_section"           in body: a.sub_section           = body["sub_section"]
    if "activity_name"         in body: a.activity_name         = body["activity_name"]
    if "total_cost_usd"        in body: a.total_cost_usd        = float(body["total_cost_usd"] or 0)
    if "status"                in body: a.status                = body["status"]
    if "priority"              in body: a.priority              = body["priority"]
    if "notes"                 in body: a.notes                 = body["notes"]

    db.session.commit()
    return _ok(a.to_dict(), "Activity updated")


@evd_bp.route("/activities/<int:aid>", methods=["DELETE"])
@login_required
def delete_activity(aid):
    a = GovernmentActivity.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    return _ok(None, "Activity deleted")


# ── Contributions CRUD ────────────────────────────────────────────────────────
@evd_bp.route("/contributions", methods=["GET"])
def list_contributions():
    aid  = request.args.get("activity_id", type=int)
    pname = request.args.get("partner_name")

    q = PartnerContribution.query
    if aid:   q = q.filter_by(government_activity_id=aid)
    if pname: q = q.filter_by(partner_name=pname)

    return _ok([c.to_dict() for c in q.all()])


@evd_bp.route("/contributions", methods=["POST"])
@login_required
def create_contribution():
    body  = request.get_json() or {}
    aid   = body.get("government_activity_id")
    pname = (body.get("partner_name") or "").strip()
    if not aid or not pname:
        return _err("government_activity_id and partner_name are required", 422)

    GovernmentActivity.query.get_or_404(aid)
    pobj = Partner.query.filter_by(name=pname).first()

    c = PartnerContribution(
        government_activity_id=aid,
        partner_name=pname,
        partner_id=pobj.id if pobj else None,
        amount_committed_usd=float(body.get("amount_committed_usd") or 0),
        amount_available_usd=float(body.get("amount_available_usd") or 0),
        amount_to_mobilize_usd=float(body.get("amount_to_mobilize_usd") or 0),
        amount_disbursed_usd=float(body.get("amount_disbursed_usd") or 0),
        modality=body.get("modality", "Direct Implementation"),
        status=body.get("status", "Committed"),
        notes=body.get("notes", ""),
    )
    db.session.add(c)
    db.session.commit()
    return _ok(c.to_dict(), "Contribution recorded", 201)


@evd_bp.route("/contributions/bulk", methods=["POST"])
@login_required
def bulk_contributions():
    """Upsert multiple contributions for one activity at once."""
    body  = request.get_json() or {}
    aid   = body.get("government_activity_id")
    rows  = body.get("contributions", [])
    if not aid:
        return _err("government_activity_id is required", 422)

    GovernmentActivity.query.get_or_404(aid)
    saved = []
    for row in rows:
        pname = (row.get("partner_name") or "").strip()
        if not pname:
            continue
        committed = float(row.get("amount_committed_usd") or 0)
        available = float(row.get("amount_available_usd") or 0)
        mobilize  = float(row.get("amount_to_mobilize_usd") or 0)
        disbursed = float(row.get("amount_disbursed_usd") or 0)

        existing = PartnerContribution.query.filter_by(
            government_activity_id=aid, partner_name=pname
        ).first()

        if existing:
            existing.amount_committed_usd   = committed
            existing.amount_available_usd   = available
            existing.amount_to_mobilize_usd = mobilize
            existing.amount_disbursed_usd   = disbursed
            existing.modality = row.get("modality", existing.modality)
            existing.status   = row.get("status",   existing.status)
            existing.notes    = row.get("notes",     existing.notes)
            saved.append(existing)
        else:
            pobj = Partner.query.filter_by(name=pname).first()
            c = PartnerContribution(
                government_activity_id=aid,
                partner_name=pname,
                partner_id=pobj.id if pobj else None,
                amount_committed_usd=committed,
                amount_available_usd=available,
                amount_to_mobilize_usd=mobilize,
                amount_disbursed_usd=disbursed,
                modality=row.get("modality", "Direct Implementation"),
                status=row.get("status", "Committed"),
                notes=row.get("notes", ""),
            )
            db.session.add(c)
            saved.append(c)

    db.session.commit()
    return _ok([c.to_dict() for c in saved], f"{len(saved)} contributions saved")


@evd_bp.route("/contributions/<int:cid>", methods=["PUT"])
@login_required
def update_contribution(cid):
    c    = PartnerContribution.query.get_or_404(cid)
    body = request.get_json() or {}

    if "partner_name"           in body: c.partner_name           = body["partner_name"]
    if "amount_committed_usd"   in body: c.amount_committed_usd   = float(body["amount_committed_usd"] or 0)
    if "amount_available_usd"   in body: c.amount_available_usd   = float(body["amount_available_usd"] or 0)
    if "amount_to_mobilize_usd" in body: c.amount_to_mobilize_usd = float(body["amount_to_mobilize_usd"] or 0)
    if "amount_disbursed_usd"   in body: c.amount_disbursed_usd   = float(body["amount_disbursed_usd"] or 0)
    if "modality"               in body: c.modality               = body["modality"]
    if "status"                 in body: c.status                 = body["status"]
    if "notes"                  in body: c.notes                  = body["notes"]

    db.session.commit()
    return _ok(c.to_dict(), "Contribution updated")


@evd_bp.route("/contributions/<int:cid>", methods=["DELETE"])
@login_required
def delete_contribution(cid):
    c = PartnerContribution.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return _ok(None, "Contribution deleted")


# ── Matrix ────────────────────────────────────────────────────────────────────
@evd_bp.route("/matrix")
def matrix():
    acts    = GovernmentActivity.query.order_by(
        GovernmentActivity.technical_area_number,
        GovernmentActivity.activity_number,
    ).all()
    contribs = PartnerContribution.query.all()

    partner_names = sorted({c.partner_name for c in contribs})

    matrix_data = {}
    row_totals  = {}
    for a in acts:
        a_id = str(a.id)
        matrix_data[a_id] = {}
        for c in a.partner_contributions:
            matrix_data[a_id][c.partner_name] = {
                "contribution_id": c.id,
                "amount_committed": c.amount_committed_usd or 0,
                "amount_disbursed": c.amount_disbursed_usd or 0,
            }
        row_totals[a_id] = sum(
            c.amount_committed_usd or 0 for c in a.partner_contributions
        )

    col_totals = {}
    for pname in partner_names:
        col_totals[pname] = sum(
            c.amount_committed_usd or 0
            for c in contribs if c.partner_name == pname
        )

    grand_total = sum(row_totals.values())

    return _ok({
        "activities": [a.to_dict() for a in acts],
        "partners": partner_names,
        "matrix": matrix_data,
        "row_totals": row_totals,
        "col_totals": col_totals,
        "grand_total": round(grand_total, 2),
    })


# ── Gaps ─────────────────────────────────────────────────────────────────────
@evd_bp.route("/gaps")
def gaps():
    acts = GovernmentActivity.query.filter(
        GovernmentActivity.total_cost_usd > 0
    ).all()
    gap_list = sorted(
        [a.to_dict() for a in acts if a.funding_gap > 0],
        key=lambda x: x["funding_gap"],
        reverse=True,
    )
    return _ok(gap_list)
