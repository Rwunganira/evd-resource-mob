from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from models import FundingGap

funding_gap_bp = Blueprint("funding_gap", __name__)


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


@funding_gap_bp.route("/api/funding-gap", methods=["GET"])
def list_funding_gaps():
    gaps = FundingGap.query.order_by(FundingGap.pillar_name).all()
    return success([g.to_dict() for g in gaps])


@funding_gap_bp.route("/api/funding-gap", methods=["POST"])
def create_funding_gap():
    data = request.get_json() or {}
    pillar = (data.get("pillar_name") or "").strip()
    if not pillar:
        return error("pillar_name is required")
    if FundingGap.query.filter_by(pillar_name=pillar).first():
        return error(f"Pillar '{pillar}' already exists — use PUT to update", 409)
    gap = FundingGap(
        pillar_name=pillar,
        amount_required_usd=float(data.get("amount_required_usd", 0) or 0),
        amount_funded_usd=float(data.get("amount_funded_usd", 0) or 0),
        notes=data.get("notes"),
    )
    db.session.add(gap)
    db.session.commit()
    return success(gap.to_dict(), "Pillar created", 201)


@funding_gap_bp.route("/api/funding-gap/<int:gap_id>", methods=["PUT"])
def update_funding_gap(gap_id):
    gap = FundingGap.query.get_or_404(gap_id)
    data = request.get_json() or {}
    if "amount_required_usd" in data:
        gap.amount_required_usd = float(data["amount_required_usd"] or 0)
    if "amount_funded_usd" in data:
        gap.amount_funded_usd = float(data["amount_funded_usd"] or 0)
    if "notes" in data:
        gap.notes = data["notes"]
    gap.last_updated = datetime.utcnow()
    db.session.commit()
    return success(gap.to_dict(), "Pillar updated")


@funding_gap_bp.route("/api/funding-gap/summary", methods=["GET"])
def funding_gap_summary():
    gaps = FundingGap.query.all()
    if not gaps:
        return success({
            "total_required_usd": 0, "total_funded_usd": 0,
            "total_gap_usd": 0, "coverage_pct": 0,
            "top_funded_pillar": None, "pillars": [],
        })
    total_required = sum(g.amount_required_usd for g in gaps)
    total_funded = sum(g.amount_funded_usd for g in gaps)
    total_gap = sum(g.gap_usd for g in gaps)
    coverage = round(total_funded / total_required * 100, 1) if total_required else 0
    top_funded = max(gaps, key=lambda g: g.coverage_pct)
    return success({
        "total_required_usd": total_required,
        "total_funded_usd": total_funded,
        "total_gap_usd": total_gap,
        "coverage_pct": coverage,
        "top_funded_pillar": top_funded.pillar_name,
        "pillars": [g.to_dict() for g in sorted(gaps, key=lambda g: g.gap_usd, reverse=True)],
    })
