from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date, datetime
from database import db
from models import Resource, Partner

resources_view_bp = Blueprint("resources_view", __name__)


@resources_view_bp.before_request
@login_required
def require_login():
    pass


def _parse_date(val):
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


@resources_view_bp.route("/resources")
def list_resources():
    q = Resource.query
    rtype = request.args.get("type")
    status = request.args.get("status")
    partner_name = request.args.get("partner")
    if rtype:
        q = q.filter_by(resource_type=rtype)
    if status:
        q = q.filter_by(status=status)
    if partner_name:
        q = q.join(Partner).filter(Partner.name.ilike(f"%{partner_name}%"))
    resources = q.order_by(Resource.commitment_date.desc()).all()
    return render_template(
        "resources/list.html",
        resources=resources,
        today=date.today(),
        types=["Funding", "PPE", "Personnel", "Vaccines", "Logistics", "Technical"],
        statuses=["Pipeline", "Committed", "Deployed", "Under Review"],
    )


@resources_view_bp.route("/resources/new", methods=["GET", "POST"])
def new_resource():
    partners = Partner.query.filter(Partner.status != "Inactive").order_by(Partner.name).all()
    if request.method == "POST":
        partner_id = request.form.get("partner_id")
        if not partner_id or not Partner.query.get(int(partner_id)):
            flash("A valid partner is required.", "error")
            return render_template("resources/form.html", resource=None, partners=partners)
        resource = Resource(
            partner_id=int(partner_id),
            resource_type=request.form.get("resource_type", "Funding"),
            description=request.form.get("description", ""),
            amount=float(request.form.get("amount", 0) or 0),
            currency=request.form.get("currency", "USD"),
            status=request.form.get("status", "Pipeline"),
            reporting_frequency=request.form.get("reporting_frequency", "Monthly"),
            commitment_date=_parse_date(request.form.get("commitment_date")),
            deployment_date=_parse_date(request.form.get("deployment_date")),
            next_report_due=_parse_date(request.form.get("next_report_due")),
        )
        db.session.add(resource)
        db.session.commit()
        flash("Resource created successfully.", "success")
        return redirect(url_for("resources_view.list_resources"))
    return render_template("resources/form.html", resource=None, partners=partners)


@resources_view_bp.route("/resources/<int:resource_id>/edit", methods=["GET", "POST"])
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    partners = Partner.query.filter(Partner.status != "Inactive").order_by(Partner.name).all()
    if resource.partner not in partners:
        partners.append(resource.partner)
    if request.method == "POST":
        resource.resource_type = request.form.get("resource_type", resource.resource_type)
        resource.status = request.form.get("status", resource.status)
        resource.description = request.form.get("description", resource.description)
        resource.amount = float(request.form.get("amount", resource.amount) or resource.amount)
        resource.currency = request.form.get("currency", resource.currency)
        resource.reporting_frequency = request.form.get("reporting_frequency", resource.reporting_frequency)
        resource.commitment_date = _parse_date(request.form.get("commitment_date")) or resource.commitment_date
        resource.deployment_date = _parse_date(request.form.get("deployment_date")) or resource.deployment_date
        resource.next_report_due = _parse_date(request.form.get("next_report_due")) or resource.next_report_due
        db.session.commit()
        flash("Resource updated.", "success")
        return redirect(url_for("resources_view.list_resources"))
    return render_template("resources/form.html", resource=resource, partners=partners)
