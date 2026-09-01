from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from models import GovernmentActivity, PartnerContribution

gov_activities_bp = Blueprint("gov_activities", __name__)

VALID_STATUSES  = {"Planned", "Active", "Completed", "Suspended"}
VALID_PRIORITIES = {"High", "Medium", "Low"}

PILLARS = {
    1: "Leadership and Coordination",
    2: "Epidemiological Surveillance",
    3: "Laboratory and Diagnostics",
    4: "Case Management, IPC/WASH and SDB",
    5: "Risk Communication and Community Engagement",
    6: "Operational Support and Logistics",
    7: "Research and Strategic Information",
}


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


@gov_activities_bp.route("/api/government-activities/summary", methods=["GET"])
def gov_activities_summary():
    activities = GovernmentActivity.query.filter(
        GovernmentActivity.status != "Suspended"
    ).all()

    total_cost    = sum(a.total_cost_usd or 0 for a in activities)
    total_support = sum(a.total_partner_support for a in activities)
    total_gap     = sum(a.funding_gap for a in activities)
    coverage      = round(total_support / total_cost * 100, 1) if total_cost else 0

    by_pillar = []
    for pnum, pname in sorted(PILLARS.items()):
        pillar_acts = [a for a in activities if a.pillar_number == pnum]
        pc = sum(a.total_cost_usd or 0 for a in pillar_acts)
        ps = sum(a.total_partner_support for a in pillar_acts)
        pg = sum(a.funding_gap for a in pillar_acts)
        by_pillar.append({
            "pillar_number": pnum,
            "pillar_name": pname,
            "total_cost": round(pc, 2),
            "total_support": round(ps, 2),
            "gap": round(pg, 2),
            "coverage_pct": round(ps / pc * 100, 1) if pc else 0,
            "activity_count": len(pillar_acts),
        })

    return success({
        "total_activities": len(activities),
        "total_cost_usd": round(total_cost, 2),
        "total_partner_support": round(total_support, 2),
        "total_funding_gap": round(total_gap, 2),
        "coverage_pct": coverage,
        "by_pillar": by_pillar,
    })


@gov_activities_bp.route("/api/government-activities", methods=["GET"])
def list_gov_activities():
    q = GovernmentActivity.query.filter(GovernmentActivity.status != "Suspended")

    pillar   = request.args.get("pillar")
    status   = request.args.get("status")
    priority = request.args.get("priority")

    if pillar:
        q = q.filter(GovernmentActivity.pillar.ilike(f"%{pillar}%"))
    if status:
        q = q.filter(GovernmentActivity.status == status)
    if priority:
        q = q.filter(GovernmentActivity.priority == priority)

    activities = q.order_by(
        GovernmentActivity.pillar_number,
        GovernmentActivity.activity_number,
    ).all()

    grouped: dict = {}
    for a in activities:
        pnum = a.pillar_number or 0
        if pnum not in grouped:
            grouped[pnum] = {
                "pillar_number": pnum,
                "pillar_name": PILLARS.get(pnum, a.pillar or ""),
                "activities": [],
            }
        grouped[pnum]["activities"].append(a.to_dict())

    return success({
        "grouped": list(grouped.values()),
        "flat": [a.to_dict() for a in activities],
    })


@gov_activities_bp.route("/api/government-activities", methods=["POST"])
def create_gov_activity():
    data = request.get_json() or {}
    name = (data.get("activity_name") or "").strip()
    if not name:
        return error("activity_name is required")

    status = data.get("status", "Planned")
    if status not in VALID_STATUSES:
        return error(f"status must be one of {sorted(VALID_STATUSES)}")

    priority = data.get("priority", "Medium")
    if priority not in VALID_PRIORITIES:
        return error(f"priority must be one of {sorted(VALID_PRIORITIES)}")

    pillar_num = data.get("pillar_number")
    if pillar_num is not None:
        try:
            pillar_num = int(pillar_num)
        except (TypeError, ValueError):
            return error("pillar_number must be an integer 1–7")
        if pillar_num not in PILLARS:
            return error("pillar_number must be between 1 and 7")

    pillar_name = data.get("pillar") or (PILLARS.get(pillar_num, "") if pillar_num else "")

    activity = GovernmentActivity(
        activity_number=data.get("activity_number", ""),
        pillar=pillar_name,
        pillar_number=pillar_num,
        sub_section=data.get("sub_section", ""),
        activity_name=name,
        total_cost_usd=float(data.get("total_cost_usd", 0) or 0),
        status=status,
        priority=priority,
        notes=data.get("notes", ""),
    )
    db.session.add(activity)
    db.session.commit()
    return success(activity.to_dict(), "Activity created", 201)


@gov_activities_bp.route("/api/government-activities/<int:activity_id>", methods=["GET"])
def get_gov_activity(activity_id):
    activity = GovernmentActivity.query.get_or_404(activity_id)
    data = activity.to_dict()
    data["partner_contributions"] = [c.to_dict() for c in activity.partner_contributions]
    return success(data)


@gov_activities_bp.route("/api/government-activities/<int:activity_id>", methods=["PUT"])
def update_gov_activity(activity_id):
    activity = GovernmentActivity.query.get_or_404(activity_id)
    data = request.get_json() or {}

    if "activity_name" in data:
        name = (data["activity_name"] or "").strip()
        if name:
            activity.activity_name = name

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return error(f"status must be one of {sorted(VALID_STATUSES)}")
        activity.status = data["status"]

    if "priority" in data:
        if data["priority"] not in VALID_PRIORITIES:
            return error(f"priority must be one of {sorted(VALID_PRIORITIES)}")
        activity.priority = data["priority"]

    for field in ("activity_number", "pillar", "sub_section", "notes"):
        if field in data:
            setattr(activity, field, data[field])

    if "pillar_number" in data and data["pillar_number"] is not None:
        try:
            pnum = int(data["pillar_number"])
        except (TypeError, ValueError):
            return error("pillar_number must be an integer 1–7")
        if pnum not in PILLARS:
            return error("pillar_number must be between 1 and 7")
        activity.pillar_number = pnum

    if "total_cost_usd" in data:
        activity.total_cost_usd = float(data["total_cost_usd"] or 0)

    activity.updated_at = datetime.utcnow()
    db.session.commit()
    return success(activity.to_dict(), "Activity updated")


@gov_activities_bp.route("/api/government-activities/<int:activity_id>", methods=["DELETE"])
def delete_gov_activity(activity_id):
    activity = GovernmentActivity.query.get_or_404(activity_id)
    activity.status = "Suspended"
    activity.updated_at = datetime.utcnow()
    db.session.commit()
    return success({"id": activity_id}, "Activity suspended")
