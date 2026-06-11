from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from database import db
from models import Partner, PartnerPillar

partners_view_bp = Blueprint("partners_view", __name__)

VALID_TYPES = {
    "UN agency", "International NGO", "National NGO", "Government / MoH",
    "Bilateral donor", "Red Cross / Red Crescent", "Academic / Research",
    "Private sector", "Faith-based organization", "Community-based organization",
}
VALID_STATUSES = {"Operational", "Mobilizing", "On stand-by", "Withdrawing", "Not present"}
PILLAR_TWGS = [
    "Coordination & Workforce",
    "Epi & Surveillance",
    "Points of Entry",
    "Laboratory & Diagnostics",
    "WASH, Nutrition & SDB",
    "Clinical Care, IPC & PSS",
    "RCCE",
    "Operational Support & Logistics",
    "Research & Strategic Information",
]


@partners_view_bp.route("/partners")
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
    return render_template(
        "partners/list.html",
        partners=partners,
        types=sorted(VALID_TYPES),
        statuses=sorted(VALID_STATUSES),
    )


@partners_view_bp.route("/partners/new", methods=["GET", "POST"])
def new_partner():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Partner name is required.", "error")
            return render_template("partners/form.html", partner=None,
                                   types=sorted(VALID_TYPES), statuses=sorted(VALID_STATUSES),
                                   pillar_twgs=PILLAR_TWGS)
        if Partner.query.filter_by(name=name).first():
            flash(f"Partner '{name}' already exists.", "error")
            return render_template("partners/form.html", partner=None,
                                   types=sorted(VALID_TYPES), statuses=sorted(VALID_STATUSES),
                                   pillar_twgs=PILLAR_TWGS)
        partner = Partner(
            name=name,
            acronym=request.form.get("acronym") or None,
            partner_type=request.form.get("partner_type", "UN agency"),
            country=request.form.get("country", ""),
            contact_person=request.form.get("contact_person") or None,
            contact_phone=request.form.get("contact_phone") or None,
            contact_email=request.form.get("contact_email") or None,
            status=request.form.get("status", "Mobilizing"),
        )
        db.session.add(partner)
        db.session.flush()
        for pillar in request.form.getlist("pillar_twgs"):
            db.session.add(PartnerPillar(partner_id=partner.id, pillar_name=pillar))
        db.session.commit()
        flash(f"Partner '{name}' created successfully.", "success")
        return redirect(url_for("partners_view.list_partners"))
    return render_template(
        "partners/form.html",
        partner=None,
        types=sorted(VALID_TYPES),
        statuses=sorted(VALID_STATUSES),
        pillar_twgs=PILLAR_TWGS,
    )


@partners_view_bp.route("/partners/<int:partner_id>/edit", methods=["GET", "POST"])
def edit_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            partner.name = name
        partner.acronym = request.form.get("acronym") or partner.acronym
        partner.partner_type = request.form.get("partner_type", partner.partner_type)
        partner.status = request.form.get("status", partner.status)
        partner.country = request.form.get("country", partner.country)
        partner.contact_person = request.form.get("contact_person") or partner.contact_person
        partner.contact_phone = request.form.get("contact_phone") or partner.contact_phone
        partner.contact_email = request.form.get("contact_email") or partner.contact_email
        PartnerPillar.query.filter_by(partner_id=partner.id).delete()
        for pillar in request.form.getlist("pillar_twgs"):
            db.session.add(PartnerPillar(partner_id=partner.id, pillar_name=pillar))
        partner.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f"Partner '{partner.name}' updated.", "success")
        return redirect(url_for("partners_view.list_partners"))
    return render_template(
        "partners/form.html",
        partner=partner,
        types=sorted(VALID_TYPES),
        statuses=sorted(VALID_STATUSES),
        pillar_twgs=PILLAR_TWGS,
    )


@partners_view_bp.route("/partners/<int:partner_id>/delete", methods=["POST"])
def delete_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    partner.status = "Not present"
    partner.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f"Partner '{partner.name}' deactivated.", "success")
    return redirect(url_for("partners_view.list_partners"))
