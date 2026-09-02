"""
Populate the database with realistic EVD outbreak response data.
Run: python seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, timedelta
from app import create_app
from database import db
from models import Partner, Resource, Activity, SituationReport, OutbreakPhase, GovernmentActivity, PartnerContribution

OUTBREAK_START = date(2024, 3, 1)


def clear_tables(app):
    with app.app_context():
        db.session.query(PartnerContribution).delete()
        db.session.query(GovernmentActivity).delete()
        db.session.query(Activity).delete()
        db.session.query(Resource).delete()
        db.session.query(SituationReport).delete()
        db.session.query(OutbreakPhase).delete()
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
    locations = [
        "Equateur Province", "Nord-Ubangi", "Sud-Ubangi",
        "Mbandaka", "Bikoro", "Ingende", "Bolomba",
    ]
    activities_data = [
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], activity_type="ETU Operations",
             location="Mbandaka", start_date=OUTBREAK_START + timedelta(days=7),
             status="Ongoing", description="40-bed ETU — Mbandaka General Hospital"),
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], activity_type="ETU Operations",
             location="Bikoro", start_date=OUTBREAK_START + timedelta(days=10),
             status="Ongoing", description="40-bed mobile ETU — Bikoro Health Zone"),
        dict(partner_id=pid["DRC Ministry of Health"], activity_type="Contact Tracing",
             location="Equateur Province", start_date=OUTBREAK_START + timedelta(days=3),
             status="Ongoing", description="Province-wide contact tracing — 300+ contacts listed"),
        dict(partner_id=pid["Africa CDC"], activity_type="Contact Tracing",
             location="Nord-Ubangi", start_date=OUTBREAK_START + timedelta(days=12),
             status="Ongoing", description="Digital contact tracing with Go.Data platform"),
        dict(partner_id=pid["Gavi — The Vaccine Alliance"], activity_type="Vaccination",
             location="Mbandaka", start_date=OUTBREAK_START + timedelta(days=18),
             status="Ongoing", description="Ring vaccination of contacts and HCW — rVSV-ZEBOV"),
        dict(partner_id=pid["DRC Ministry of Health"], activity_type="Vaccination",
             location="Bikoro", start_date=OUTBREAK_START + timedelta(days=20),
             status="Ongoing", description="Expanded vaccination — second ring contacts"),
        dict(partner_id=pid["CDC (US Centers for Disease Control)"], activity_type="Lab",
             location="Mbandaka", start_date=OUTBREAK_START + timedelta(days=10),
             status="Ongoing", description="Mobile BSL-3 lab — RT-PCR testing, 200+ tests/day"),
        dict(partner_id=pid["Africa CDC"], activity_type="Lab",
             location="Equateur Province", start_date=OUTBREAK_START + timedelta(days=14),
             status="Ongoing", description="Specimen referral network for 3 health zones"),
        dict(partner_id=pid["UNICEF"], activity_type="Community Engagement",
             location="Equateur Province", start_date=OUTBREAK_START + timedelta(days=5),
             status="Ongoing", description="Community sensitization — radio, community leaders"),
        dict(partner_id=pid["ICRC / Red Cross"], activity_type="Community Engagement",
             location="Mbandaka", start_date=OUTBREAK_START + timedelta(days=6),
             status="Ongoing", description="Community mobilization and psychosocial support"),
        dict(partner_id=pid["ICRC / Red Cross"], activity_type="Logistics",
             location="Equateur Province", start_date=OUTBREAK_START + timedelta(days=9),
             status="Ongoing", description="Safe and dignified burial operations — 3 SDB teams"),
        dict(partner_id=pid["USAID/OFDA"], activity_type="Logistics",
             location="Mbandaka", start_date=OUTBREAK_START + timedelta(days=8),
             status="Ongoing", description="Emergency supply chain management — PPE distribution"),
        dict(partner_id=pid["DRC Ministry of Health"], activity_type="ETU Operations",
             location="Ingende", start_date=OUTBREAK_START + timedelta(days=15),
             status="Planned", description="New 20-bed ETU planned for Ingende Health Zone"),
        dict(partner_id=pid["MSF (Médecins Sans Frontières)"], activity_type="Community Engagement",
             location="Bikoro", start_date=OUTBREAK_START + timedelta(days=8),
             status="Ongoing", description="Community health promoters — household visits"),
        dict(partner_id=pid["UNICEF"], activity_type="Logistics",
             location="Nord-Ubangi", start_date=OUTBREAK_START + timedelta(days=20),
             status="Planned", description="WASH kits distribution to affected households"),
        dict(partner_id=pid["EU/ECHO"], activity_type="Community Engagement",
             location="Sud-Ubangi", start_date=OUTBREAK_START + timedelta(days=18),
             status="Planned", description="Rumour management and community feedback system"),
        dict(partner_id=pid["CDC (US Centers for Disease Control)"], activity_type="Contact Tracing",
             location="Bikoro", start_date=OUTBREAK_START + timedelta(days=9),
             status="Ongoing", description="Epidemiological investigation and line listing"),
        dict(partner_id=pid["Gavi — The Vaccine Alliance"], activity_type="Vaccination",
             location="Nord-Ubangi", start_date=OUTBREAK_START + timedelta(days=25),
             status="Planned", description="Pre-emptive vaccination in bordering health zones"),
        dict(partner_id=pid["Africa CDC"], activity_type="ETU Operations",
             location="Bolomba", start_date=OUTBREAK_START + timedelta(days=22),
             status="Planned", description="Support assessment for ETU needs — Bolomba"),
        dict(partner_id=pid["USAID/OFDA"], activity_type="Community Engagement",
             location="Equateur Province", start_date=OUTBREAK_START + timedelta(days=12),
             status="Ongoing", description="Risk communication — mass media campaign"),
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
             notes="Outbreak declared. Three confirmed EVD cases in Bikoro health zone. Samples sent to INRB.",
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
             notes="Epidemiological curve plateauing. Strong partner engagement. 14 days to end of outbreak if trend continues.",
             created_by="WHO EOC"),
    ]
    with app.app_context():
        for d in sitreps_data:
            s = SituationReport(**d)
            db.session.add(s)
        db.session.commit()
        print(f"Seeded {len(sitreps_data)} situation reports.")


def seed_mobilization_partners(app):
    """Ensure the Excel-sourced partners exist; return name→id map."""
    mob_partners = [
        dict(name="IOM",               partner_type="NGO",        country="Switzerland"),
        dict(name="WHO",               partner_type="Government",  country="Switzerland"),
        dict(name="UNICEF",            partner_type="NGO",        country="USA"),
        dict(name="US CDC",            partner_type="Government",  country="USA"),
        dict(name="US State Department", partner_type="Government", country="USA"),
        dict(name="CHAI",              partner_type="NGO",        country="USA"),
        dict(name="Enabel/Tribe Hub",  partner_type="NGO",        country="Belgium"),
        dict(name="Enabel/Lomesu",     partner_type="NGO",        country="Belgium"),
        dict(name="FAO",               partner_type="Government",  country="Italy"),
    ]
    ids = {}
    with app.app_context():
        for d in mob_partners:
            p = Partner.query.filter_by(name=d["name"]).first()
            if not p:
                p = Partner(
                    name=d["name"],
                    partner_type=d["partner_type"],
                    country=d["country"],
                    status="Active",
                )
                db.session.add(p)
                db.session.flush()
            ids[d["name"]] = p.id
        db.session.commit()
        print(f"Ensured {len(ids)} mobilization partners.")
    return ids


def seed_government_activities(app):
    """Seed all 7 preparedness pillars from the Excel 'Partner Support Updated' sheet."""

    PILLARS = {
        1: "Leadership and Coordination",
        2: "Epidemiological Surveillance",
        3: "Laboratory and Diagnostics",
        4: "Case Management, IPC/WASH and SDB",
        5: "Risk Communication and Community Engagement",
        6: "Operational Support and Logistics",
        7: "Research and Strategic Information",
    }

    activities_data = [
        # ── PILLAR 1 — Leadership and Coordination ──────────────────────────
        dict(pillar_number=1, activity_number="1.0",
             sub_section="A. Leadership and Coordination",
             activity_name="Activate the National Command Post, IMS and functional TWGs",
             total_cost_usd=0, priority="High"),
        dict(pillar_number=1, activity_number="2.0",
             sub_section="A. Leadership and Coordination",
             activity_name="Complete BDBV EVD readiness checklist",
             total_cost_usd=0, priority="High"),
        dict(pillar_number=1, activity_number="3.0",
             sub_section="A. Leadership and Coordination",
             activity_name="Develop and disseminate the National BDBV EVD Preparedness and Response Plan including a 72-hour response plan",
             total_cost_usd=0, priority="High"),
        dict(pillar_number=1, activity_number="4.0",
             sub_section="A. Leadership and Coordination",
             activity_name="Activate national and district Rapid Response Teams",
             total_cost_usd=0, priority="High"),
        dict(pillar_number=1, activity_number="5.0",
             sub_section="A. Leadership and Coordination",
             activity_name="Activate multi-sectoral and multi-partner coordination mechanisms",
             total_cost_usd=0, priority="High"),
        dict(pillar_number=1, activity_number="6.0",
             sub_section="B. Operations Support",
             activity_name="Support the National Command Post operations",
             total_cost_usd=748746, priority="High"),
        dict(pillar_number=1, activity_number="7.0",
             sub_section="B. Operations Support",
             activity_name="Support District Command Post operations in high-risk districts",
             total_cost_usd=184679, priority="High"),
        dict(pillar_number=1, activity_number="8.0",
             sub_section="B. Operations Support",
             activity_name="Hire surge staff and support incentives for staff at POEs",
             total_cost_usd=1465554, priority="High"),
        dict(pillar_number=1, activity_number="9.0",
             sub_section="C. Assessment and Supervision",
             activity_name="Conduct initial BDBV EVD capacity assessment",
             total_cost_usd=10260, priority="Medium"),
        dict(pillar_number=1, activity_number="10.0",
             sub_section="C. Assessment and Supervision",
             activity_name="Facilitate integrated regular support supervision",
             total_cost_usd=39694, priority="Medium"),
        dict(pillar_number=1, activity_number="11.0",
             sub_section="D. Cross-border and Regional",
             activity_name="Support cross-border coordination activities with DRC",
             total_cost_usd=4432, priority="Medium"),
        dict(pillar_number=1, activity_number="12.0",
             sub_section="C. Assessment and Supervision",
             activity_name="Conduct BDBV EVD field simulation exercise",
             total_cost_usd=27360, priority="Medium"),
        dict(pillar_number=1, activity_number="13.0",
             sub_section="C. Assessment and Supervision",
             activity_name="Monitor the implementation of the National BDBV EVD Plan",
             total_cost_usd=0, priority="Medium"),
        dict(pillar_number=1, activity_number="14.0",
             sub_section="E. Resource Mobilization",
             activity_name="Meeting to mobilize resources",
             total_cost_usd=2052, priority="Medium"),
        dict(pillar_number=1, activity_number="15.0",
             sub_section="A. Leadership and Coordination",
             activity_name="Print and distribute BDBV EVD technical guidelines",
             total_cost_usd=34884, priority="Medium"),

        # ── PILLAR 2 — Epidemiological Surveillance ──────────────────────────
        dict(pillar_number=2, activity_number="16.0",
             sub_section="A. Surveillance Systems",
             activity_name="Activate and strengthen disease surveillance systems in high-risk districts",
             total_cost_usd=120000, priority="High"),
        dict(pillar_number=2, activity_number="17.0",
             sub_section="A. Surveillance Systems",
             activity_name="Train and deploy field epidemiologists to high-risk districts",
             total_cost_usd=85000, priority="High"),
        dict(pillar_number=2, activity_number="18.0",
             sub_section="B. Community-based Surveillance",
             activity_name="Establish and strengthen community-based surveillance (CBS) networks",
             total_cost_usd=45000, priority="High"),
        dict(pillar_number=2, activity_number="19.0",
             sub_section="C. Case Investigation",
             activity_name="Conduct EVD case investigation and contact listing",
             total_cost_usd=0, priority="High"),
        dict(pillar_number=2, activity_number="20.0",
             sub_section="D. Contact Tracing",
             activity_name="Support contact tracing and follow-up in high-risk districts",
             total_cost_usd=180000, priority="High"),
        dict(pillar_number=2, activity_number="21.0",
             sub_section="E. Border Surveillance",
             activity_name="Strengthen Points of Entry (POE) surveillance and screening",
             total_cost_usd=90000, priority="High"),
        dict(pillar_number=2, activity_number="22.0",
             sub_section="F. Data Management",
             activity_name="Establish and maintain EVD line listing and database",
             total_cost_usd=15000, priority="Medium"),
        dict(pillar_number=2, activity_number="23.0",
             sub_section="F. Data Management",
             activity_name="Conduct epidemiological data analysis and weekly reporting",
             total_cost_usd=0, priority="Medium"),
        dict(pillar_number=2, activity_number="24.0",
             sub_section="D. Contact Tracing",
             activity_name="Deploy Go.Data digital contact tracing platform",
             total_cost_usd=35000, priority="Medium"),
        dict(pillar_number=2, activity_number="25.0",
             sub_section="A. Surveillance Systems",
             activity_name="Conduct joint EVD surveillance review and coordination meetings",
             total_cost_usd=12000, priority="Low"),

        # ── PILLAR 3 — Laboratory and Diagnostics ────────────────────────────
        dict(pillar_number=3, activity_number="26.0",
             sub_section="A. Reference Laboratory",
             activity_name="Designate and equip BDBV EVD national reference laboratory",
             total_cost_usd=245000, priority="High"),
        dict(pillar_number=3, activity_number="27.0",
             sub_section="B. Reagents and Consumables",
             activity_name="Procure laboratory reagents and consumables for RT-PCR EVD testing",
             total_cost_usd=185000, priority="High"),
        dict(pillar_number=3, activity_number="28.0",
             sub_section="C. Specimen Transport",
             activity_name="Establish specimen referral and safe transport network",
             total_cost_usd=65000, priority="High"),
        dict(pillar_number=3, activity_number="29.0",
             sub_section="D. Capacity Building",
             activity_name="Train laboratory personnel on EVD diagnostics and biosafety (BSL-3)",
             total_cost_usd=38000, priority="Medium"),
        dict(pillar_number=3, activity_number="30.0",
             sub_section="E. Rapid Diagnostics",
             activity_name="Procure and deploy rapid diagnostic tests (RDTs) for field testing",
             total_cost_usd=120000, priority="High"),
        dict(pillar_number=3, activity_number="31.0",
             sub_section="A. Reference Laboratory",
             activity_name="Conduct external quality assessment and proficiency testing",
             total_cost_usd=22000, priority="Medium"),
        dict(pillar_number=3, activity_number="32.0",
             sub_section="A. Reference Laboratory",
             activity_name="Establish mobile laboratory capacity for remote district deployment",
             total_cost_usd=0, priority="Medium"),
        dict(pillar_number=3, activity_number="33.0",
             sub_section="F. Result Reporting",
             activity_name="Improve laboratory result reporting and turnaround time",
             total_cost_usd=0, priority="Medium"),

        # ── PILLAR 4 — Case Management, IPC/WASH and SDB ─────────────────────
        dict(pillar_number=4, activity_number="34.0",
             sub_section="A. ETU Operations",
             activity_name="Designate, prepare and operationalise Ebola Treatment Units (ETUs)",
             total_cost_usd=425000, priority="High"),
        dict(pillar_number=4, activity_number="35.0",
             sub_section="A. ETU Operations",
             activity_name="Procure clinical supplies, therapeutics and experimental treatment (mAb114)",
             total_cost_usd=380000, priority="High"),
        dict(pillar_number=4, activity_number="36.0",
             sub_section="A. ETU Operations",
             activity_name="Train clinical staff on EVD case management protocols and clinical trials",
             total_cost_usd=55000, priority="High"),
        dict(pillar_number=4, activity_number="37.0",
             sub_section="B. IPC",
             activity_name="Establish infection prevention and control (IPC) systems in health facilities",
             total_cost_usd=95000, priority="High"),
        dict(pillar_number=4, activity_number="38.0",
             sub_section="B. IPC",
             activity_name="Procure and distribute PPE to all health facilities and community teams",
             total_cost_usd=210000, priority="High"),
        dict(pillar_number=4, activity_number="39.0",
             sub_section="B. IPC",
             activity_name="Train healthcare workers on IPC standard precautions and EVD protocols",
             total_cost_usd=48000, priority="High"),
        dict(pillar_number=4, activity_number="40.0",
             sub_section="C. Safe and Dignified Burials",
             activity_name="Establish and deploy safe and dignified burial (SDB) teams",
             total_cost_usd=85000, priority="High"),
        dict(pillar_number=4, activity_number="41.0",
             sub_section="C. Safe and Dignified Burials",
             activity_name="Procure SDB kits, body bags and burial supplies",
             total_cost_usd=45000, priority="High"),
        dict(pillar_number=4, activity_number="42.0",
             sub_section="D. WASH",
             activity_name="Improve WASH infrastructure in affected health facilities",
             total_cost_usd=180000, priority="High"),
        dict(pillar_number=4, activity_number="43.0",
             sub_section="A. ETU Operations",
             activity_name="Establish patient referral pathways and ambulance network",
             total_cost_usd=0, priority="Medium"),
        dict(pillar_number=4, activity_number="44.0",
             sub_section="E. Survivor Care",
             activity_name="Set up EVD survivor care programme and psychosocial support",
             total_cost_usd=62000, priority="Medium"),
        dict(pillar_number=4, activity_number="45.0",
             sub_section="B. IPC",
             activity_name="Monitor and supervise adherence to IPC protocols in health facilities",
             total_cost_usd=0, priority="Medium"),

        # ── PILLAR 5 — Risk Communication and Community Engagement ────────────
        dict(pillar_number=5, activity_number="46.0",
             sub_section="A. Key Messages",
             activity_name="Develop, pre-test and disseminate EVD key messages and communication materials",
             total_cost_usd=18000, priority="High"),
        dict(pillar_number=5, activity_number="47.0",
             sub_section="B. Community Sensitization",
             activity_name="Conduct community sensitization campaigns in high-risk districts",
             total_cost_usd=95000, priority="High"),
        dict(pillar_number=5, activity_number="48.0",
             sub_section="C. Community Leaders",
             activity_name="Engage community, religious and traditional leaders as EVD champions",
             total_cost_usd=22000, priority="High"),
        dict(pillar_number=5, activity_number="49.0",
             sub_section="D. Rumour Management",
             activity_name="Implement community feedback and rumour management system",
             total_cost_usd=35000, priority="High"),
        dict(pillar_number=5, activity_number="50.0",
             sub_section="B. Community Sensitization",
             activity_name="Support community-based organisations (CBOs) for RCCE activities",
             total_cost_usd=48000, priority="Medium"),
        dict(pillar_number=5, activity_number="51.0",
             sub_section="E. Mass Media",
             activity_name="Implement mass media campaign (radio, TV, social media)",
             total_cost_usd=85000, priority="High"),
        dict(pillar_number=5, activity_number="52.0",
             sub_section="A. Key Messages",
             activity_name="Produce and distribute IEC materials (posters, leaflets, banners)",
             total_cost_usd=38000, priority="Medium"),
        dict(pillar_number=5, activity_number="53.0",
             sub_section="F. Monitoring",
             activity_name="Monitor and evaluate RCCE activities and community knowledge",
             total_cost_usd=0, priority="Medium"),
        dict(pillar_number=5, activity_number="54.0",
             sub_section="C. Community Leaders",
             activity_name="Organise community dialogues, town halls and public health engagement",
             total_cost_usd=28000, priority="Medium"),
        dict(pillar_number=5, activity_number="55.0",
             sub_section="D. Rumour Management",
             activity_name="Establish EVD public hotline and information desk",
             total_cost_usd=15000, priority="Medium"),

        # ── PILLAR 6 — Operational Support and Logistics ─────────────────────
        dict(pillar_number=6, activity_number="56.0",
             sub_section="A. Supply Chain",
             activity_name="Establish and operate logistics and supply chain management system",
             total_cost_usd=145000, priority="High"),
        dict(pillar_number=6, activity_number="57.0",
             sub_section="A. Supply Chain",
             activity_name="Procure and distribute PPE and essential health supplies to districts",
             total_cost_usd=285000, priority="High"),
        dict(pillar_number=6, activity_number="58.0",
             sub_section="B. Transport",
             activity_name="Provide transportation and fleet management for response teams",
             total_cost_usd=165000, priority="High"),
        dict(pillar_number=6, activity_number="59.0",
             sub_section="C. Field Coordination",
             activity_name="Establish and operate field coordination sites in high-risk districts",
             total_cost_usd=85000, priority="High"),
        dict(pillar_number=6, activity_number="60.0",
             sub_section="D. Staff Welfare",
             activity_name="Support staff accommodation, per diem and duty of care",
             total_cost_usd=120000, priority="Medium"),
        dict(pillar_number=6, activity_number="61.0",
             sub_section="E. IT and Communications",
             activity_name="Procure fuel, ICT equipment and communications supplies",
             total_cost_usd=68000, priority="Medium"),
        dict(pillar_number=6, activity_number="62.0",
             sub_section="E. IT and Communications",
             activity_name="Establish and maintain communication systems (radio, satellite, internet)",
             total_cost_usd=45000, priority="Medium"),
        dict(pillar_number=6, activity_number="63.0",
             sub_section="D. Staff Welfare",
             activity_name="Provide food and essential supplies for deployed field staff",
             total_cost_usd=0, priority="Low"),
        dict(pillar_number=6, activity_number="64.0",
             sub_section="B. Transport",
             activity_name="Support air transportation for remote and inaccessible areas",
             total_cost_usd=180000, priority="High"),
        dict(pillar_number=6, activity_number="65.0",
             sub_section="A. Supply Chain",
             activity_name="Track, report and account for supplies and expenditures",
             total_cost_usd=0, priority="Medium"),

        # ── PILLAR 7 — Research and Strategic Information ─────────────────────
        dict(pillar_number=7, activity_number="66.0",
             sub_section="A. Data Management",
             activity_name="Set up EVD surveillance data management and information system",
             total_cost_usd=35000, priority="Medium"),
        dict(pillar_number=7, activity_number="67.0",
             sub_section="B. Operational Research",
             activity_name="Conduct operational research on BDBV transmission dynamics and risk factors",
             total_cost_usd=85000, priority="Medium"),
        dict(pillar_number=7, activity_number="68.0",
             sub_section="C. Vaccine Research",
             activity_name="Evaluate ring vaccination efficacy and adverse events",
             total_cost_usd=0, priority="High"),
        dict(pillar_number=7, activity_number="69.0",
             sub_section="D. After-Action Review",
             activity_name="Conduct after-action reviews (AAR) and lessons learned exercises",
             total_cost_usd=18000, priority="Medium"),
        dict(pillar_number=7, activity_number="70.0",
             sub_section="E. Dissemination",
             activity_name="Support academic publications and findings dissemination",
             total_cost_usd=12000, priority="Low"),
        dict(pillar_number=7, activity_number="71.0",
             sub_section="A. Data Management",
             activity_name="Establish EVD knowledge management and document repository",
             total_cost_usd=0, priority="Low"),
        dict(pillar_number=7, activity_number="72.0",
             sub_section="B. Operational Research",
             activity_name="Conduct serosurveillance and seroprevalence studies in affected areas",
             total_cost_usd=65000, priority="Medium"),
        dict(pillar_number=7, activity_number="73.0",
             sub_section="D. After-Action Review",
             activity_name="Support external evaluation and independent response review",
             total_cost_usd=28000, priority="Medium"),
    ]

    PILLAR_NAMES = {
        1: "Leadership and Coordination",
        2: "Epidemiological Surveillance",
        3: "Laboratory and Diagnostics",
        4: "Case Management, IPC/WASH and SDB",
        5: "Risk Communication and Community Engagement",
        6: "Operational Support and Logistics",
        7: "Research and Strategic Information",
    }

    with app.app_context():
        count = 0
        for d in activities_data:
            existing = GovernmentActivity.query.filter_by(
                activity_number=d["activity_number"]
            ).first()
            if existing:
                continue
            a = GovernmentActivity(
                activity_number=d["activity_number"],
                pillar=PILLAR_NAMES[d["pillar_number"]],
                pillar_number=d["pillar_number"],
                sub_section=d.get("sub_section", ""),
                activity_name=d["activity_name"],
                total_cost_usd=d.get("total_cost_usd", 0),
                status="Planned",
                priority=d.get("priority", "Medium"),
            )
            db.session.add(a)
            count += 1
        db.session.commit()
        print(f"Seeded {count} government activities.")


def seed_partner_contributions(app, mob_partner_ids):
    """Seed partner contributions from the Excel 'Partner Support Updated' sheet."""

    def _get_activity_id(activity_number):
        a = GovernmentActivity.query.filter_by(activity_number=activity_number).first()
        return a.id if a else None

    # (activity_number, partner_name, amount_pledged_usd)
    contributions_data = [
        # ── Pillar 1 contributions (from Excel) ──────────────────────────────
        ("7.0",  "WHO",              52000),
        ("7.0",  "UNICEF",           10000),
        ("7.0",  "CHAI",              5216),
        ("8.0",  "IOM",              70000),
        ("8.0",  "US CDC",           65000),
        ("10.0", "IOM",               8000),
        ("10.0", "WHO",               5000),
        ("10.0", "US CDC",           10000),
        ("10.0", "CHAI",             59388),
        ("11.0", "IOM",               4432),
        ("11.0", "CHAI",            170921),
        ("12.0", "IOM",              24238),
        ("12.0", "WHO",              10000),
        ("12.0", "US CDC",            5000),
        ("12.0", "Enabel/Tribe Hub",  5000),
        # ── Pillar 2 contributions ────────────────────────────────────────────
        ("16.0", "WHO",              45000),
        ("16.0", "US CDC",           35000),
        ("17.0", "WHO",              30000),
        ("17.0", "Africa CDC",       25000),
        ("18.0", "UNICEF",           20000),
        ("18.0", "WHO",              12000),
        ("20.0", "IOM",              60000),
        ("20.0", "US CDC",           55000),
        ("20.0", "WHO",              40000),
        ("21.0", "IOM",              30000),
        ("21.0", "WHO",              25000),
        ("24.0", "US CDC",           35000),
        # ── Pillar 3 contributions ────────────────────────────────────────────
        ("26.0", "WHO",              80000),
        ("26.0", "US CDC",           70000),
        ("27.0", "WHO",              60000),
        ("27.0", "US CDC",           50000),
        ("28.0", "IOM",              25000),
        ("28.0", "WHO",              20000),
        ("29.0", "WHO",              18000),
        ("30.0", "UNICEF",           55000),
        ("30.0", "WHO",              40000),
        # ── Pillar 4 contributions ────────────────────────────────────────────
        ("34.0", "WHO",             120000),
        ("34.0", "IOM",              80000),
        ("35.0", "WHO",             100000),
        ("35.0", "UNICEF",           75000),
        ("36.0", "WHO",              22000),
        ("36.0", "US CDC",           18000),
        ("37.0", "WHO",              38000),
        ("37.0", "UNICEF",           28000),
        ("38.0", "UNICEF",           90000),
        ("38.0", "IOM",              55000),
        ("38.0", "WHO",              40000),
        ("39.0", "WHO",              20000),
        ("40.0", "IOM",              35000),
        ("40.0", "WHO",              25000),
        ("41.0", "UNICEF",           20000),
        ("42.0", "UNICEF",           70000),
        ("42.0", "FAO",              30000),
        ("44.0", "UNICEF",           28000),
        ("44.0", "WHO",              18000),
        # ── Pillar 5 contributions ────────────────────────────────────────────
        ("46.0", "UNICEF",           10000),
        ("46.0", "WHO",               5000),
        ("47.0", "UNICEF",           40000),
        ("47.0", "IOM",              22000),
        ("47.0", "WHO",              18000),
        ("48.0", "UNICEF",           12000),
        ("49.0", "UNICEF",           15000),
        ("51.0", "IOM",              35000),
        ("51.0", "US State Department", 25000),
        ("52.0", "UNICEF",           18000),
        ("52.0", "WHO",               8000),
        ("54.0", "WHO",              12000),
        ("55.0", "WHO",               8000),
        # ── Pillar 6 contributions ────────────────────────────────────────────
        ("56.0", "IOM",              60000),
        ("56.0", "WHO",              40000),
        ("57.0", "UNICEF",          110000),
        ("57.0", "IOM",              80000),
        ("58.0", "IOM",              70000),
        ("58.0", "WHO",              45000),
        ("59.0", "WHO",              35000),
        ("59.0", "Enabel/Lomesu",    20000),
        ("61.0", "US CDC",           28000),
        ("62.0", "WHO",              20000),
        ("64.0", "IOM",              80000),
        ("64.0", "US State Department", 50000),
        # ── Pillar 7 contributions ────────────────────────────────────────────
        ("66.0", "US CDC",           20000),
        ("67.0", "WHO",              35000),
        ("67.0", "US CDC",           25000),
        ("69.0", "WHO",               8000),
        ("72.0", "WHO",              30000),
        ("72.0", "US CDC",           20000),
        ("73.0", "WHO",              12000),
    ]

    # Also allow "Africa CDC" — it might be in existing partners table
    with app.app_context():
        africa_cdc = Partner.query.filter(Partner.name.ilike("africa cdc")).first()
        if africa_cdc:
            mob_partner_ids["Africa CDC"] = africa_cdc.id

        count = 0
        for act_num, partner_name, amount in contributions_data:
            activity_id = _get_activity_id(act_num)
            partner_id  = mob_partner_ids.get(partner_name)

            if not activity_id or not partner_id:
                continue

            existing = PartnerContribution.query.filter_by(
                government_activity_id=activity_id,
                partner_id=partner_id,
            ).first()
            if existing:
                continue

            c = PartnerContribution(
                government_activity_id=activity_id,
                partner_id=partner_id,
                amount_pledged_usd=float(amount),
                amount_available_usd=float(amount),
                amount_to_mobilize_usd=0,
                amount_disbursed_usd=0,
                modality="Direct Implementation",
                status="Pledged",
            )
            db.session.add(c)
            count += 1

        db.session.commit()
        print(f"Seeded {count} partner contributions.")


if __name__ == "__main__":
    app = create_app()
    print("Starting EVD Response data seeding...")
    clear_tables(app)
    seed_phases(app)
    partner_ids = seed_partners(app)
    seed_resources(app, partner_ids)
    seed_activities(app, partner_ids)
    seed_sitreps(app)
    mob_partner_ids = seed_mobilization_partners(app)
    seed_government_activities(app)
    seed_partner_contributions(app, mob_partner_ids)
    print("\nSeed complete! Run `python app.py` to start the API.")
