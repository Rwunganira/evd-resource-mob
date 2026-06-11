from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from database import db
from models import Activity, Partner

activities_view_bp = Blueprint("activities_view", __name__)


@activities_view_bp.before_request
@login_required
def require_login():
    pass


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
VALID_ACTIVITY_STATUSES = {
    "Planned",
    "Ongoing",
    "Completed",
    "Suspended",
    "Cancelled",
}
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
VALID_TIMELINE_STATUSES = {
    "Not started",
    "In progress",
    "Completed",
    "Delayed",
}
VALID_MODALITIES = {
    "Direct Implementation",
    "Transfer to Government",
    "Both",
}


def _parse_date(val):
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


@activities_view_bp.route("/activities")
def list_activities():
    q = Activity.query
    atype = request.args.get("type")
    status = request.args.get("status")
    location = request.args.get("location")
    pillar = request.args.get("pillar")
    funding_source = request.args.get("funding_source")
    timeline_status = request.args.get("timeline_status")
    modality = request.args.get("modality")
    if atype:
        q = q.filter_by(activity_type=atype)
    if status:
        q = q.filter_by(status=status)
    if location:
        q = q.filter(Activity.location.ilike(f"%{location}%"))
    if pillar:
        q = q.filter_by(pillar=pillar)
    if funding_source:
        q = q.filter_by(funding_source=funding_source)
    if timeline_status:
        q = q.filter_by(timeline_status=timeline_status)
    if modality:
        q = q.filter_by(modality_of_support=modality)
    activities = q.order_by(Activity.start_date.desc()).all()
    return render_template(
        "activities/list.html",
        activities=activities,
        types=sorted(VALID_TYPES),
        pillars=sorted(VALID_PILLARS),
        funding_sources=sorted(VALID_FUNDING_SOURCES),
        timeline_statuses=sorted(VALID_TIMELINE_STATUSES),
        modalities=sorted(VALID_MODALITIES),
    )


@activities_view_bp.route("/activities/new", methods=["GET", "POST"])
def new_activity():
    partners = Partner.query.filter(Partner.status != "Not present").order_by(Partner.name).all()
    if request.method == "POST":
        partner_id = request.form.get("partner_id")
        if not partner_id or not Partner.query.get(int(partner_id)):
            flash("A valid partner is required.", "error")
            return render_template(
                "activities/form.html",
                activity=None,
                partners=partners,
                pillars=sorted(VALID_PILLARS),
                funding_sources=sorted(VALID_FUNDING_SOURCES),
                timeline_statuses=sorted(VALID_TIMELINE_STATUSES),
                modalities=sorted(VALID_MODALITIES),
            )
        location = request.form.get("location", "").strip()
        if not location:
            flash("Location is required.", "error")
            return render_template(
                "activities/form.html",
                activity=None,
                partners=partners,
                pillars=sorted(VALID_PILLARS),
                funding_sources=sorted(VALID_FUNDING_SOURCES),
                timeline_statuses=sorted(VALID_TIMELINE_STATUSES),
                modalities=sorted(VALID_MODALITIES),
            )
        activity = Activity(
            partner_id=int(partner_id),
            activity_type=request.form.get("activity_type", ""),
            location=location,
            district=request.form.get("district", "").strip() or None,
            status=request.form.get("status", "Planned"),
            pillar=request.form.get("pillar") or None,
            funding_source=request.form.get("funding_source") or None,
            timeline_status=request.form.get("timeline_status", "Not started"),
            modality_of_support=request.form.get("modality_of_support") or None,
            description=request.form.get("description", ""),
            start_date=_parse_date(request.form.get("start_date")),
            end_date=_parse_date(request.form.get("end_date")),
            beneficiaries_reached=int(request.form.get("beneficiaries_reached", 0) or 0),
        )
        db.session.add(activity)
        db.session.commit()
        flash("Activity created successfully.", "success")
        return redirect(url_for("activities_view.list_activities"))
    return render_template(
        "activities/form.html",
        activity=None,
        partners=partners,
        pillars=sorted(VALID_PILLARS),
        funding_sources=sorted(VALID_FUNDING_SOURCES),
        timeline_statuses=sorted(VALID_TIMELINE_STATUSES),
        modalities=sorted(VALID_MODALITIES),
    )


@activities_view_bp.route("/activities/<int:activity_id>/edit", methods=["GET", "POST"])
def edit_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    partners = Partner.query.filter(Partner.status != "Not present").order_by(Partner.name).all()
    if activity.partner not in partners:
        partners.append(activity.partner)
    if request.method == "POST":
        activity.activity_type = request.form.get("activity_type", activity.activity_type)
        activity.location = request.form.get("location", activity.location).strip() or activity.location
        activity.district = request.form.get("district", "").strip() or activity.district
        activity.status = request.form.get("status", activity.status)
        activity.pillar = request.form.get("pillar") or activity.pillar
        activity.funding_source = request.form.get("funding_source") or activity.funding_source
        activity.timeline_status = request.form.get("timeline_status", activity.timeline_status)
        activity.modality_of_support = request.form.get("modality_of_support") or activity.modality_of_support
        activity.description = request.form.get("description", activity.description)
        activity.start_date = _parse_date(request.form.get("start_date")) or activity.start_date
        activity.end_date = _parse_date(request.form.get("end_date")) or activity.end_date
        beneficiaries = request.form.get("beneficiaries_reached")
        if beneficiaries is not None:
            activity.beneficiaries_reached = int(beneficiaries or 0)
        db.session.commit()
        flash("Activity updated.", "success")
        return redirect(url_for("activities_view.list_activities"))
    return render_template(
        "activities/form.html",
        activity=activity,
        partners=partners,
        pillars=sorted(VALID_PILLARS),
        funding_sources=sorted(VALID_FUNDING_SOURCES),
        timeline_statuses=sorted(VALID_TIMELINE_STATUSES),
        modalities=sorted(VALID_MODALITIES),
    )
