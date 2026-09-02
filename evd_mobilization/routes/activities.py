from flask import Blueprint, request, jsonify
from datetime import datetime
from collections import defaultdict
from database import db
from models import Activity, Partner

activities_bp = Blueprint("activities", __name__)

VALID_TYPES = {
    "ETU Operations", "Contact Tracing", "Vaccination",
    "Lab", "Community Engagement", "Logistics",
}
VALID_STATUSES = {"Planned", "Ongoing", "Completed"}


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


def _parse_date(val):
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


@activities_bp.route("/api/activities", methods=["GET"])
def list_activities():
    q = Activity.query
    location = request.args.get("location")
    atype = request.args.get("type")
    status = request.args.get("status")
    partner_id = request.args.get("partner_id")
    if location:
        q = q.filter(Activity.location.ilike(f"%{location}%"))
    if atype:
        q = q.filter_by(activity_type=atype)
    if status:
        q = q.filter_by(status=status)
    if partner_id:
        q = q.filter_by(partner_id=int(partner_id))
    activities = q.order_by(Activity.start_date.desc()).all()
    return success([a.to_dict() for a in activities])


@activities_bp.route("/api/activities", methods=["POST"])
def create_activity():
    data = request.get_json() or {}
    partner_id = data.get("partner_id")
    if not partner_id or not Partner.query.get(partner_id):
        return error("Valid partner_id is required")
    atype = data.get("activity_type", "")
    if atype not in VALID_TYPES:
        return error(f"activity_type must be one of {sorted(VALID_TYPES)}")
    location = (data.get("location") or "").strip()
    if not location:
        return error("location is required")
    status = data.get("status", "Planned")
    if status not in VALID_STATUSES:
        return error(f"status must be one of {sorted(VALID_STATUSES)}")

    activity = Activity(
        partner_id=partner_id,
        activity_type=atype,
        location=location,
        start_date=_parse_date(data.get("start_date")),
        end_date=_parse_date(data.get("end_date")),
        status=status,
        description=data.get("description", ""),
    )
    db.session.add(activity)
    db.session.commit()
    return success(activity.to_dict(), "Activity created", 201)


@activities_bp.route("/api/activities/<int:activity_id>", methods=["PUT"])
def update_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    data = request.get_json() or {}
    if "activity_type" in data:
        if data["activity_type"] not in VALID_TYPES:
            return error(f"activity_type must be one of {sorted(VALID_TYPES)}")
        activity.activity_type = data["activity_type"]
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return error(f"status must be one of {sorted(VALID_STATUSES)}")
        activity.status = data["status"]
    for field in ("location", "description"):
        if field in data:
            setattr(activity, field, data[field])
    for dfield in ("start_date", "end_date"):
        if dfield in data:
            setattr(activity, dfield, _parse_date(data[dfield]))
    db.session.commit()
    return success(activity.to_dict(), "Activity updated")


@activities_bp.route("/api/activities/3w-matrix", methods=["GET"])
def three_w_matrix():
    """Who does What Where — returns a nested dict for table rendering."""
    activities = Activity.query.filter(Activity.status != "Completed").all()
    # matrix[location][activity_type] = [partner names]
    matrix = defaultdict(lambda: defaultdict(list))
    locations = set()
    activity_types = set()
    for a in activities:
        loc = a.location
        atype = a.activity_type
        partner_name = a.partner.name if a.partner else "Unknown"
        matrix[loc][atype].append(partner_name)
        locations.add(loc)
        activity_types.add(atype)

    # Flatten for JSON
    result = {}
    for loc in sorted(locations):
        result[loc] = {}
        for atype in sorted(activity_types):
            partners = matrix[loc].get(atype, [])
            result[loc][atype] = partners

    return success({
        "matrix": result,
        "locations": sorted(locations),
        "activity_types": sorted(activity_types),
    })
