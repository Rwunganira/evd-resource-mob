from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
from sqlalchemy import func
from database import db
from models import Resource, Partner

resources_bp = Blueprint("resources", __name__)

VALID_TYPES = {"Funding", "PPE", "Personnel", "Vaccines", "Logistics", "Technical"}
VALID_STATUSES = {"Committed", "Deployed", "Pipeline", "Under Review"}
VALID_CURRENCIES = {"USD", "EUR", "GBP", "In-kind"}
VALID_FREQ = {"Daily", "Weekly", "Biweekly", "Monthly", "Quarterly"}


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


def _parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


@resources_bp.route("/api/resources", methods=["GET"])
def list_resources():
    q = Resource.query
    rtype = request.args.get("type")
    status = request.args.get("status")
    partner_id = request.args.get("partner_id")
    if rtype:
        q = q.filter_by(resource_type=rtype)
    if status:
        q = q.filter_by(status=status)
    if partner_id:
        q = q.filter_by(partner_id=int(partner_id))
    resources = q.order_by(Resource.commitment_date.desc()).all()
    return success([r.to_dict() for r in resources])


@resources_bp.route("/api/resources", methods=["POST"])
def create_resource():
    data = request.get_json() or {}
    partner_id = data.get("partner_id")
    if not partner_id or not Partner.query.get(partner_id):
        return error("Valid partner_id is required")
    rtype = data.get("resource_type", "Funding")
    if rtype not in VALID_TYPES:
        return error(f"resource_type must be one of {sorted(VALID_TYPES)}")
    status = data.get("status", "Pipeline")
    if status not in VALID_STATUSES:
        return error(f"status must be one of {sorted(VALID_STATUSES)}")
    currency = data.get("currency", "USD")
    if currency not in VALID_CURRENCIES:
        return error(f"currency must be one of {sorted(VALID_CURRENCIES)}")
    freq = data.get("reporting_frequency", "Monthly")
    if freq not in VALID_FREQ:
        return error(f"reporting_frequency must be one of {sorted(VALID_FREQ)}")

    resource = Resource(
        partner_id=partner_id,
        resource_type=rtype,
        description=data.get("description", ""),
        amount=float(data.get("amount", 0)),
        currency=currency,
        commitment_date=_parse_date(data.get("commitment_date")),
        deployment_date=_parse_date(data.get("deployment_date")),
        status=status,
        reporting_frequency=freq,
        next_report_due=_parse_date(data.get("next_report_due")),
    )
    db.session.add(resource)
    db.session.commit()
    return success(resource.to_dict(), "Resource created", 201)


@resources_bp.route("/api/resources/<int:resource_id>", methods=["PUT"])
def update_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    data = request.get_json() or {}
    if "resource_type" in data:
        if data["resource_type"] not in VALID_TYPES:
            return error(f"resource_type must be one of {sorted(VALID_TYPES)}")
        resource.resource_type = data["resource_type"]
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return error(f"status must be one of {sorted(VALID_STATUSES)}")
        resource.status = data["status"]
    for field in ("description", "amount", "currency", "reporting_frequency"):
        if field in data:
            setattr(resource, field, data[field])
    for dfield in ("commitment_date", "deployment_date", "next_report_due"):
        if dfield in data:
            setattr(resource, dfield, _parse_date(data[dfield]))
    db.session.commit()
    return success(resource.to_dict(), "Resource updated")


@resources_bp.route("/api/resources/total-by-type", methods=["GET"])
def total_by_type():
    rows = (
        db.session.query(Resource.resource_type, func.sum(Resource.amount).label("total"))
        .filter(Resource.currency == "USD")
        .group_by(Resource.resource_type)
        .all()
    )
    return success({rtype: float(total or 0) for rtype, total in rows})


@resources_bp.route("/api/resources/funding-gap", methods=["GET"])
def funding_gap():
    committed = (
        db.session.query(func.sum(Resource.amount))
        .filter(Resource.resource_type == "Funding", Resource.currency == "USD",
                Resource.status.in_(["Committed", "Deployed"]))
        .scalar() or 0
    )
    deployed = (
        db.session.query(func.sum(Resource.amount))
        .filter(Resource.resource_type == "Funding", Resource.currency == "USD",
                Resource.status == "Deployed")
        .scalar() or 0
    )
    needed = float(request.args.get("needed", 50_000_000))
    return success({
        "total_committed_usd": float(committed),
        "total_deployed_usd": float(deployed),
        "estimated_need_usd": needed,
        "gap_usd": max(0, needed - float(committed)),
        "coverage_percent": round(float(committed) / needed * 100, 1) if needed else 0,
    })


@resources_bp.route("/api/resources/reporting-due", methods=["GET"])
def reporting_due():
    days_ahead = int(request.args.get("days", 7))
    cutoff = date.today() + timedelta(days=days_ahead)
    resources = (
        Resource.query
        .filter(Resource.next_report_due <= cutoff, Resource.next_report_due >= date.today())
        .order_by(Resource.next_report_due)
        .all()
    )
    overdue = (
        Resource.query
        .filter(Resource.next_report_due < date.today())
        .order_by(Resource.next_report_due)
        .all()
    )
    return success({
        "due_soon": [r.to_dict() for r in resources],
        "overdue": [r.to_dict() for r in overdue],
    })
