from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_login import login_required
from database import db
from models import GovernmentActivity, PartnerContribution

gov_activities_bp = Blueprint("gov_activities", __name__)

VALID_STATUSES   = {"Planned", "Active", "Completed", "Suspended"}
VALID_PRIORITIES = {"High", "Medium", "Low"}

TECHNICAL_AREAS = {
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
    total_support = sum(a.total_committed for a in activities)
    total_gap     = sum(a.funding_gap for a in activities)
    coverage      = round(total_support / total_cost * 100, 1) if total_cost else 0

    by_ta = []
    for ta_num, ta_name in sorted(TECHNICAL_AREAS.items()):
        ta_acts = [a for a in activities if a.technical_area_number == ta_num]
        tc = sum(a.total_cost_usd or 0 for a in ta_acts)
        ts = sum(a.total_committed for a in ta_acts)
        tg = sum(a.funding_gap for a in ta_acts)
        by_ta.append({
            "technical_area_number": ta_num,
            "technical_area_name":   ta_name,
            "total_cost":    round(tc, 2),
            "total_support": round(ts, 2),
            "gap":           round(tg, 2),
            "coverage_pct":  round(ts / tc * 100, 1) if tc else 0,
            "activity_count": len(ta_acts),
        })

    return success({
        "total_activities":    len(activities),
        "total_cost_usd":      round(total_cost, 2),
        "total_committed":     round(total_support, 2),
        "total_funding_gap":   round(total_gap, 2),
        "coverage_pct":        coverage,
        "by_technical_area":   by_ta,
    })


@gov_activities_bp.route("/api/government-activities", methods=["GET"])
def list_gov_activities():
    q = GovernmentActivity.query.filter(GovernmentActivity.status != "Suspended")

    technical_area = request.args.get("technical_area")
    status         = request.args.get("status")
    priority       = request.args.get("priority")

    if technical_area:
        q = q.filter(GovernmentActivity.technical_area.ilike(f"%{technical_area}%"))
    if status:
        q = q.filter(GovernmentActivity.status == status)
    if priority:
        q = q.filter(GovernmentActivity.priority == priority)

    activities = q.order_by(
        GovernmentActivity.technical_area_number,
        GovernmentActivity.activity_number,
    ).all()

    grouped: dict = {}
    for a in activities:
        ta_num = a.technical_area_number or 0
        if ta_num not in grouped:
            grouped[ta_num] = {
                "technical_area_number": ta_num,
                "technical_area_name":   TECHNICAL_AREAS.get(ta_num, a.technical_area or ""),
                "activities": [],
            }
        grouped[ta_num]["activities"].append(a.to_dict())

    return success({
        "grouped": list(grouped.values()),
        "flat":    [a.to_dict() for a in activities],
    })


@gov_activities_bp.route("/api/government-activities", methods=["POST"])
@login_required
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

    ta_num = data.get("technical_area_number")
    if ta_num is not None:
        try:
            ta_num = int(ta_num)
        except (TypeError, ValueError):
            return error("technical_area_number must be an integer 1–7")
        if ta_num not in TECHNICAL_AREAS:
            return error("technical_area_number must be between 1 and 7")

    ta_name = data.get("technical_area") or (TECHNICAL_AREAS.get(ta_num, "") if ta_num else "")

    activity = GovernmentActivity(
        activity_number=data.get("activity_number", ""),
        technical_area=ta_name,
        technical_area_number=ta_num,
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
@login_required
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

    for field in ("activity_number", "technical_area", "sub_section", "notes"):
        if field in data:
            setattr(activity, field, data[field])

    if "technical_area_number" in data and data["technical_area_number"] is not None:
        try:
            ta_num = int(data["technical_area_number"])
        except (TypeError, ValueError):
            return error("technical_area_number must be an integer 1–7")
        if ta_num not in TECHNICAL_AREAS:
            return error("technical_area_number must be between 1 and 7")
        activity.technical_area_number = ta_num

    if "total_cost_usd" in data:
        activity.total_cost_usd = float(data["total_cost_usd"] or 0)

    activity.updated_at = datetime.utcnow()
    db.session.commit()
    return success(activity.to_dict(), "Activity updated")


@gov_activities_bp.route("/api/government-activities/<int:activity_id>", methods=["DELETE"])
@login_required
def delete_gov_activity(activity_id):
    activity = GovernmentActivity.query.get_or_404(activity_id)
    activity.status = "Suspended"
    activity.updated_at = datetime.utcnow()
    db.session.commit()
    return success({"id": activity_id}, "Activity suspended")
