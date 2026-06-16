import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models import User, Partner, GovernmentActivity, PartnerContribution

app = create_app()
with app.app_context():

    # ── Schema migration: drop old tables if they have the old column names ────
    from sqlalchemy import text, inspect
    insp = inspect(db.engine)
    existing_tables = insp.get_table_names()

    if "government_activities" in existing_tables:
        old_cols = [c["name"] for c in insp.get_columns("government_activities")]
        if "pillar" in old_cols:          # old schema detected
            print("Old schema detected — dropping government_activities and partner_contributions …")
            # Drop child table first (satisfies FK constraint without CASCADE)
            is_pg = db.engine.dialect.name == "postgresql"
            db.session.execute(text(
                "DROP TABLE IF EXISTS partner_contributions" + (" CASCADE" if is_pg else "")
            ))
            db.session.execute(text(
                "DROP TABLE IF EXISTS government_activities" + (" CASCADE" if is_pg else "")
            ))
            db.session.commit()
            print("Old tables dropped.")

    db.create_all()
    print("Database tables ready.")

    # ── Admin user ────────────────────────────────────────────────────────────
    admin_email = "samuel.rwunganira@gmail.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(email=admin_email, name="Samuel Rwunganira", role="admin")
        admin.set_password(os.getenv("ADMIN_PASSWORD", "Admin@EVD2024!"))
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {admin_email}")
    else:
        print(f"Admin user already exists: {admin_email}")

    # ── Ensure all mobilization partners exist ────────────────────────────────
    _MOB_PARTNERS = [
        ("IOM",              "UN agency",         "Switzerland"),
        ("WHO",              "UN agency",         "Switzerland"),
        ("UNICEF",           "UN agency",         "USA"),
        ("US CDC",           "Government / MoH",  "USA"),
        ("CHAI",             "International NGO", "USA"),
        ("Enabel/Tribe Hub", "International NGO", "Belgium"),
        ("Enabel/Lomesu",    "International NGO", "Belgium"),
        ("FAO",              "UN agency",         "Italy"),
        ("UNFPA",            "UN agency",         "USA"),
        ("World Bank",       "Bilateral donor",   "USA"),
        ("UNHCR",            "UN agency",         "Switzerland"),
    ]
    for pname, ptype, country in _MOB_PARTNERS:
        if not Partner.query.filter_by(name=pname).first():
            db.session.add(Partner(name=pname, partner_type=ptype,
                                   country=country, status="Active"))
    db.session.commit()
    print("Mobilization partners ensured.")

    # ── Seed government activities (only if empty) ────────────────────────────
    if GovernmentActivity.query.count() == 0:
        print("Seeding government activities …")

        _TA = {
            1: "Leadership and Coordination",
            2: "Epidemiological Surveillance",
            3: "Laboratory and Diagnostics",
            4: "Case Management, IPC/WASH and SDB",
            5: "Risk Communication and Community Engagement",
            6: "Operational Support and Logistics",
            7: "Research and Strategic Information",
        }

        # (ta_number, activity_number, sub_section, activity_name, total_cost_usd, priority)
        # Grand total of all non-zero costs = $26,401,617
        _ACTIVITIES = [
            # ── Technical Area 1: Leadership and Coordination  ($5,091,617) ──
            (1,"1.0", "A. Leadership and Coordination",
             "Activate the National Command Post, IMS and functional TWGs", 0, "High"),
            (1,"2.0", "A. Leadership and Coordination",
             "Complete BDBV EVD readiness checklist", 0, "High"),
            (1,"3.0", "A. Leadership and Coordination",
             "Develop and disseminate the National BDBV EVD Preparedness and Response Plan "
             "including a 72-hour response plan", 0, "High"),
            (1,"4.0", "A. Leadership and Coordination",
             "Activate national and district Rapid Response Teams", 0, "High"),
            (1,"5.0", "A. Leadership and Coordination",
             "Activate multi-sectoral and multi-partner coordination mechanisms", 0, "High"),
            (1,"6.0", "B. Operations Support",
             "Support the National Command Post operations", 1700000, "High"),
            (1,"7.0", "B. Operations Support",
             "Support District Command Post operations in high-risk districts", 500000, "High"),
            (1,"8.0", "B. Operations Support",
             "Hire surge staff and support incentives for staff at POEs", 2583234, "High"),
            (1,"9.0", "C. Assessment and Supervision",
             "Conduct initial BDBV EVD capacity assessment", 25000, "Medium"),
            (1,"10.0","C. Assessment and Supervision",
             "Facilitate integrated regular support supervision", 100000, "Medium"),
            (1,"11.0","D. Cross-border and Regional",
             "Support cross-border coordination activities with DRC", 20000, "Medium"),
            (1,"12.0","C. Assessment and Supervision",
             "Conduct BDBV EVD field simulation exercise", 80000, "Medium"),
            (1,"13.0","C. Assessment and Supervision",
             "Monitor the implementation of the National BDBV EVD Plan", 0, "Medium"),
            (1,"14.0","E. Resource Mobilization",
             "Meeting to mobilize resources", 5000, "Medium"),
            (1,"15.0","A. Leadership and Coordination",
             "Print and distribute BDBV EVD technical guidelines", 78383, "Medium"),
            # ── Technical Area 2: Epidemiological Surveillance  ($4,000,000) ──
            (2,"16.0","A. Surveillance Systems",
             "Activate and strengthen disease surveillance systems in high-risk districts", 1000000, "High"),
            (2,"17.0","A. Surveillance Systems",
             "Train and deploy field epidemiologists to high-risk districts", 700000, "High"),
            (2,"18.0","B. Community-based Surveillance",
             "Establish and strengthen community-based surveillance (CBS) networks", 400000, "High"),
            (2,"19.0","C. Case Investigation",
             "Conduct EVD case investigation and contact listing", 0, "High"),
            (2,"20.0","D. Contact Tracing",
             "Support contact tracing and follow-up in high-risk districts", 1200000, "High"),
            (2,"21.0","E. Border Surveillance",
             "Strengthen Points of Entry (POE) surveillance and screening", 500000, "High"),
            (2,"22.0","F. Data Management",
             "Establish and maintain EVD line listing and database", 50000, "Medium"),
            (2,"23.0","F. Data Management",
             "Conduct epidemiological data analysis and weekly reporting", 0, "Medium"),
            (2,"24.0","D. Contact Tracing",
             "Deploy Go.Data digital contact tracing platform", 100000, "Medium"),
            (2,"25.0","A. Surveillance Systems",
             "Conduct joint EVD surveillance review and coordination meetings", 50000, "Low"),
            # ── Technical Area 3: Laboratory and Diagnostics  ($3,500,000) ──
            (3,"26.0","A. Reference Laboratory",
             "Designate and equip BDBV EVD national reference laboratory", 1200000, "High"),
            (3,"27.0","B. Reagents and Consumables",
             "Procure laboratory reagents and consumables for RT-PCR EVD testing", 800000, "High"),
            (3,"28.0","C. Specimen Transport",
             "Establish specimen referral and safe transport network", 250000, "High"),
            (3,"29.0","D. Capacity Building",
             "Train laboratory personnel on EVD diagnostics and biosafety (BSL-3)", 200000, "Medium"),
            (3,"30.0","E. Rapid Diagnostics",
             "Procure and deploy rapid diagnostic tests (RDTs) for field testing", 500000, "High"),
            (3,"31.0","A. Reference Laboratory",
             "Conduct external quality assessment and proficiency testing", 150000, "Medium"),
            (3,"32.0","A. Reference Laboratory",
             "Establish mobile laboratory capacity for remote district deployment", 400000, "Medium"),
            (3,"33.0","F. Result Reporting",
             "Improve laboratory result reporting and turnaround time", 0, "Medium"),
            # ── Technical Area 4: Case Management, IPC/WASH and SDB  ($6,200,000) ──
            (4,"34.0","A. ETU Operations",
             "Designate, prepare and operationalise Ebola Treatment Units (ETUs)", 1900000, "High"),
            (4,"35.0","A. ETU Operations",
             "Procure clinical supplies, therapeutics and experimental treatment (mAb114)", 1400000, "High"),
            (4,"36.0","A. ETU Operations",
             "Train clinical staff on EVD case management protocols and clinical trials", 300000, "High"),
            (4,"37.0","B. IPC",
             "Establish infection prevention and control (IPC) systems in health facilities", 400000, "High"),
            (4,"38.0","B. IPC",
             "Procure and distribute PPE to all health facilities and community teams", 800000, "High"),
            (4,"39.0","B. IPC",
             "Train healthcare workers on IPC standard precautions and EVD protocols", 200000, "High"),
            (4,"40.0","C. Safe and Dignified Burials",
             "Establish and deploy safe and dignified burial (SDB) teams", 300000, "High"),
            (4,"41.0","C. Safe and Dignified Burials",
             "Procure SDB kits, body bags and burial supplies", 150000, "High"),
            (4,"42.0","D. WASH",
             "Improve WASH infrastructure in affected health facilities", 600000, "High"),
            (4,"43.0","A. ETU Operations",
             "Establish patient referral pathways and ambulance network", 0, "Medium"),
            (4,"44.0","E. Survivor Care",
             "Set up EVD survivor care programme and psychosocial support", 150000, "Medium"),
            (4,"45.0","B. IPC",
             "Monitor and supervise adherence to IPC protocols in health facilities", 0, "Medium"),
            # ── Technical Area 5: Risk Communication and Community Engagement  ($2,000,000) ──
            (5,"46.0","A. Key Messages",
             "Develop, pre-test and disseminate EVD key messages and communication materials", 100000, "High"),
            (5,"47.0","B. Community Sensitization",
             "Conduct community sensitization campaigns in high-risk districts", 450000, "High"),
            (5,"48.0","C. Community Leaders",
             "Engage community, religious and traditional leaders as EVD champions", 150000, "High"),
            (5,"49.0","D. Rumour Management",
             "Implement community feedback and rumour management system", 200000, "High"),
            (5,"50.0","B. Community Sensitization",
             "Support community-based organisations (CBOs) for RCCE activities", 250000, "Medium"),
            (5,"51.0","E. Mass Media",
             "Implement mass media campaign (radio, TV, social media)", 400000, "High"),
            (5,"52.0","A. Key Messages",
             "Produce and distribute IEC materials (posters, leaflets, banners)", 200000, "Medium"),
            (5,"53.0","F. Monitoring",
             "Monitor and evaluate RCCE activities and community knowledge", 0, "Medium"),
            (5,"54.0","C. Community Leaders",
             "Organise community dialogues, town halls and public health engagement", 150000, "Medium"),
            (5,"55.0","D. Rumour Management",
             "Establish EVD public hotline and information desk", 100000, "Medium"),
            # ── Technical Area 6: Operational Support and Logistics  ($4,200,000) ──
            (6,"56.0","A. Supply Chain",
             "Establish and operate logistics and supply chain management system", 600000, "High"),
            (6,"57.0","A. Supply Chain",
             "Procure and distribute PPE and essential health supplies to districts", 1000000, "High"),
            (6,"58.0","B. Transport",
             "Provide transportation and fleet management for response teams", 700000, "High"),
            (6,"59.0","C. Field Coordination",
             "Establish and operate field coordination sites in high-risk districts", 350000, "High"),
            (6,"60.0","D. Staff Welfare",
             "Support staff accommodation, per diem and duty of care", 450000, "Medium"),
            (6,"61.0","E. IT and Communications",
             "Procure fuel, ICT equipment and communications supplies", 250000, "Medium"),
            (6,"62.0","E. IT and Communications",
             "Establish and maintain communication systems (radio, satellite, internet)", 200000, "Medium"),
            (6,"63.0","D. Staff Welfare",
             "Provide food and essential supplies for deployed field staff", 0, "Low"),
            (6,"64.0","B. Transport",
             "Support air transportation for remote and inaccessible areas", 650000, "High"),
            (6,"65.0","A. Supply Chain",
             "Track, report and account for supplies and expenditures", 0, "Medium"),
            # ── Technical Area 7: Research and Strategic Information  ($1,410,000) ──
            (7,"66.0","A. Data Management",
             "Set up EVD surveillance data management and information system", 150000, "Medium"),
            (7,"67.0","B. Operational Research",
             "Conduct operational research on BDBV transmission dynamics and risk factors", 500000, "Medium"),
            (7,"68.0","C. Vaccine Research",
             "Evaluate ring vaccination efficacy and adverse events", 0, "High"),
            (7,"69.0","D. After-Action Review",
             "Conduct after-action reviews (AAR) and lessons learned exercises", 120000, "Medium"),
            (7,"70.0","E. Dissemination",
             "Support academic publications and findings dissemination", 80000, "Low"),
            (7,"71.0","A. Data Management",
             "Establish EVD knowledge management and document repository", 0, "Low"),
            (7,"72.0","B. Operational Research",
             "Conduct serosurveillance and seroprevalence studies in affected areas", 380000, "Medium"),
            (7,"73.0","D. After-Action Review",
             "Support external evaluation and independent response review", 180000, "Medium"),
        ]

        _TA = {
            1: "Leadership and Coordination",
            2: "Epidemiological Surveillance",
            3: "Laboratory and Diagnostics",
            4: "Case Management, IPC/WASH and SDB",
            5: "Risk Communication and Community Engagement",
            6: "Operational Support and Logistics",
            7: "Research and Strategic Information",
        }

        for ta_num, act_num, sub, name, cost, priority in _ACTIVITIES:
            db.session.add(GovernmentActivity(
                activity_number=act_num,
                technical_area=_TA[ta_num],
                technical_area_number=ta_num,
                sub_section=sub,
                activity_name=name,
                total_cost_usd=float(cost),
                status="Planned",
                priority=priority,
            ))
        db.session.commit()
        print("Government activities seeded (73 activities, $26,401,617 total need).")

    # ── Seed partner contributions (only if empty) ────────────────────────────
    if PartnerContribution.query.count() == 0 and GovernmentActivity.query.count() > 0:
        print("Seeding partner contributions …")

        # Per-partner totals:
        # IOM=$754,283  WHO=$174,702  UNICEF=$1,097,444  US CDC=$1,000,000
        # CHAI=$4,514,775  Enabel/Tribe Hub=$66,160  Enabel/Lomesu=$10,000
        # FAO=$79,891  World Bank=$579,000  UNHCR=$83,000
        # Grand total committed: $8,359,255
        _CONTRIB_DATA = [
            # IOM  — $754,283
            ("8.0",  "IOM",  70000),
            ("10.0", "IOM",  8000),
            ("11.0", "IOM",  4432),
            ("12.0", "IOM",  24238),
            ("20.0", "IOM",  60000),
            ("21.0", "IOM",  30000),
            ("28.0", "IOM",  25000),
            ("34.0", "IOM",  80000),
            ("38.0", "IOM",  55000),
            ("40.0", "IOM",  35000),
            ("47.0", "IOM",  22000),
            ("51.0", "IOM",  35000),
            ("56.0", "IOM",  60000),
            ("57.0", "IOM",  80000),
            ("58.0", "IOM",  70000),
            ("64.0", "IOM",  80000),
            ("66.0", "IOM",  15613),
            # WHO  — $174,702
            ("7.0",  "WHO",  52000),
            ("10.0", "WHO",  5000),
            ("12.0", "WHO",  10000),
            ("16.0", "WHO",  45000),
            ("17.0", "WHO",  30000),
            ("18.0", "WHO",  12000),
            ("26.0", "WHO",  20702),
            # UNICEF  — $1,097,444
            ("8.0",  "UNICEF", 10000),
            ("18.0", "UNICEF", 20000),
            ("26.0", "UNICEF", 100000),
            ("27.0", "UNICEF", 100000),
            ("30.0", "UNICEF", 55000),
            ("35.0", "UNICEF", 75000),
            ("36.0", "UNICEF", 50000),
            ("37.0", "UNICEF", 28000),
            ("38.0", "UNICEF", 90000),
            ("39.0", "UNICEF", 50000),
            ("41.0", "UNICEF", 20000),
            ("42.0", "UNICEF", 70000),
            ("44.0", "UNICEF", 28000),
            ("46.0", "UNICEF", 10000),
            ("47.0", "UNICEF", 88444),
            ("48.0", "UNICEF", 12000),
            ("49.0", "UNICEF", 15000),
            ("50.0", "UNICEF", 48000),
            ("52.0", "UNICEF", 18000),
            ("56.0", "UNICEF", 50000),
            ("57.0", "UNICEF", 110000),
            ("59.0", "UNICEF", 50000),
            # US CDC  — $1,000,000
            ("8.0",  "US CDC", 65000),
            ("10.0", "US CDC", 10000),
            ("12.0", "US CDC", 5000),
            ("16.0", "US CDC", 35000),
            ("20.0", "US CDC", 55000),
            ("21.0", "US CDC", 100000),
            ("24.0", "US CDC", 35000),
            ("26.0", "US CDC", 70000),
            ("27.0", "US CDC", 50000),
            ("28.0", "US CDC", 100000),
            ("29.0", "US CDC", 18000),
            ("30.0", "US CDC", 40000),
            ("34.0", "US CDC", 100000),
            ("36.0", "US CDC", 18000),
            ("37.0", "US CDC", 20000),
            ("42.0", "US CDC", 100000),
            ("56.0", "US CDC", 36000),
            ("61.0", "US CDC", 28000),
            ("64.0", "US CDC", 50000),
            ("66.0", "US CDC", 20000),
            ("67.0", "US CDC", 25000),
            ("72.0", "US CDC", 20000),
            # CHAI  — $4,514,775
            ("6.0",  "CHAI",  400000),
            ("7.0",  "CHAI",  300000),
            ("8.0",  "CHAI",  2000000),
            ("10.0", "CHAI",  59388),
            ("34.0", "CHAI",  700000),
            ("35.0", "CHAI",  500000),
            ("36.0", "CHAI",  200000),
            ("37.0", "CHAI",  155387),
            ("42.0", "CHAI",  100000),
            ("44.0", "CHAI",  100000),
            # Enabel/Tribe Hub  — $66,160
            ("12.0", "Enabel/Tribe Hub", 5000),
            ("59.0", "Enabel/Tribe Hub", 20000),
            ("60.0", "Enabel/Tribe Hub", 41160),
            # Enabel/Lomesu  — $10,000
            ("59.0", "Enabel/Lomesu",    10000),
            # FAO  — $79,891
            ("18.0", "FAO", 29891),
            ("42.0", "FAO", 50000),
            # World Bank  — $579,000
            ("34.0", "World Bank", 100000),
            ("42.0", "World Bank", 200000),
            ("56.0", "World Bank", 100000),
            ("57.0", "World Bank", 100000),
            ("66.0", "World Bank",  79000),
            # UNHCR  — $83,000
            ("20.0", "UNHCR", 50000),
            ("47.0", "UNHCR", 33000),
        ]

        for act_num, pname, amount in _CONTRIB_DATA:
            act  = GovernmentActivity.query.filter_by(activity_number=act_num).first()
            pobj = Partner.query.filter_by(name=pname).first()
            if not act:
                print(f"  WARNING: activity {act_num} not found — skipping {pname} ${amount}")
                continue
            db.session.add(PartnerContribution(
                government_activity_id=act.id,
                partner_name=pname,
                partner_id=pobj.id if pobj else None,
                amount_committed_usd=float(amount),
                amount_available_usd=float(amount),
                modality="Direct Implementation",
                status="Committed",
            ))
        db.session.commit()
        print("Partner contributions seeded ($8,359,255 total committed).")

    print("Setup complete.")
