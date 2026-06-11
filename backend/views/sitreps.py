from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date, datetime
from database import db
from models import SituationReport

sitreps_view_bp = Blueprint("sitreps_view", __name__)


@sitreps_view_bp.before_request
@login_required
def require_login():
    pass


def _parse_date(val):
    if not val:
        return date.today()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return date.today()


@sitreps_view_bp.route("/sitreps")
def list_sitreps():
    sitreps = SituationReport.query.order_by(SituationReport.report_date.desc()).all()
    return render_template("sitreps/list.html", sitreps=sitreps)


@sitreps_view_bp.route("/sitreps/new", methods=["GET", "POST"])
def new_sitrep():
    if request.method == "POST":
        outbreak_day = request.form.get("outbreak_day")
        if not outbreak_day:
            flash("Outbreak day is required.", "error")
            return redirect(url_for("sitreps_view.new_sitrep"))
        confirmed = int(request.form.get("confirmed_cases", 0) or 0)
        deaths = int(request.form.get("deaths", 0) or 0)
        if deaths > confirmed:
            flash("Deaths cannot exceed confirmed cases.", "error")
            return redirect(url_for("sitreps_view.new_sitrep"))
        sitrep = SituationReport(
            report_date=_parse_date(request.form.get("report_date")),
            outbreak_day=int(outbreak_day),
            confirmed_cases=confirmed,
            deaths=deaths,
            healthcare_workers_affected=int(request.form.get("healthcare_workers_affected", 0) or 0),
            etus_operational=int(request.form.get("etus_operational", 0) or 0),
            total_funding_mobilized=float(request.form.get("total_funding_mobilized", 0) or 0),
            funding_gap=float(request.form.get("funding_gap", 0) or 0),
            notes=request.form.get("notes", ""),
            created_by=request.form.get("created_by", ""),
        )
        db.session.add(sitrep)
        db.session.commit()
        flash("Situation report submitted.", "success")
        return redirect(url_for("sitreps_view.list_sitreps"))
    return render_template("sitreps/form.html", today=date.today())
