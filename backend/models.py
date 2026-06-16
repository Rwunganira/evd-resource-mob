from datetime import datetime, date
from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # roles: admin, editor, viewer
    role = db.Column(db.String(50), nullable=False, default="viewer")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Partner(db.Model):
    __tablename__ = "partners"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    acronym = db.Column(db.String(50))
    partner_type = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(150))
    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(150))
    status = db.Column(db.String(50), nullable=False, default="Mobilizing")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resources = db.relationship("Resource", backref="partner", lazy=True, cascade="all, delete-orphan")
    activities = db.relationship("Activity", backref="partner", lazy=True, cascade="all, delete-orphan")
    pillar_twgs = db.relationship("PartnerPillar", backref="partner", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "acronym": self.acronym,
            "partner_type": self.partner_type,
            "country": self.country,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "status": self.status,
            "pillar_twgs": [p.pillar_name for p in self.pillar_twgs],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resource_count": len(self.resources),
            "activity_count": len(self.activities),
        }

    def __repr__(self):
        return f"<Partner {self.name} ({self.partner_type})>"


class PartnerPillar(db.Model):
    __tablename__ = "partner_pillars"

    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("partners.id"), nullable=False)
    pillar_name = db.Column(db.String(100), nullable=False)

    __table_args__ = (db.UniqueConstraint("partner_id", "pillar_name", name="uq_partner_pillar"),)

    def __repr__(self):
        return f"<PartnerPillar partner={self.partner_id} pillar={self.pillar_name}>"


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("partners.id"), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(20), default="USD")
    commitment_date = db.Column(db.Date)
    deployment_date = db.Column(db.Date)
    status = db.Column(db.String(50), nullable=False, default="Pipeline")
    reporting_frequency = db.Column(db.String(50), default="Monthly")
    next_report_due = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "partner_name": self.partner.name if self.partner else None,
            "resource_type": self.resource_type,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "commitment_date": self.commitment_date.isoformat() if self.commitment_date else None,
            "deployment_date": self.deployment_date.isoformat() if self.deployment_date else None,
            "status": self.status,
            "reporting_frequency": self.reporting_frequency,
            "next_report_due": self.next_report_due.isoformat() if self.next_report_due else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Resource {self.resource_type} ${self.amount} ({self.status})>"


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("partners.id"), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), nullable=False, default="Planned")
    pillar = db.Column(db.String(100))
    funding_source = db.Column(db.String(100))
    timeline_status = db.Column(db.String(50), nullable=False, default="Not started")
    modality_of_support = db.Column(db.String(50))
    description = db.Column(db.Text)
    beneficiaries_reached = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "partner_name": self.partner.name if self.partner else None,
            "activity_type": self.activity_type,
            "location": self.location,
            "district": self.district,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "pillar": self.pillar,
            "funding_source": self.funding_source,
            "timeline_status": self.timeline_status,
            "modality_of_support": self.modality_of_support,
            "description": self.description,
            "beneficiaries_reached": self.beneficiaries_reached or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Activity {self.activity_type} @ {self.location} ({self.status})>"


class SituationReport(db.Model):
    __tablename__ = "situation_reports"

    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False, default=date.today)
    outbreak_day = db.Column(db.Integer, nullable=False)
    confirmed_cases = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    healthcare_workers_affected = db.Column(db.Integer, default=0)
    etus_operational = db.Column(db.Integer, default=0)
    total_funding_mobilized = db.Column(db.Float, default=0.0)
    funding_gap = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        cfr = round((self.deaths / self.confirmed_cases * 100), 1) if self.confirmed_cases else 0
        return {
            "id": self.id,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "outbreak_day": self.outbreak_day,
            "confirmed_cases": self.confirmed_cases,
            "deaths": self.deaths,
            "cfr_percent": cfr,
            "healthcare_workers_affected": self.healthcare_workers_affected,
            "etus_operational": self.etus_operational,
            "total_funding_mobilized": self.total_funding_mobilized,
            "funding_gap": self.funding_gap,
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<SituationReport Day {self.outbreak_day} — {self.confirmed_cases} cases>"


class OutbreakPhase(db.Model):
    __tablename__ = "outbreak_phases"

    id = db.Column(db.Integer, primary_key=True)
    phase_name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "phase_name": self.phase_name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_current": self.is_current,
            "description": self.description,
        }

    def __repr__(self):
        return f"<OutbreakPhase {self.phase_name} (current={self.is_current})>"


class FundingGap(db.Model):
    __tablename__ = "funding_gaps"

    id = db.Column(db.Integer, primary_key=True)
    pillar_name = db.Column(db.String(100), nullable=False, unique=True)
    amount_required_usd = db.Column(db.Float, nullable=False, default=0.0)
    amount_funded_usd = db.Column(db.Float, nullable=False, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)

    @property
    def gap_usd(self):
        return max(0.0, self.amount_required_usd - self.amount_funded_usd)

    @property
    def coverage_pct(self):
        if not self.amount_required_usd:
            return 0.0
        return round(self.amount_funded_usd / self.amount_required_usd * 100, 1)

    def to_dict(self):
        return {
            "id": self.id,
            "pillar_name": self.pillar_name,
            "amount_required_usd": self.amount_required_usd,
            "amount_funded_usd": self.amount_funded_usd,
            "gap_usd": self.gap_usd,
            "coverage_pct": self.coverage_pct,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "notes": self.notes,
        }

    def __repr__(self):
        return f"<FundingGap {self.pillar_name} {self.coverage_pct:.1f}% funded>"


