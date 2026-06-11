# EVD Resource Mobilization Tracker

A web application for tracking partner resources, activities, and funding during Ebola Virus Disease (EVD) outbreak response. Built for WHO field coordination teams.

## Live deployment

| Service | URL |
|---------|-----|
| Flask management UI | https://evd-resource-mob-50c0bbf1db4d.herokuapp.com |
| Streamlit dashboard | Deploy via Streamlit Cloud (see setup below) |

## Features

- **Login & roles** — email/password authentication with Admin, Editor, and Viewer roles
- **User management** — admins can create, edit, and deactivate user accounts
- **Partner registry** — record organizations by type, operational status, and contact details
- **Activity tracking** — 4W matrix (Who does What, Where, When) with pillar, funding source, timeline status, and modality of support
- **Resource management** — track funding commitments, deployments, and reporting deadlines
- **Situation reports** — log outbreak indicators (cases, deaths, CFR, ETUs operational)
- **Funding gap analysis** — track required vs. funded amounts by response pillar
- **Partner reporting compliance** — weekly/sitrep submission tracking
- **Excel import** — bulk upload via 4W template (.xlsx)
- **Streamlit dashboard** — interactive charts and visualizations consuming the REST API

## Project structure

```
resource_mob/
├── Procfile                   # Heroku: release phase (db setup) + web (gunicorn)
├── requirements.txt           # Flask backend dependencies
├── .python-version            # Python 3.13
├── backend/
│   ├── app.py                 # App factory, LoginManager, blueprints
│   ├── models.py              # SQLAlchemy models (User, Partner, Resource, …)
│   ├── database.py            # DB init helper
│   ├── setup_db.py            # Release-phase script: create tables + seed admin
│   ├── routes/                # JSON API blueprints (/api/*)
│   │   ├── partners.py
│   │   ├── activities.py
│   │   ├── resources.py
│   │   ├── reports.py
│   │   ├── funding_gap.py
│   │   ├── partner_reports.py
│   │   └── imports.py
│   ├── views/                 # HTML view blueprints (login-protected)
│   │   ├── auth.py            # /auth/login, /auth/logout
│   │   ├── users.py           # /users  (admin only)
│   │   ├── partners.py
│   │   ├── activities.py
│   │   ├── resources.py
│   │   └── sitreps.py
│   └── templates/             # Jinja2 templates (Bootstrap 5, WHO blue theme)
│       ├── base.html
│       ├── auth/login.html
│       ├── users/
│       ├── partners/
│       ├── activities/
│       ├── resources/
│       └── sitreps/
└── frontend/
    ├── dashboard.py           # Streamlit dashboard (calls Flask API)
    └── requirements.txt
```

## Local setup

### Prerequisites

- Python 3.11+

### Backend (Flask)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r ../requirements.txt
python setup_db.py           # creates tables + admin user
python app.py
```

Flask starts on **http://localhost:5000**. Log in with the admin credentials printed by `setup_db.py`.

### Frontend (Streamlit dashboard)

```bash
cd frontend
pip install -r requirements.txt
streamlit run dashboard.py
```

The dashboard starts on **http://localhost:8501** and reads `FLASK_URL` from the environment (defaults to `http://localhost:5000`).

### Environment variables

Create a `.env` file in `backend/` (never commit it):

```
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite:///evd_response.db   # PostgreSQL URL in production
FLASK_DEBUG=true
PORT=5000
ADMIN_PASSWORD=Admin@EVD2024!            # initial admin password (setup_db.py)
STREAMLIT_URL=http://localhost:8501      # shown in sidebar Visualizations link
```

## Authentication & roles

All HTML management pages require login. The JSON API (`/api/*`) is open for Streamlit.

| Role | Badge | Permissions |
|------|-------|-------------|
| **admin** | red | Full access, user management |
| **editor** | blue | Add and edit all data |
| **viewer** | grey | Read-only access |

The first admin account (`samuel.rwunganira@gmail.com`) is seeded automatically on first deploy. Additional users are managed at `/users`.

## Deployment

