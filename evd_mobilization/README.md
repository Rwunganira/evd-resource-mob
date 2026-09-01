# WHO EVD Partner Resource Mobilization System

A two-part application for managing partners, resources, and activities during an Ebola Virus Disease outbreak response.

## Quick Start

```bash
cd evd_mobilization

# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed the database (creates evd_response.db)
python seed_data.py

# 3. Start Flask API (port 5000)
python app.py

# 4. Start Streamlit dashboard (port 8501) — in a second terminal
streamlit run dashboard.py
```

Open http://localhost:8501 in your browser.

## Architecture

```
Flask API (port 5000)
  └── SQLite database (evd_response.db)
        ├── Partners
        ├── Resources
        ├── Activities
        ├── SituationReports
        └── OutbreakPhases

Streamlit Dashboard (port 8501)
  └── Calls Flask API via HTTP
        ├── Overview / Command Center
        ├── Partner Tracker
        ├── Resource Mobilization
        ├── 3W Matrix (Who does What Where)
        ├── Situation Reports
        └── Reports & Export
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| GET/POST | /api/partners | List / create partners |
| GET/PUT/DELETE | /api/partners/<id> | Get / update / deactivate partner |
| GET | /api/partners/summary | Counts by type and status |
| GET/POST | /api/resources | List / create resources |
| PUT | /api/resources/<id> | Update resource |
| GET | /api/resources/total-by-type | Aggregated resource totals |
| GET | /api/resources/funding-gap | Committed vs needed |
| GET | /api/resources/reporting-due | Reports due soon |
| GET/POST | /api/activities | List / log activities |
| PUT | /api/activities/<id> | Update activity |
| GET | /api/activities/3w-matrix | Who does What Where |
| GET/POST | /api/sitreps | List / create situation reports |
| GET | /api/sitreps/latest | Most recent sitrep |
| GET | /api/dashboard/summary | All KPIs in one call |

## Seed Data

Includes 10 realistic partners (USAID, MSF, CDC, UNICEF, Gavi, World Bank, etc.),
15 resource commitments, 20 activities across DRC provinces, and 5 sitreps.

## Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_DEBUG | true | Enable Flask debug mode |
| SECRET_KEY | who-evd-response-2024 | Flask secret key |
| PORT | 5000 | Flask port |
| DATABASE_URL | sqlite:///evd_response.db | Database URI |