class PartnerReport(db.Model):
    __tablename__ = "partner_reports"

    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("partners.id"), nullable=False)
    report_week = db.Column(db.Date, nullable=False)
    submitted = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime)
    report_type = db.Column(db.String(50), default="Weekly")
    notes = db.Column(db.Text)

    partner = db.relationship("Partner", backref=db.backref("reports", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "partner_name": self.partner.name if self.partner else None,
            "report_week": self.report_week.isoformat() if self.report_week else None,
            "submitted": self.submitted,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "report_type": self.report_type,
            "notes": self.notes,
        }

    def __repr__(self):
        return f"<PartnerReport partner={self.partner_id} week={self.report_week} submitted={self.submitted}>"


class GovernmentActivity(db.Model):
    __tablename__ = "government_activities"

    id                    = db.Column(db.Integer, primary_key=True)
    activity_number       = db.Column(db.String(10))
    technical_area        = db.Column(db.String(120))
    technical_area_number = db.Column(db.Integer)
    sub_section           = db.Column(db.String(120))
    activity_name         = db.Column(db.Text, nullable=False)
    total_cost_usd        = db.Column(db.Float, default=0)
    status                = db.Column(db.String(50), default="Planned")
    priority              = db.Column(db.String(20), default="Medium")
    notes                 = db.Column(db.Text)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at            = db.Column(db.DateTime, default=datetime.utcnow,
                                      onupdate=datetime.utcnow)

    @property
    def total_committed(self):
        return sum(c.amount_committed_usd or 0 for c in self.partner_contributions)

    @property
    def funding_gap(self):
        return max(0, (self.total_cost_usd or 0) - self.total_committed)

    @property
    def coverage_pct(self):
        if not self.total_cost_usd:
            return 0
        return min(100, self.total_committed / self.total_cost_usd * 100)

    def to_dict(self):
        return {
            "id": self.id,
            "activity_number": self.activity_number,
            "technical_area": self.technical_area,
            "technical_area_number": self.technical_area_number,
            "sub_section": self.sub_section,
            "activity_name": self.activity_name,
            "total_cost_usd": self.total_cost_usd or 0,
            "status": self.status,
            "priority": self.priority,
            "notes": self.notes,
            "total_committed": round(self.total_committed, 2),
            "funding_gap": round(self.funding_gap, 2),
            "coverage_pct": round(self.coverage_pct, 1),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<GovernmentActivity {self.activity_number} — {self.activity_name[:50]}>"


class PartnerContribution(db.Model):
    __tablename__ = "partner_contributions"

    id                     = db.Column(db.Integer, primary_key=True)
    government_activity_id = db.Column(db.Integer,
                               db.ForeignKey("government_activities.id",
                                             ondelete="CASCADE"),
                               nullable=False)
    partner_name           = db.Column(db.String(100), nullable=False)
    partner_id             = db.Column(db.Integer,
                               db.ForeignKey("partners.id"), nullable=True)
    amount_committed_usd   = db.Column(db.Float, default=0)
    amount_available_usd   = db.Column(db.Float, default=0)
    amount_to_mobilize_usd = db.Column(db.Float, default=0)
    amount_disbursed_usd   = db.Column(db.Float, default=0)
    modality               = db.Column(db.String(100), default="Direct Implementation")
    status                 = db.Column(db.String(50), default="Committed")
    notes                  = db.Column(db.Text)
    created_at             = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at             = db.Column(db.DateTime, default=datetime.utcnow,
                                       onupdate=datetime.utcnow)

    government_activity = db.relationship("GovernmentActivity",
                            backref=db.backref("partner_contributions",
                                               cascade="all, delete-orphan",
                                               passive_deletes=True))
    partner             = db.relationship("Partner",
                            backref="evd_contributions")

    @property
    def balance_usd(self):
        return max(0, (self.amount_committed_usd or 0) - (self.amount_disbursed_usd or 0))

    def to_dict(self):
        return {
            "id": self.id,
            "government_activity_id": self.government_activity_id,
            "partner_name": self.partner_name,
            "partner_id": self.partner_id,
            "activity_number": self.government_activity.activity_number
                               if self.government_activity else None,
            "activity_name": self.government_activity.activity_name
                             if self.government_activity else None,
            "technical_area": self.government_activity.technical_area
                              if self.government_activity else None,
            "technical_area_number": self.government_activity.technical_area_number
                                     if self.government_activity else None,
            "amount_committed_usd": self.amount_committed_usd or 0,
            "amount_available_usd": self.amount_available_usd or 0,
            "amount_to_mobilize_usd": self.amount_to_mobilize_usd or 0,
            "amount_disbursed_usd": self.amount_disbursed_usd or 0,
            "balance_usd": self.balance_usd,
            "modality": self.modality,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (f"<PartnerContribution partner={self.partner_name} "
                f"activity={self.government_activity_id} "
                f"${self.amount_committed_usd}>")
