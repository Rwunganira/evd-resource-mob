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
VALID_PILLARS = {
    "Coordination",
    "Surveillance",
    "Laboratory",
    "Case Management",
    "RCCE",
    "Logistics",
    "Research",
}
VALID_STATUSES = {"Planned", "Ongoing", "Completed", "Suspended", "Cancelled"}
VALID_FUNDING_SOURCES = {
    "Internal / own funds",
    "CFE (WHO)",
    "CERF",
    "Bilateral donor",
    "Country pooled fund",
    "Private donor",
    "Unfunded-gap",
    "Mixed",
}
VALID_TIMELINE_STATUSES = {"Not started", "In progress", "Completed", "Delayed"}
VALID_MODALITIES = {"Direct Implementation", "Transfer to Government", "Both"}


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
    pillar = request.args.get("pillar")
    funding_source = request.args.get("funding_source")
    timeline_status = request.args.get("timeline_status")
    modality = request.args.get("modality")
    partner_id = request.args.get("partner_id")
    if location:
        q = q.filter(Activity.location.ilike(f"%{location}%"))
    if atype:
        q = q.filter_by(activity_type=atype)
    if status:
        q = q.filter_by(status=status)
    if pillar:
        q = q.filter_by(pillar=pillar)
    if funding_source:
        q = q.filter_by(funding_source=funding_source)
    if timeline_status:
        q = q.filter_by(timeline_status=timeline_status)
    if modality:
        q = q.filter_by(modality_of_support=modality)
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

    pillar = data.get("pillar")
    funding_source = data.get("funding_source")
    timeline_status = data.get("timeline_status", "Not started")
    modality = data.get("modality_of_support")
    if pillar is not None and pillar not in VALID_PILLARS:
        return error(f"pillar must be one of {sorted(VALID_PILLARS)}")
    if funding_source is not None and funding_source not in VALID_FUNDING_SOURCES:
        return error(f"funding_source must be one of {sorted(VALID_FUNDING_SOURCES)}")
    if timeline_status not in VALID_TIMELINE_STATUSES:
        return error(f"timeline_status must be one of {sorted(VALID_TIMELINE_STATUSES)}")
    if modality is not None and modality not in VALID_MODALITIES:
        return error(f"modality_of_support must be one of {sorted(VALID_MODALITIES)}")

    activity = Activity(
        partner_id=partner_id,
        activity_type=atype,
        location=location,
        district=data.get("district"),
        start_date=_parse_date(data.get("start_date")),
        end_date=_parse_date(data.get("end_date")),
        status=status,
        pillar=pillar,
        funding_source=funding_source,
        timeline_status=timeline_status,
        modality_of_support=modality,
        description=data.get("description", ""),
        beneficiaries_reached=int(data.get("beneficiaries_reached", 0) or 0),
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
    if "pillar" in data:
        if data["pillar"] is not None and data["pillar"] not in VALID_PILLARS:
            return error(f"pillar must be one of {sorted(VALID_PILLARS)}")
        activity.pillar = data["pillar"]
    if "funding_source" in data:
        if data["funding_source"] is not None and data["funding_source"] not in VALID_FUNDING_SOURCES:
            return error(f"funding_source must be one of {sorted(VALID_FUNDING_SOURCES)}")
        activity.funding_source = data["funding_source"]
    if "timeline_status" in data:
        if data["timeline_status"] not in VALID_TIMELINE_STATUSES:
            return error(f"timeline_status must be one of {sorted(VALID_TIMELINE_STATUSES)}")
        activity.timeline_status = data["timeline_status"]
    if "modality_of_support" in data:
        if data["modality_of_support"] is not None and data["modality_of_support"] not in VALID_MODALITIES:
            return error(f"modality_of_support must be one of {sorted(VALID_MODALITIES)}")
        activity.modality_of_support = data["modality_of_support"]
    for field in ("location", "district", "description"):
        if field in data:
            setattr(activity, field, data[field])
    if "beneficiaries_reached" in data:
        activity.beneficiaries_reached = int(data["beneficiaries_reached"] or 0)
    for dfield in ("start_date", "end_date"):
        if dfield in data:
            setattr(activity, dfield, _parse_date(data[dfield]))
    db.session.commit()
    return success(activity.to_dict(), "Activity updated")


@activities_bp.route("/api/activities/3w-matrix", methods=["GET"])
def three_w_matrix():
    activities = Activity.query.filter(Activity.status != "Completed").all()
    matrix = defaultdict(lambda: defaultdict(list))
    locations, activity_types = set(), set()
    for a in activities:
        matrix[a.location][a.activity_type].append(a.partner.name if a.partner else "Unknown")
        locations.add(a.location)
        activity_types.add(a.activity_type)

    result = {}
    for loc in sorted(locations):
        result[loc] = {atype: matrix[loc].get(atype, []) for atype in sorted(activity_types)}

    return success({
        "matrix": result,
        "locations": sorted(locations),
        "activity_types": sorted(activity_types),
    })


@activities_bp.route("/api/activities/4w-matrix", methods=["GET"])
def four_w_matrix():
    """Who does What Where When — extended with district, dates, beneficiaries."""
    q = Activity.query
    location = request.args.get("location")
    district = request.args.get("district")
    atype = request.args.get("type")
    status = request.args.get("status")
    partner_id = request.args.get("partner_id")
    if location:
        q = q.filter(Activity.location.ilike(f"%{location}%"))
    if district:
        q = q.filter(Activity.district.ilike(f"%{district}%"))
    if atype:
        q = q.filter_by(activity_type=atype)
    if status:
        q = q.filter_by(status=status)
    if partner_id:
        q = q.filter_by(partner_id=int(partner_id))

    activities = q.order_by(Activity.start_date.desc()).all()

    # Build nested matrix AND flat list
    matrix = defaultdict(lambda: defaultdict(list))
    locations, activity_types = set(), set()
    flat = []
    for a in activities:
        partner_name = a.partner.name if a.partner else "Unknown"
        matrix[a.location][a.activity_type].append(partner_name)
        locations.add(a.location)
        activity_types.add(a.activity_type)
        flat.append({
            "partner_name": partner_name,
            "activity_type": a.activity_type,
            "pillar": a.pillar,
            "location": a.location,
            "district": a.district,
            "start_date": a.start_date.isoformat() if a.start_date else None,
            "end_date": a.end_date.isoformat() if a.end_date else None,
            "status": a.status,
            "timeline_status": a.timeline_status,
            "funding_source": a.funding_source,
            "modality_of_support": a.modality_of_support,
            "beneficiaries_reached": a.beneficiaries_reached or 0,
            "description": a.description,
        })

    matrix_result = {}
    for loc in sorted(locations):
        matrix_result[loc] = {atype: matrix[loc].get(atype, []) for atype in sorted(activity_types)}

    return success({
        "matrix": matrix_result,
        "locations": sorted(locations),
        "activity_types": sorted(activity_types),
        "flat": flat,
    })


@activities_bp.route("/api/activities/4w-matrix/export", methods=["GET"])
def four_w_export():
    """CSV-ready flat list of all activities for export."""
    activities = Activity.query.order_by(Activity.location, Activity.activity_type).all()
    flat = [
        {
            "partner_name": a.partner.name if a.partner else "",
            "activity_type": a.activity_type,
            "pillar": a.pillar or "",
            "location": a.location,
            "district": a.district or "",
            "start_date": a.start_date.isoformat() if a.start_date else "",
            "end_date": a.end_date.isoformat() if a.end_date else "",
            "status": a.status,
            "timeline_status": a.timeline_status,
            "funding_source": a.funding_source or "",
            "modality_of_support": a.modality_of_support or "",
            "beneficiaries_reached": a.beneficiaries_reached or 0,
            "description": a.description or "",
        }
        for a in activities
    ]
    return success(flat, f"{len(flat)} activities")