### Flask → Heroku

```bash
# One-time setup
heroku create <app-name>
heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY=<random> ADMIN_PASSWORD=<password>

# Deploy
git push heroku master:main
```

The `Procfile` release phase runs `setup_db.py` once before the web dyno starts, creating all tables and seeding the admin user.

### Streamlit dashboard → Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and connect the GitHub repo `Rwunganira/evd-resource-mob`
2. Set **Main file path** to `frontend/dashboard.py`
3. In **Advanced settings → Secrets** add:

```toml
FLASK_URL = "https://<your-heroku-app>.herokuapp.com"
```

After deploying, set `STREAMLIT_URL` on Heroku so the sidebar link points to the live dashboard:

```bash
heroku config:set STREAMLIT_URL=https://<your-streamlit-app>.streamlit.app
```

## HTML routes

| Path | Access | Description |
|------|--------|-------------|
| `/` | any | Redirects to partners list |
| `/auth/login` | public | Login page |
| `/auth/logout` | logged in | Logout |
| `/users` | admin | User list |
| `/users/new` | admin | Add user |
| `/users/<id>/edit` | admin | Edit user |
| `/partners` | logged in | Partner list with filters |
| `/partners/new` | logged in | Add partner |
| `/partners/<id>/edit` | logged in | Edit partner |
| `/activities` | logged in | Activity list |
| `/activities/new` | logged in | Add activity |
| `/activities/<id>/edit` | logged in | Edit activity |
| `/resources` | logged in | Resource list |
| `/sitreps` | logged in | Situation reports |

## API endpoints

All endpoints are under `/api/` and return `{"status": "success"|"error", "data": …, "message": …}`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET / POST | `/api/partners` | List / create partners |
| GET / PUT / DELETE | `/api/partners/<id>` | Get / update / deactivate |
| GET | `/api/partners/summary` | Count by type and status |
| GET / POST | `/api/activities` | List / create activities |
| PUT | `/api/activities/<id>` | Update activity |
| GET | `/api/activities/3w-matrix` | Who-What-Where matrix |
| GET | `/api/activities/4w-matrix` | Extended matrix with dates |
| GET | `/api/activities/4w-matrix/export` | CSV-ready flat export |
| GET / POST | `/api/resources` | List / create resources |
| PUT | `/api/resources/<id>` | Update resource |
| GET | `/api/resources/total-by-type` | Funding totals by type |
| GET | `/api/resources/funding-gap` | Commitment vs. need |
| GET | `/api/resources/reporting-due` | Overdue reports |
| GET / POST | `/api/sitreps` | List / create situation reports |
| GET | `/api/sitreps/latest` | Latest sitrep |
| GET | `/api/dashboard/summary` | Dashboard metrics |
| GET / POST | `/api/funding-gap` | List / create funding gap pillars |
| PUT | `/api/funding-gap/<id>` | Update pillar funding |
| GET | `/api/funding-gap/summary` | Aggregated gap summary |
| GET / POST | `/api/partner-reports` | List / log partner reports |
| GET | `/api/partner-reports/overdue` | Overdue reporters |
| GET | `/api/partner-reports/compliance` | 4-week compliance matrix |
| POST | `/api/import/4w-template` | Bulk import via Excel (.xlsx) |

## Controlled vocabularies

### Partner

| Field | Allowed values |
|-------|----------------|
| Type | UN agency, International NGO, National NGO, Government / MoH, Bilateral donor, Red Cross / Red Crescent, Academic / Research, Private sector, Faith-based organization, Community-based organization |
| Status | Operational, Mobilizing, On stand-by, Withdrawing, Not present |

### Activity

| Field | Allowed values |
|-------|----------------|
| Status | Planned, Ongoing, Completed, Suspended, Cancelled |
| Funding source | Internal / own funds, CFE (WHO), CERF, Bilateral donor, Country pooled fund, Private donor, Unfunded-gap, Mixed |
| Timeline status | Not started, In progress, Completed, Delayed |
| Modality of support | Direct Implementation, Transfer to Government, Both |
