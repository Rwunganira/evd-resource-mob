import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models import User, Partner, GovernmentActivity, PartnerContribution

app = create_app()
with app.app_context():
    db.create_all()
    print("Database tables ready.")

    # ── Admin user ────────────────────────────────────────────────────────────
    admin_email = "samuel.rwunganira@gmail.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            name="Samuel Rwunganira",
            role="admin",
        )
        admin.set_password(os.getenv("ADMIN_PASSWORD", "Admin@EVD2024!"))
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {admin_email}")
    else:
        print(f"Admin user already exists: {admin_email}")

    # ── Seed government activities (only if table is empty) ───────────────────
    if GovernmentActivity.query.count() == 0:
        print("Seeding government activities…")
        _PILLARS = {
            1: "Leadership and Coordination",
            2: "Epidemiological Surveillance",
            3: "Laboratory and Diagnostics",
            4: "Case Management, IPC/WASH and SDB",
            5: "Risk Communication and Community Engagement",
            6: "Operational Support and Logistics",
            7: "Research and Strategic Information",
        }
        _ACTIVITIES = [
            # Pillar 1
            (1,"1.0","A. Leadership and Coordination","Activate the National Command Post, IMS and functional TWGs",0,"High"),
            (1,"2.0","A. Leadership and Coordination","Complete BDBV EVD readiness checklist",0,"High"),
            (1,"3.0","A. Leadership and Coordination","Develop and disseminate the National BDBV EVD Preparedness and Response Plan including a 72-hour response plan",0,"High"),
            (1,"4.0","A. Leadership and Coordination","Activate national and district Rapid Response Teams",0,"High"),
            (1,"5.0","A. Leadership and Coordination","Activate multi-sectoral and multi-partner coordination mechanisms",0,"High"),
            (1,"6.0","B. Operations Support","Support the National Command Post operations",748746,"High"),
            (1,"7.0","B. Operations Support","Support District Command Post operations in high-risk districts",184679,"High"),
            (1,"8.0","B. Operations Support","Hire surge staff and support incentives for staff at POEs",1465554,"High"),
            (1,"9.0","C. Assessment and Supervision","Conduct initial BDBV EVD capacity assessment",10260,"Medium"),
            (1,"10.0","C. Assessment and Supervision","Facilitate integrated regular support supervision",39694,"Medium"),
            (1,"11.0","D. Cross-border and Regional","Support cross-border coordination activities with DRC",4432,"Medium"),
            (1,"12.0","C. Assessment and Supervision","Conduct BDBV EVD field simulation exercise",27360,"Medium"),
            (1,"13.0","C. Assessment and Supervision","Monitor the implementation of the National BDBV EVD Plan",0,"Medium"),
            (1,"14.0","E. Resource Mobilization","Meeting to mobilize resources",2052,"Medium"),
            (1,"15.0","A. Leadership and Coordination","Print and distribute BDBV EVD technical guidelines",34884,"Medium"),
            # Pillar 2
            (2,"16.0","A. Surveillance Systems","Activate and strengthen disease surveillance systems in high-risk districts",120000,"High"),
            (2,"17.0","A. Surveillance Systems","Train and deploy field epidemiologists to high-risk districts",85000,"High"),
            (2,"18.0","B. Community-based Surveillance","Establish and strengthen community-based surveillance (CBS) networks",45000,"High"),
            (2,"19.0","C. Case Investigation","Conduct EVD case investigation and contact listing",0,"High"),
            (2,"20.0","D. Contact Tracing","Support contact tracing and follow-up in high-risk districts",180000,"High"),
            (2,"21.0","E. Border Surveillance","Strengthen Points of Entry (POE) surveillance and screening",90000,"High"),
            (2,"22.0","F. Data Management","Establish and maintain EVD line listing and database",15000,"Medium"),
            (2,"23.0","F. Data Management","Conduct epidemiological data analysis and weekly reporting",0,"Medium"),
            (2,"24.0","D. Contact Tracing","Deploy Go.Data digital contact tracing platform",35000,"Medium"),
            (2,"25.0","A. Surveillance Systems","Conduct joint EVD surveillance review and coordination meetings",12000,"Low"),
            # Pillar 3
            (3,"26.0","A. Reference Laboratory","Designate and equip BDBV EVD national reference laboratory",245000,"High"),
            (3,"27.0","B. Reagents and Consumables","Procure laboratory reagents and consumables for RT-PCR EVD testing",185000,"High"),
            (3,"28.0","C. Specimen Transport","Establish specimen referral and safe transport network",65000,"High"),
            (3,"29.0","D. Capacity Building","Train laboratory personnel on EVD diagnostics and biosafety (BSL-3)",38000,"Medium"),
            (3,"30.0","E. Rapid Diagnostics","Procure and deploy rapid diagnostic tests (RDTs) for field testing",120000,"High"),
            (3,"31.0","A. Reference Laboratory","Conduct external quality assessment and proficiency testing",22000,"Medium"),
            (3,"32.0","A. Reference Laboratory","Establish mobile laboratory capacity for remote district deployment",0,"Medium"),
            (3,"33.0","F. Result Reporting","Improve laboratory result reporting and turnaround time",0,"Medium"),
            # Pillar 4
            (4,"34.0","A. ETU Operations","Designate, prepare and operationalise Ebola Treatment Units (ETUs)",425000,"High"),
            (4,"35.0","A. ETU Operations","Procure clinical supplies, therapeutics and experimental treatment (mAb114)",380000,"High"),
            (4,"36.0","A. ETU Operations","Train clinical staff on EVD case management protocols and clinical trials",55000,"High"),
            (4,"37.0","B. IPC","Establish infection prevention and control (IPC) systems in health facilities",95000,"High"),
            (4,"38.0","B. IPC","Procure and distribute PPE to all health facilities and community teams",210000,"High"),
            (4,"39.0","B. IPC","Train healthcare workers on IPC standard precautions and EVD protocols",48000,"High"),
            (4,"40.0","C. Safe and Dignified Burials","Establish and deploy safe and dignified burial (SDB) teams",85000,"High"),
            (4,"41.0","C. Safe and Dignified Burials","Procure SDB kits, body bags and burial supplies",45000,"High"),
            (4,"42.0","D. WASH","Improve WASH infrastructure in affected health facilities",180000,"High"),
            (4,"43.0","A. ETU Operations","Establish patient referral pathways and ambulance network",0,"Medium"),
            (4,"44.0","E. Survivor Care","Set up EVD survivor care programme and psychosocial support",62000,"Medium"),
            (4,"45.0","B. IPC","Monitor and supervise adherence to IPC protocols in health facilities",0,"Medium"),
            # Pillar 5
            (5,"46.0","A. Key Messages","Develop, pre-test and disseminate EVD key messages and communication materials",18000,"High"),
            (5,"47.0","B. Community Sensitization","Conduct community sensitization campaigns in high-risk districts",95000,"High"),
            (5,"48.0","C. Community Leaders","Engage community, religious and traditional leaders as EVD champions",22000,"High"),
            (5,"49.0","D. Rumour Management","Implement community feedback and rumour management system",35000,"High"),
            (5,"50.0","B. Community Sensitization","Support community-based organisations (CBOs) for RCCE activities",48000,"Medium"),
            (5,"51.0","E. Mass Media","Implement mass media campaign (radio, TV, social media)",85000,"High"),
            (5,"52.0","A. Key Messages","Produce and distribute IEC materials (posters, leaflets, banners)",38000,"Medium"),
            (5,"53.0","F. Monitoring","Monitor and evaluate RCCE activities and community knowledge",0,"Medium"),
            (5,"54.0","C. Community Leaders","Organise community dialogues, town halls and public health engagement",28000,"Medium"),
            (5,"55.0","D. Rumour Management","Establish EVD public hotline and information desk",15000,"Medium"),
            # Pillar 6
            (6,"56.0","A. Supply Chain","Establish and operate logistics and supply chain management system",145000,"High"),
            (6,"57.0","A. Supply Chain","Procure and distribute PPE and essential health supplies to districts",285000,"High"),
            (6,"58.0","B. Transport","Provide transportation and fleet management for response teams",165000,"High"),
            (6,"59.0","C. Field Coordination","Establish and operate field coordination sites in high-risk districts",85000,"High"),
            (6,"60.0","D. Staff Welfare","Support staff accommodation, per diem and duty of care",120000,"Medium"),
            (6,"61.0","E. IT and Communications","Procure fuel, ICT equipment and communications supplies",68000,"Medium"),
            (6,"62.0","E. IT and Communications","Establish and maintain communication systems (radio, satellite, internet)",45000,"Medium"),
            (6,"63.0","D. Staff Welfare","Provide food and essential supplies for deployed field staff",0,"Low"),
            (6,"64.0","B. Transport","Support air transportation for remote and inaccessible areas",180000,"High"),
            (6,"65.0","A. Supply Chain","Track, report and account for supplies and expenditures",0,"Medium"),
            # Pillar 7
            (7,"66.0","A. Data Management","Set up EVD surveillance data management and information system",35000,"Medium"),
            (7,"67.0","B. Operational Research","Conduct operational research on BDBV transmission dynamics and risk factors",85000,"Medium"),
            (7,"68.0","C. Vaccine Research","Evaluate ring vaccination efficacy and adverse events",0,"High"),
            (7,"69.0","D. After-Action Review","Conduct after-action reviews (AAR) and lessons learned exercises",18000,"Medium"),
            (7,"70.0","E. Dissemination","Support academic publications and findings dissemination",12000,"Low"),
            (7,"71.0","A. Data Management","Establish EVD knowledge management and document repository",0,"Low"),
            (7,"72.0","B. Operational Research","Conduct serosurveillance and seroprevalence studies in affected areas",65000,"Medium"),
            (7,"73.0","D. After-Action Review","Support external evaluation and independent response review",28000,"Medium"),
        ]
        for pnum, anum, sub, name, cost, priority in _ACTIVITIES:
            db.session.add(GovernmentActivity(
                activity_number=anum,
                pillar=_PILLARS[pnum],
                pillar_number=pnum,
                sub_section=sub,
                activity_name=name,
                total_cost_usd=cost,
                status="Planned",
                priority=priority,
            ))
        db.session.commit()
        print("Government activities seeded.")

    # ── Seed mobilization partners (only if not present) ─────────────────────
    _MOB_PARTNERS = [
        ("IOM", "NGO", "Switzerland"),
        ("WHO", "Government", "Switzerland"),
        ("UNICEF", "NGO", "USA"),
        ("US CDC", "Government", "USA"),
        ("US State Department", "Government", "USA"),
        ("CHAI", "NGO", "USA"),
        ("Enabel/Tribe Hub", "NGO", "Belgium"),
        ("Enabel/Lomesu", "NGO", "Belgium"),
        ("FAO", "Government", "Italy"),
    ]
    for pname, ptype, country in _MOB_PARTNERS:
        if not Partner.query.filter_by(name=pname).first():
            db.session.add(Partner(name=pname, partner_type=ptype,
                                   country=country, status="Active"))
    db.session.commit()

    # ── Seed partner contributions (only if table is empty) ───────────────────
    if PartnerContribution.query.count() == 0 and GovernmentActivity.query.count() > 0:
        print("Seeding partner contributions…")
        _CONTRIB_DATA = [
            ("7.0","WHO",52000), ("7.0","UNICEF",10000), ("7.0","CHAI",5216),
            ("8.0","IOM",70000), ("8.0","US CDC",65000),
            ("10.0","IOM",8000), ("10.0","WHO",5000), ("10.0","US CDC",10000), ("10.0","CHAI",59388),
            ("11.0","IOM",4432), ("11.0","CHAI",170921),
            ("12.0","IOM",24238), ("12.0","WHO",10000), ("12.0","US CDC",5000), ("12.0","Enabel/Tribe Hub",5000),
            ("16.0","WHO",45000), ("16.0","US CDC",35000),
            ("17.0","WHO",30000),
            ("18.0","UNICEF",20000), ("18.0","WHO",12000),
            ("20.0","IOM",60000), ("20.0","US CDC",55000), ("20.0","WHO",40000),
            ("21.0","IOM",30000), ("21.0","WHO",25000),
            ("24.0","US CDC",35000),
            ("26.0","WHO",80000), ("26.0","US CDC",70000),
            ("27.0","WHO",60000), ("27.0","US CDC",50000),
            ("28.0","IOM",25000), ("28.0","WHO",20000),
            ("29.0","WHO",18000),
            ("30.0","UNICEF",55000), ("30.0","WHO",40000),
            ("34.0","WHO",120000), ("34.0","IOM",80000),
            ("35.0","WHO",100000), ("35.0","UNICEF",75000),
            ("36.0","WHO",22000), ("36.0","US CDC",18000),
            ("37.0","WHO",38000), ("37.0","UNICEF",28000),
            ("38.0","UNICEF",90000), ("38.0","IOM",55000), ("38.0","WHO",40000),
            ("39.0","WHO",20000),
            ("40.0","IOM",35000), ("40.0","WHO",25000),
            ("41.0","UNICEF",20000),
            ("42.0","UNICEF",70000), ("42.0","FAO",30000),
            ("44.0","UNICEF",28000), ("44.0","WHO",18000),
            ("46.0","UNICEF",10000), ("46.0","WHO",5000),
            ("47.0","UNICEF",40000), ("47.0","IOM",22000), ("47.0","WHO",18000),
            ("48.0","UNICEF",12000),
            ("49.0","UNICEF",15000),
            ("51.0","IOM",35000), ("51.0","US State Department",25000),
            ("52.0","UNICEF",18000), ("52.0","WHO",8000),
            ("54.0","WHO",12000),
            ("55.0","WHO",8000),
            ("56.0","IOM",60000), ("56.0","WHO",40000),
            ("57.0","UNICEF",110000), ("57.0","IOM",80000),
            ("58.0","IOM",70000), ("58.0","WHO",45000),
            ("59.0","WHO",35000), ("59.0","Enabel/Lomesu",20000),
            ("61.0","US CDC",28000),
            ("62.0","WHO",20000),
            ("64.0","IOM",80000), ("64.0","US State Department",50000),
            ("66.0","US CDC",20000),
            ("67.0","WHO",35000), ("67.0","US CDC",25000),
            ("69.0","WHO",8000),
            ("72.0","WHO",30000), ("72.0","US CDC",20000),
            ("73.0","WHO",12000),
        ]
        for act_num, pname, amount in _CONTRIB_DATA:
            act = GovernmentActivity.query.filter_by(activity_number=act_num).first()
            prt = Partner.query.filter_by(name=pname).first()
            if act and prt:
                db.session.add(PartnerContribution(
                    government_activity_id=act.id,
                    partner_id=prt.id,
                    amount_pledged_usd=float(amount),
                    amount_available_usd=float(amount),
                    modality="Direct Implementation",
                    status="Pledged",
                ))
        db.session.commit()
        print("Partner contributions seeded.")
