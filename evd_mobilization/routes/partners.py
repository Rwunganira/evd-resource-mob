from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from models import Partner

partners_bp = Blueprint("partners", __name__)

VALID_TYPES = {"Government", "NGO", "Private", "Academic", "Military", "Community"}
VALID_STATUSES = {"Active", "Negotiating", "Pipeline", "Inactive"}


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


@partners_bp.route("/api/partners/summary", methods=["GET"])
def partners_summary():
    partners = Partner.query.filter(Partner.status != "Inactive").all()
    by_type = {}
    by_status = {}
    for p in Partner.query.all():
        by_type[p.partner_type] = by_type.get(p.partner_type, 0) + 1
        by_status[p.status] = by_status.get(p.status, 0) + 1
    return success({
        "total": Partner.query.count(),
        "active": Partner.query.filter_by(status="Active").count(),
        "by_type": by_type,
        "by_status": by_status,
    })


@partners_bp.route("/api/partners", methods=["GET"])
def list_partners():
    q = Partner.query
    ptype = request.args.get("type")
    status = request.args.get("status")
    country = request.args.get("country")
    if ptype:
        q = q.filter_by(partner_type=ptype)
    if status:
        q = q.filter_by(status=status)
    if country:
        q = q.filter(Partner.country.ilike(f"%{country}%"))
    partners = q.order_by(Partner.name).all()
    return success([p.to_dict() for p in partners])


@partners_bp.route("/api/partners", methods=["POST"])
def create_partner():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return error("Partner name is required")
    ptype = data.get("partner_type", "NGO")
    if ptype not in VALID_TYPES:
        return error(f"partner_type must be one of {sorted(VALID_TYPES)}")
    status = data.get("status", "Pipeline")
    if status not in VALID_STATUSES:
        return error(f"status must be one of {sorted(VALID_STATUSES)}")
    if Partner.query.filter_by(name=name).first():
        return error(f"Partner '{name}' already exists", 409)
    partner = Partner(
        name=name,
        partner_type=ptype,
        country=data.get("country", ""),
        contact_person=data.get("contact_person"),
        contact_email=data.get("contact_email"),
        status=status,
    )
    db.session.add(partner)
    db.session.commit()
    return success(partner.to_dict(), "Partner created", 201)


@partners_bp.route("/api/partners/<int:partner_id>", methods=["GET"])
def get_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    data = partner.to_dict()
    data["resources"] = [r.to_dict() for r in partner.resources]
    data["activities"] = [a.to_dict() for a in partner.activities]
    return success(data)


@partners_bp.route("/api/partners/<int:partner_id>", methods=["PUT"])
def update_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    data = request.get_json() or {}
    if "name" in data and data["name"].strip():
        partner.name = data["name"].strip()
    if "partner_type" in data:
        if data["partner_type"] not in VALID_TYPES:
            return error(f"partner_type must be one of {sorted(VALID_TYPES)}")
        partner.partner_type = data["partner_type"]
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return error(f"status must be one of {sorted(VALID_STATUSES)}")
        partner.status = data["status"]
    for field in ("country", "contact_person", "contact_email"):
        if field in data:
            setattr(partner, field, data[field])
    partner.updated_at = datetime.utcnow()
    db.session.commit()
    return success(partner.to_dict(), "Partner updated")


@partners_bp.route("/api/partners/<int:partner_id>", methods=["DELETE"])
def delete_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    partner.status = "Inactive"
    partner.updated_at = datetime.utcnow()
    db.session.commit()
    return success({"id": partner_id}, "Partner deactivated")
