"""
Populate the database with realistic EVD outbreak response data.
Run: python seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, datetime, timedelta
from app import create_app
from database import db
from models import (
    Partner, Resource, Activity, SituationReport, OutbreakPhase,
    FundingGap, PartnerReport,
)

OUTBREAK_START = date(2024, 3, 1)


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def clear_tables(app):
    with app.app_context():
        db.session.query(PartnerReport).delete()
        db.session.query(Activity).delete()
        db.session.query(Resource).delete()
        db.session.query(SituationReport).delete()
        db.session.query(OutbreakPhase).delete()
        db.session.query(FundingGap).delete()
        db.session.query(Partner).delete()
        db.session.commit()
        print("Cleared existing data.")


def seed_phases(app):
    phases = [
        OutbreakPhase(
            phase_name="Alert",
            start_date=OUTBREAK_START,
            end_date=OUTBREAK_START + timedelta(days=6),
            is_current=False,
            description="Initial alert; verification of outbreak",
        ),
        OutbreakPhase(
            phase_name="Mobilization",
            start_date=OUTBREAK_START + timedelta(days=7),
            end_date=OUTBREAK_START + timedelta(days=20),
            is_current=False,
            description="Partner mobilization and resource deployment",
        ),
        OutbreakPhase(
            phase_name="Response",
            start_date=OUTBREAK_START + timedelta(days=21),
            end_date=None,
            is_current=True,
            description="Full-scale response operations",
        ),
    ]
    with app.app_context():
        for p in phases:
            db.session.add(p)
        db.session.commit()
        print(f"Seeded {len(phases)} outbreak phases.")


def seed_partners(app):
    partners_data = [
        # 5.1 — WHO entry with required contact details
        dict(name="WHO", partner_type="Government", country="Switzerland",
             contact_person="Dr. Brian Chirombo", contact_email="chirombo@who.int", status="Active"),
        dict(name="USAID/OFDA", partner_type="Government", country="USA",
             contact_person="Dr. Maria Johnson", contact_email="m.johnson@usaid.gov", status="Active"),
        dict(name="EU/ECHO", partner_type="Government", country="Belgium",
             contact_person="Pierre Dupont", contact_email="p.dupont@echo.eu", status="Active"),
        dict(name="MSF (Médecins Sans Frontières)", partner_type="NGO", country="Switzerland",
             contact_person="Dr. Amina Diallo", contact_email="a.diallo@msf.org", status="Active"),
        dict(name="CDC (US Centers for Disease Control)", partner_type="Government", country="USA",
             contact_person="Dr. Robert Chen", contact_email="r.chen@cdc.gov", status="Active"),
        dict(name="UNICEF", partner_type="NGO", country="USA",
             contact_person="Fatou Ndiaye", contact_email="f.ndiaye@unicef.org", status="Active"),
        dict(name="Gavi — The Vaccine Alliance", partner_type="Private", country="Switzerland",
             contact_person="Dr. Helen Brooks", contact_email="h.brooks@gavi.org", status="Active"),
        dict(name="World Bank / IDA", partner_type="Private", country="USA",
             contact_person="James Kariuki", contact_email="j.kariuki@worldbank.org", status="Negotiating"),
        dict(name="DRC Ministry of Health", partner_type="Government", country="DRC",
             contact_person="Prof. Jean-Baptiste Mwamba", contact_email="mwamba@sante.gouv.cd", status="Active"),
        dict(name="ICRC / Red Cross", partner_type="NGO", country="Switzerland",
             contact_person="Sophie Leclerc", contact_email="s.leclerc@icrc.org", status="Active"),
        dict(name="Africa CDC", partner_type="Government", country="Ethiopia",
             contact_person="Dr. Ngozi Okonkwo", contact_email="n.okonkwo@africacdc.org", status="Active"),
    ]
    with app.app_context():
        partners = []
        for d in partners_data:
            p = Partner(**d)
            db.session.add(p)
            partners.append(p)
        db.session.commit()
        print(f"Seeded {len(partners)} partners.")
        return {p.name: p.id for p in partners}


def seed_resources(app, partner_ids):
    pid = partner_ids
    resources_data = [
        dict(partner_id=pid["USAID/OFDA"], resource_type="Funding",
             description="Emergency Supplemental Ebola Response Fund",
             amount=12_500_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=5),
             deployment_date=OUTBREAK_START + timedelta(days=14),
             status="Deployed", reporting_frequency="Monthly",
             next_report_due=date(2024, 5, 1)),
        dict(partner_id=pid["EU/ECHO"], resource_type="Funding",
             description="Humanitarian Aid for EVD Response DRC",
             amount=8_000_000, currency="EUR",
             commitment_date=OUTBREAK_START + timedelta(days=8),
             deployment_date=OUTBREAK_START + timedelta(days=20),
             status="Deployed", reporting_frequency="Biweekly",
             next_report_due=date(2024, 4, 20)),
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], resource_type="Personnel",
             description="50 medical staff — ETU management and clinical care",
             amount=0, currency="In-kind",
             commitment_date=OUTBREAK_START + timedelta(days=3),
             deployment_date=OUTBREAK_START + timedelta(days=7),
             status="Deployed", reporting_frequency="Weekly",
             next_report_due=date(2024, 4, 15)),
        dict(partner_id=pid["CDC (US Centers for Disease Control)"], resource_type="Technical",
             description="Lab surge capacity — mobile BSL-3 laboratory",
             amount=2_200_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=4),
             deployment_date=OUTBREAK_START + timedelta(days=10),
             status="Deployed", reporting_frequency="Weekly",
             next_report_due=date(2024, 4, 15)),
        dict(partner_id=pid["UNICEF"], resource_type="PPE",
             description="50,000 PPE kits (gloves, gowns, masks, face shields)",
             amount=1_500_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=6),
             deployment_date=OUTBREAK_START + timedelta(days=15),
             status="Deployed", reporting_frequency="Monthly",
             next_report_due=date(2024, 5, 1)),
        dict(partner_id=pid["UNICEF"], resource_type="Logistics",
             description="Cold chain logistics for vaccine transport",
             amount=750_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=10),
             status="Committed", reporting_frequency="Monthly",
             next_report_due=date(2024, 5, 1)),
        dict(partner_id=pid["Gavi — The Vaccine Alliance"], resource_type="Vaccines",
             description="200,000 rVSV-ZEBOV (Ervebo) doses for ring vaccination",
             amount=4_800_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=7),
             deployment_date=OUTBREAK_START + timedelta(days=18),
             status="Deployed", reporting_frequency="Biweekly",
             next_report_due=date(2024, 4, 20)),
        dict(partner_id=pid["World Bank / IDA"], resource_type="Funding",
             description="Emergency Health System Support — DRC EVD",
             amount=15_000_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=15),
             status="Committed", reporting_frequency="Monthly",
             next_report_due=date(2024, 5, 15)),
        dict(partner_id=pid["DRC Ministry of Health"], resource_type="Personnel",
             description="500 community health workers mobilized",
             amount=0, currency="In-kind",
             commitment_date=OUTBREAK_START + timedelta(days=2),
             deployment_date=OUTBREAK_START + timedelta(days=5),
             status="Deployed", reporting_frequency="Weekly",
             next_report_due=date(2024, 4, 15)),
        dict(partner_id=pid["ICRC / Red Cross"], resource_type="Logistics",
             description="Safe and dignified burials team — 3 teams of 8",
             amount=600_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=5),
             deployment_date=OUTBREAK_START + timedelta(days=9),
             status="Deployed", reporting_frequency="Weekly",
             next_report_due=date(2024, 4, 15)),
        dict(partner_id=pid["Africa CDC"], resource_type="Technical",
             description="Epidemiology surge team — 12 field epidemiologists",
             amount=800_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=6),
             deployment_date=OUTBREAK_START + timedelta(days=12),
             status="Deployed", reporting_frequency="Biweekly",
             next_report_due=date(2024, 4, 20)),
        dict(partner_id=pid["USAID/OFDA"], resource_type="Funding",
             description="Supplemental funding tranche 2",
             amount=5_000_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=30),
             status="Pipeline", reporting_frequency="Monthly",
             next_report_due=date(2024, 6, 1)),
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], resource_type="Logistics",
             description="2 mobile ETU units (40 beds each)",
             amount=0, currency="In-kind",
             commitment_date=OUTBREAK_START + timedelta(days=4),
             deployment_date=OUTBREAK_START + timedelta(days=14),
             status="Deployed", reporting_frequency="Weekly",
             next_report_due=date(2024, 4, 15)),
        dict(partner_id=pid["CDC (US Centers for Disease Control)"], resource_type="Technical",
             description="Contact tracing digital platform (Go.Data) deployment",
             amount=350_000, currency="USD",
             commitment_date=OUTBREAK_START + timedelta(days=8),
             status="Under Review", reporting_frequency="Monthly",
             next_report_due=date(2024, 5, 1)),
        dict(partner_id=pid["EU/ECHO"], resource_type="PPE",
             description="20,000 additional PPE sets via stockpile",
             amount=600_000, currency="EUR",
             commitment_date=OUTBREAK_START + timedelta(days=12),
             status="Pipeline", reporting_frequency="Monthly",
             next_report_due=date(2024, 5, 15)),
    ]
    with app.app_context():
        for d in resources_data:
            r = Resource(**d)
            db.session.add(r)
        db.session.commit()
        print(f"Seeded {len(resources_data)} resources.")


def seed_activities(app, partner_ids):
    pid = partner_ids
    activities_data = [
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], activity_type="ETU Operations",
             location="Mbandaka", district="Equateur", start_date=OUTBREAK_START + timedelta(days=7),
             status="Ongoing", description="40-bed ETU — Mbandaka General Hospital",
             beneficiaries_reached=312),
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], activity_type="ETU Operations",
             location="Bikoro", district="Equateur", start_date=OUTBREAK_START + timedelta(days=10),
             status="Ongoing", description="40-bed mobile ETU — Bikoro Health Zone",
             beneficiaries_reached=178),
        dict(partner_id=pid["DRC Ministry of Health"], activity_type="Contact Tracing",
             location="Equateur Province", district="Equateur", start_date=OUTBREAK_START + timedelta(days=3),
             status="Ongoing", description="Province-wide contact tracing — 300+ contacts listed",
             beneficiaries_reached=1240),
        dict(partner_id=pid["Africa CDC"], activity_type="Contact Tracing",
             location="Nord-Ubangi", district="Nord-Ubangi", start_date=OUTBREAK_START + timedelta(days=12),
             status="Ongoing", description="Digital contact tracing with Go.Data platform",
             beneficiaries_reached=680),
        dict(partner_id=pid["Gavi — The Vaccine Alliance"], activity_type="Vaccination",
             location="Mbandaka", district="Equateur", start_date=OUTBREAK_START + timedelta(days=18),
             status="Ongoing", description="Ring vaccination of contacts and HCW — rVSV-ZEBOV",
             beneficiaries_reached=4200),
        dict(partner_id=pid["DRC Ministry of Health"], activity_type="Vaccination",
             location="Bikoro", district="Equateur", start_date=OUTBREAK_START + timedelta(days=20),
             status="Ongoing", description="Expanded vaccination — second ring contacts",
             beneficiaries_reached=2100),
        dict(partner_id=pid["CDC (US Centers for Disease Control)"], activity_type="Lab",
             location="Mbandaka", district="Equateur", start_date=OUTBREAK_START + timedelta(days=10),
             status="Ongoing", description="Mobile BSL-3 lab — RT-PCR testing, 200+ tests/day",
             beneficiaries_reached=0),
        dict(partner_id=pid["Africa CDC"], activity_type="Lab",
             location="Equateur Province", district="Equateur", start_date=OUTBREAK_START + timedelta(days=14),
             status="Ongoing", description="Specimen referral network for 3 health zones",
             beneficiaries_reached=0),
        dict(partner_id=pid["UNICEF"], activity_type="Community Engagement",
             location="Equateur Province", district="Equateur", start_date=OUTBREAK_START + timedelta(days=5),
             status="Ongoing", description="Community sensitization — radio, community leaders",
             beneficiaries_reached=85000),
        dict(partner_id=pid["ICRC / Red Cross"], activity_type="Community Engagement",
             location="Mbandaka", district="Equateur", start_date=OUTBREAK_START + timedelta(days=6),
             status="Ongoing", description="Community mobilization and psychosocial support",
             beneficiaries_reached=12000),
        dict(partner_id=pid["ICRC / Red Cross"], activity_type="Logistics",
             location="Equateur Province", district="Equateur", start_date=OUTBREAK_START + timedelta(days=9),
             status="Ongoing", description="Safe and dignified burial operations — 3 SDB teams",
             beneficiaries_reached=0),
        dict(partner_id=pid["USAID/OFDA"], activity_type="Logistics",
             location="Mbandaka", district="Equateur", start_date=OUTBREAK_START + timedelta(days=8),
             status="Ongoing", description="Emergency supply chain management — PPE distribution",
             beneficiaries_reached=0),
        dict(partner_id=pid["DRC Ministry of Health"], activity_type="ETU Operations",
             location="Ingende", district="Equateur", start_date=OUTBREAK_START + timedelta(days=15),
             status="Planned", description="New 20-bed ETU planned for Ingende Health Zone",
             beneficiaries_reached=0),
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], activity_type="Community Engagement",
             location="Bikoro", district="Equateur", start_date=OUTBREAK_START + timedelta(days=8),
             status="Ongoing", description="Community health promoters — household visits",
             beneficiaries_reached=9500),
        dict(partner_id=pid["UNICEF"], activity_type="Logistics",
             location="Nord-Ubangi", district="Nord-Ubangi", start_date=OUTBREAK_START + timedelta(days=20),
             status="Planned", description="WASH kits distribution to affected households",
             beneficiaries_reached=0),
        dict(partner_id=pid["EU/ECHO"], activity_type="Community Engagement",
             location="Sud-Ubangi", district="Sud-Ubangi", start_date=OUTBREAK_START + timedelta(days=18),
             status="Planned", description="Rumour management and community feedback system",
             beneficiaries_reached=0),
        dict(partner_id=pid["CDC (US Centers for Disease Control)"], activity_type="Contact Tracing",
             location="Bikoro", district="Equateur", start_date=OUTBREAK_START + timedelta(days=9),
             status="Ongoing", description="Epidemiological investigation and line listing",
             beneficiaries_reached=520),
        dict(partner_id=pid["Gavi — The Vaccine Alliance"], activity_type="Vaccination",
             location="Nord-Ubangi", district="Nord-Ubangi", start_date=OUTBREAK_START + timedelta(days=25),
             status="Planned", description="Pre-emptive vaccination in bordering health zones",
             beneficiaries_reached=0),
        dict(partner_id=pid["Africa CDC"], activity_type="ETU Operations",
             location="Bolomba", district="Equateur", start_date=OUTBREAK_START + timedelta(days=22),
             status="Planned", description="Support assessment for ETU needs — Bolomba",
             beneficiaries_reached=0),
        dict(partner_id=pid["USAID/OFDA"], activity_type="Community Engagement",
             location="Equateur Province", district="Equateur", start_date=OUTBREAK_START + timedelta(days=12),
             status="Ongoing", description="Risk communication — mass media campaign",
             beneficiaries_reached=150000),
    ]
    with app.app_context():
        for d in activities_data:
            a = Activity(**d)
            db.session.add(a)
        db.session.commit()
        print(f"Seeded {len(activities_data)} activities.")


def seed_sitreps(app):
    sitreps_data = [
        dict(report_date=OUTBREAK_START + timedelta(days=1), outbreak_day=1,
             confirmed_cases=3, deaths=1, healthcare_workers_affected=0,
             etus_operational=0, total_funding_mobilized=0, funding_gap=50_000_000,
             notes="Outbreak declared. Three confirmed EVD cases in Bikoro health zone.",
             created_by="WHO EOC"),
        dict(report_date=OUTBREAK_START + timedelta(days=7), outbreak_day=7,
             confirmed_cases=18, deaths=7, healthcare_workers_affected=2,
             etus_operational=1, total_funding_mobilized=5_000_000, funding_gap=45_000_000,
             notes="Outbreak spreading. One ETU operational. USAID and EU initial pledges received.",
             created_by="WHO EOC"),
        dict(report_date=OUTBREAK_START + timedelta(days=14), outbreak_day=14,
             confirmed_cases=42, deaths=16, healthcare_workers_affected=5,
             etus_operational=2, total_funding_mobilized=18_500_000, funding_gap=31_500_000,
             notes="Acceleration in case counts. Second ETU operational. Vaccination campaign launched.",
             created_by="WHO EOC"),
        dict(report_date=OUTBREAK_START + timedelta(days=21), outbreak_day=21,
             confirmed_cases=67, deaths=23, healthcare_workers_affected=8,
             etus_operational=3, total_funding_mobilized=32_000_000, funding_gap=18_000_000,
             notes="Response scaling. Ring vaccination showing early efficacy. Contact tracing coverage 78%.",
             created_by="WHO EOC"),
        dict(report_date=OUTBREAK_START + timedelta(days=28), outbreak_day=28,
             confirmed_cases=89, deaths=29, healthcare_workers_affected=10,
             etus_operational=3, total_funding_mobilized=41_800_000, funding_gap=8_200_000,
             notes="Epidemic curve plateauing. Strong partner engagement. 14 days to end if trend continues.",
             created_by="WHO EOC"),
    ]
    with app.app_context():
        for d in sitreps_data:
            s = SituationReport(**d)
            db.session.add(s)
        db.session.commit()
        print(f"Seeded {len(sitreps_data)} situation reports.")


def seed_funding_gaps(app):
    pillars = [
        dict(pillar_name="Coordination",    amount_required_usd=2_000_000,  amount_funded_usd=1_400_000,
             notes="Includes EOC operations, coordination meetings, information management"),
        dict(pillar_name="Surveillance",    amount_required_usd=5_000_000,  amount_funded_usd=3_200_000,
             notes="Epidemiology, contact tracing, Go.Data platform"),
        dict(pillar_name="Laboratory",      amount_required_usd=8_000_000,  amount_funded_usd=6_100_000,
             notes="Mobile labs, specimen referral, reagents, BSL-3 capacity"),
        dict(pillar_name="Case Management", amount_required_usd=15_000_000, amount_funded_usd=9_800_000,
             notes="ETU operations, clinical care, IPC, patient transfer"),
        dict(pillar_name="RCCE",            amount_required_usd=3_000_000,  amount_funded_usd=1_100_000,
             notes="Risk communication, community engagement, rumour management"),
        dict(pillar_name="Logistics",       amount_required_usd=10_000_000, amount_funded_usd=7_500_000,
             notes="Supply chain, cold chain, PPE, safe burials, WASH"),
        dict(pillar_name="Research",        amount_required_usd=4_000_000,  amount_funded_usd=2_900_000,
             notes="Clinical trials, vaccine studies, operational research"),
    ]
    with app.app_context():
        for d in pillars:
            fg = FundingGap(**d)
            db.session.add(fg)
        db.session.commit()
        print(f"Seeded {len(pillars)} funding gap pillars.")


def seed_partner_reports(app, partner_ids):
    pid = partner_ids
    today = date.today()
    weeks = [_monday_of(today) - timedelta(weeks=i) for i in range(3, -1, -1)]

    # Mix of submitted/not-submitted across 4 weeks for active partners
    active_partners = [
        "WHO", "USAID/OFDA", "EU/ECHO", "MSF (Médecins Sans Frontières)",
        "CDC (US Centers for Disease Control)", "UNICEF", "Gavi — The Vaccine Alliance",
        "DRC Ministry of Health", "ICRC / Red Cross", "Africa CDC",
    ]
    # Compliance pattern: [week-3, week-2, week-1, this_week]
    # True = submitted, False = overdue
    compliance_map = {
        "WHO":                              [True,  True,  True,  True],
        "USAID/OFDA":                       [True,  True,  True,  True],
        "EU/ECHO":                          [True,  True,  True,  False],
        "MSF (Médecins Sans Frontières)":   [True,  True,  False, True],
        "CDC (US Centers for Disease Control)": [True,  True,  True,  True],
        "UNICEF":                           [True,  False, True,  True],
        "Gavi — The Vaccine Alliance":      [True,  True,  True,  False],
        "DRC Ministry of Health":           [False, True,  True,  True],
        "ICRC / Red Cross":                 [True,  True,  False, False],
        "Africa CDC":                       [True,  True,  True,  True],
    }

    records = []
    for pname in active_partners:
        if pname not in pid:
            continue
        for week_idx, week in enumerate(weeks):
            submitted = compliance_map.get(pname, [False] * 4)[week_idx]
            records.append(PartnerReport(
                partner_id=pid[pname],
                report_week=week,
                submitted=submitted,
                submitted_at=datetime(week.year, week.month, week.day, 9, 0) if submitted else None,
                report_type="Weekly",
                notes=f"Auto-generated seed record" if submitted else None,
            ))

    with app.app_context():
        for r in records:
            db.session.add(r)
        db.session.commit()
        print(f"Seeded {len(records)} partner report records.")


if __name__ == "__main__":
    app = create_app()
    print("Starting EVD Response data seeding...")
    clear_tables(app)
    seed_phases(app)
    partner_ids = seed_partners(app)
    seed_resources(app, partner_ids)
    seed_activities(app, partner_ids)
    seed_sitreps(app)
    seed_funding_gaps(app)
    seed_partner_reports(app, partner_ids)
    print("\nSeed complete! Run `python app.py` to start the API.")
