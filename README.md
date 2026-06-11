# EVD Resource Mobilization Tracker

A web application for tracking partner resources, activities, and funding during Ebola Virus Disease (EVD) outbreak response. Built for WHO field coordination teams.

## Features

- **Partner registry** — record organizations by type, operational status, and contact details
- **Activity tracking** — 4W matrix (Who does What, Where, When) with pillar, funding source, timeline status, and modality of support
- **Resource management** — track funding commitments, deployments, and reporting deadlines
- **Situation reports** — log outbreak indicators (cases, deaths, CFR, ETUs operational)
- **Funding gap analysis** — track required vs. funded amounts by response pillar
- **Partner reporting compliance** — weekly/sitrep submission tracking
- **Excel import** — bulk upload via 4W template (.xlsx)
- **Streamlit dashboard** — interactive charts and visualizations consuming the REST API

## Project Structure

```
resource_mob/
├── backend/               # Flask API + HTML management UI
│   ├── app.py             # App factory and entry point
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # DB initialization
│   ├── routes/            # JSON API blueprints (/api/*)
│   │   ├── partners.py
│   │   ├── activities.py
│   │   ├── resources.py
│   │   ├── reports.py
│   │   ├── funding_gap.py
│   │   ├── partner_reports.py
│   │   └── imports.py
│   ├── views/             # HTML view blueprints
│   │   ├── partners.py
│   │   ├── activities.py
│   │   ├── resources.py
│   │   └── sitreps.py
│   ├── templates/         # Jinja2 templates (Bootstrap 5)
│   └── evd_response.db    # SQLite database
└── frontend/
    ├── dashboard.py       # Streamlit dashboard
    └── requirements.txt
```

## Setup

### Prerequisites

- Python 3.10+

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
python app.py
```

The Flask app starts on **http://localhost:5000**.

### Frontend (Streamlit dashboard)

```bash
cd frontend
pip install -r requirements.txt
streamlit run dashboard.py
```

The dashboard starts on **http://localhost:8501** and consumes the Flask API.

### Environment variables

Create a `.env` file in `backend/` to override defaults:

```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///evd_response.db   # or a PostgreSQL URL
FLASK_DEBUG=true
PORT=5000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET/POST | `/api/partners` | List / create partners |
| GET/PUT/DELETE | `/api/partners/<id>` | Get / update / deactivate partner |
| GET | `/api/partners/summary` | Count by type and status |
| GET/POST | `/api/activities` | List / create activities |
| PUT | `/api/activities/<id>` | Update activity |
| GET | `/api/activities/3w-matrix` | Who-What-Where matrix |
| GET | `/api/activities/4w-matrix` | Extended matrix with dates and beneficiaries |
| GET | `/api/activities/4w-matrix/export` | CSV-ready flat export |
| GET/POST | `/api/resources` | List / create resources |
| PUT | `/api/resources/<id>` | Update resource |
| GET | `/api/resources/total-by-type` | Funding totals by type |
| GET | `/api/resources/funding-gap` | Commitment vs. need |
| GET | `/api/resources/reporting-due` | Overdue reports |
| GET/POST | `/api/sitreps` | List / create situation reports |
| GET | `/api/sitreps/latest` | Latest sitrep |
| GET | `/api/dashboard/summary` | Dashboard metrics |
| GET/POST | `/api/funding-gap` | List / create funding gap pillars |
| PUT | `/api/funding-gap/<id>` | Update pillar funding |
| GET | `/api/funding-gap/summary` | Aggregated gap summary |
| GET/POST | `/api/partner-reports` | List / log partner reports |
| GET | `/api/partner-reports/overdue` | Overdue reporters |
| GET | `/api/partner-reports/compliance` | 4-week compliance matrix |
| POST | `/api/import/4w-template` | Bulk import via Excel |

## Controlled Vocabularies

### Partner

| Field | Allowed values |
|-------|---------------|
| Partner type | UN agency, International NGO, National NGO, Government / MoH, Bilateral donor, Red Cross / Red Crescent, Academic / Research, Private sector, Faith-based organization, Community-based organization |
| Operational status | Operational, Mobilizing, On stand-by, Withdrawing, Not present |

### Activity

| Field | Allowed values |
|-------|---------------|
| Status | Planned, Ongoing, Completed, Suspended, Cancelled |
| Funding source | Internal / own funds, CFE (WHO), CERF, Bilateral donor, Country pooled fund, Private donor, Unfunded-gap, Mixed |
| Timeline status | Not started, In progress, Completed, Delayed |
| Modality of support | Direct Implementation, Transfer to Government, Both |

## Database migrations

The app calls `db.create_all()` on startup, which creates tables that do not yet exist. For adding columns to existing tables, run the migration script manually:

```bash
cd backend
python -c "
import sqlite3
conn = sqlite3.connect('evd_response.db')
# Example: add a new column
conn.execute('ALTER TABLE activities ADD COLUMN new_field VARCHAR(100)')
conn.commit()
conn.close()
"
```

## HTML Management UI

The Flask app also serves a Bootstrap 5 data-entry interface at the following routes:

| Path | Description |
|------|-------------|
| `/` | Redirects to partners list |
| `/partners` | Partner list with filters |
| `/partners/new` | Add partner |
| `/partners/<id>/edit` | Edit partner |
| `/activities` | Activity list with filters |
| `/activities/new` | Add activity |
| `/activities/<id>/edit` | Edit activity |
| `/resources` | Resource list |
| `/sitreps` | Situation reports |
