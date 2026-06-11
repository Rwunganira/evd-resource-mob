import io
import pandas as pd
from flask import Blueprint, request, jsonify
from database import db
from models import Partner, PartnerPillar, Resource

imports_bp = Blueprint("imports", __name__)

# Maps the Excel column prefix → canonical short pillar name
PILLAR_COLUMN_MAP = {
    "1.Coordination_and_Workforce": "Coordination & Workforce",
    "2.1.Epidemiology_Surveillance_and_Points_of_Entry": "Epi & Surveillance",
    "2.2.Epidemiology_Surveillance_and_Points_of_Entry": "Points of Entry",
    "3.Laboratory_and_Diagnostics": "Laboratory & Diagnostics",
    "4.1.Case_Management_IPC_or_WASH_and_SDB": "WASH, Nutrition & SDB",
    "4.2.Case_Management_IPC_or_WASH_and_SDB": "Clinical Care, IPC & PSS",
    "5.RCCE": "RCCE",
    "6.Operational_Support_and_Logistics": "Operational Support & Logistics",
    "7.Research_and_Strategic_Information": "Research & Strategic Information",
}


def success(data, message="OK", code=200):
    return jsonify({"status": "success", "data": data, "message": message}), code


def error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code


def _safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if v == v else default
    except (TypeError, ValueError):
        return default


def _safe_str(val):
    s = str(val or "").strip()
    return "" if s == "nan" else s


def _match_pillar_columns(df_columns):
    """Return {df_col: canonical_name} for all pillar columns found in df."""
    matched = {}
    for df_col in df_columns:
        col_clean = str(df_col).strip().replace("\n", "").replace(" ", "_")
        for prefix, canonical in PILLAR_COLUMN_MAP.items():
            if col_clean.startswith(prefix):
                matched[df_col] = canonical
                break
    return matched


@imports_bp.route("/api/import/4w-template", methods=["POST"])
def import_4w_template():
    if "file" not in request.files:
        return error("No file uploaded — send as multipart/form-data with key 'file'")
    f = request.files["file"]
    if not f.filename.lower().endswith(".xlsx"):
        return error("File must be .xlsx format")

    imported = 0
    skipped = 0
    errors = []
    preview = []

    try:
        content = f.read()

        # ── Partner Mapping sheet ─────────────────────────────────────────────
        try:
            pm_df = pd.read_excel(io.BytesIO(content), sheet_name="Partner Mapping", header=0)
            pillar_cols = _match_pillar_columns(pm_df.columns)

            for _, row in pm_df.iterrows():
                # Support both old and new header names
                name = _safe_str(
                    row.get("Partner / Organization") or row.get("Institution Agency") or ""
                )
                if not name:
                    continue

                acronym = _safe_str(row.get("Acronym", "")) or None
                ptype = _safe_str(row.get("Type (dropdown)") or row.get("Type") or "UN agency") or "UN agency"
                contact_person = _safe_str(row.get("Name", "")) or None
                contact_phone = _safe_str(row.get("Phone", "")) or None
                contact_email = _safe_str(row.get("Email", "")) or None

                # Pillar TWGs this contact row voted "Yes" on
                row_pillars = [
                    canonical
                    for df_col, canonical in pillar_cols.items()
                    if _safe_str(row.get(df_col, "")).lower() == "yes"
                ]

                existing = Partner.query.filter_by(name=name).first()
                if existing:
                    # Merge new pillar TWGs onto existing partner
                    existing_pillars = {p.pillar_name for p in existing.pillar_twgs}
                    for pillar in row_pillars:
                        if pillar not in existing_pillars:
                            db.session.add(PartnerPillar(partner_id=existing.id, pillar_name=pillar))
                    skipped += 1
                    continue

                partner = Partner(
                    name=name,
                    acronym=acronym,
                    partner_type=ptype,
                    country=_safe_str(row.get("Country", "")),
                    contact_person=contact_person,
                    contact_phone=contact_phone,
                    contact_email=contact_email,
                    status="Operational",
                )
                db.session.add(partner)
                db.session.flush()
                for pillar in row_pillars:
                    db.session.add(PartnerPillar(partner_id=partner.id, pillar_name=pillar))
                imported += 1

        except Exception as exc:
            errors.append(f"Partner Mapping sheet skipped: {exc}")

        db.session.flush()

        # ── Partner Support sheet ─────────────────────────────────────────────
        try:
            ps_df = pd.read_excel(io.BytesIO(content), sheet_name="Partner support", header=0)
            for _, row in ps_df.iterrows():
                agency = _safe_str(
                    row.get("Partner / Organization") or row.get("Institution Agency") or ""
                )
                if not agency:
                    continue
                partner = Partner.query.filter_by(name=agency).first()
                if not partner:
                    partner = Partner(name=agency, partner_type="UN agency", country="", status="Operational")
                    db.session.add(partner)
                    db.session.flush()

                amount_pledged = _safe_float(row.get("Amount pledged (Total)"))
                amount_disbursed = _safe_float(row.get("Amount Disbursed"))
                description = _safe_str(row.get("Intervention/Activity", ""))

                resource = Resource(
                    partner_id=partner.id,
                    resource_type="Funding",
                    description=description,
                    amount=amount_pledged,
                    currency="USD",
                    status="Deployed" if amount_disbursed > 0 else "Committed",
                    reporting_frequency="Monthly",
                )
                db.session.add(resource)
                preview.append({
                    "partner": agency,
                    "description": description,
                    "amount_pledged": amount_pledged,
                    "amount_disbursed": amount_disbursed,
                    "status": resource.status,
                })
                imported += 1

        except Exception as exc:
            errors.append(f"Partner support sheet skipped: {exc}")

        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        return error(f"Import failed: {exc}", 500)

    return success(
        {"imported": imported, "skipped": skipped, "errors": errors, "preview": preview[:20]},
        f"Import complete: {imported} records imported, {skipped} skipped",
    )
