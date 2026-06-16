"""
WHO EVD Partner Resource Mobilization Dashboard
Run: streamlit run dashboard.py
"""
import io
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, datetime

import os
API_BASE = os.getenv("FLASK_URL", "https://evd-resource-mob-50c0bbf1db4d.herokuapp.com").rstrip("/") + "/api"

WHO_BLUE = "#0093D5"
WHO_DARK = "#003D6B"
ALERT_RED = "#CC0000"
WARNING_ORANGE = "#FF6600"
SUCCESS_GREEN = "#008000"

st.set_page_config(
    page_title="WHO EVD Resource Mobilization",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  [data-testid="stSidebar"] {{ background-color: {WHO_DARK}; }}
  [data-testid="stSidebar"] * {{ color: white !important; }}
  .metric-card {{
      background: white; border-left: 5px solid {WHO_BLUE};
      border-radius: 6px; padding: 12px 16px;
      box-shadow: 0 2px 6px rgba(0,0,0,.10);
  }}
  .phase-banner {{
      padding: 10px 20px; border-radius: 6px;
      font-size: 1.1rem; font-weight: 700;
      text-align: center; margin-bottom: 12px;
  }}
  .alert-box {{
      background: #fff3cd; border-left: 4px solid #ffc107;
      padding: 8px 14px; border-radius: 4px; margin: 4px 0;
  }}
  .status-deployed  {{ color: {SUCCESS_GREEN}; font-weight: 600; }}
  .status-committed {{ color: #b8860b; font-weight: 600; }}
  .status-pipeline  {{ color: {WARNING_ORANGE}; font-weight: 600; }}
  .status-review    {{ color: {ALERT_RED}; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def api_get(endpoint: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}/{endpoint.lstrip('/')}", params=params, timeout=5)
        r.raise_for_status()
        return r.json().get("data"), None
    except requests.exceptions.ConnectionError:
        return None, "API unavailable — Flask server is not running."
    except Exception as exc:
        return None, str(exc)


def api_post(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE}/{endpoint.lstrip('/')}", json=payload, timeout=5)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "API unavailable"}, 503
    except Exception as exc:
        return {"status": "error", "message": str(exc)}, 500


def api_put(endpoint: str, payload: dict):
    try:
        r = requests.put(f"{API_BASE}/{endpoint.lstrip('/')}", json=payload, timeout=5)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "API unavailable"}, 503
    except Exception as exc:
        return {"status": "error", "message": str(exc)}, 500


def api_delete(endpoint: str):
    try:
        r = requests.delete(f"{API_BASE}/{endpoint.lstrip('/')}", timeout=5)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "API unavailable"}, 503
    except Exception as exc:
        return {"status": "error", "message": str(exc)}, 500


def api_offline_msg(msg: str):
    st.error(f"API Error: {msg}")
    st.info("Make sure Flask is running: `python app.py`")


def fmt_usd(val):
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;padding:10px 0 4px;'>
      <div style='font-size:2rem;'>🏥</div>
      <div style='font-size:1.1rem;font-weight:800;color:white;'>WHO EOC</div>
      <div style='font-size:.75rem;color:#a0c4e8;'>EVD Response — DRC</div>
    </div>
    <hr style='border-color:#1a5276;margin:8px 0;'>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Overview / Command Center",
            "Partner Tracker",
            "Resource Mobilization",
            "3W Matrix",
            "Situation Reports",
            "Reports & Export",
            "📊 EVD Coverage Analysis",
            "💰 EVD Funding Matrix",
        ],
        label_visibility="collapsed",
    )
    st.markdown("<hr style='border-color:#1a5276;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:.7rem;color:#a0c4e8;'>Last refresh: {datetime.now():%H:%M:%S}</div>", unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW / COMMAND CENTER
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview / Command Center":
    st.title("EVD Response — Command Center")

    summary, err = api_get("dashboard/summary")
    if err:
        api_offline_msg(err)
        st.stop()

    # Outbreak phase banner
    phase = summary.get("current_phase")
    if phase:
        phase_name = phase["phase_name"]
        phase_colors = {
            "Alert": ALERT_RED, "Mobilization": WARNING_ORANGE,
            "Response": "#1a7a1a", "Scale-down": WHO_BLUE, "End": "#555",
        }
        bg = phase_colors.get(phase_name, WHO_BLUE)
        st.markdown(
            f"<div class='phase-banner' style='background:{bg};color:white;'>"
            f"OUTBREAK PHASE: {phase_name.upper()}&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"Day {summary['outbreak_day']} of EVD Response"
            "</div>",
            unsafe_allow_html=True,
        )

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    f = summary.get("funding", {})
    p = summary.get("partners", {})
    sr = summary.get("latest_sitrep") or {}

    col1.metric("Partners Mobilized", p.get("total", 0), delta=f"+{p.get('active', 0)} active")
    col2.metric("Funding Committed", fmt_usd(f.get("total_committed_usd", 0)))
    col3.metric("Funding Gap", fmt_usd(f.get("gap_usd", 0)),
                delta=f"{f.get('coverage_percent', 0):.0f}% covered", delta_color="off")
    col4.metric("ETUs Operational", summary.get("etus_operational", 0))
    col5.metric("Outbreak Day", summary.get("outbreak_day", 0))

    st.divider()

    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.subheader("Latest Situation Report")
        if sr:
            c1, c2, c3 = st.columns(3)
            c1.metric("Confirmed Cases", sr.get("confirmed_cases", 0))
            c2.metric("Deaths", sr.get("deaths", 0))
            c3.metric("CFR %", f"{sr.get('cfr_percent', 0)}%")
            st.caption(f"Report date: {sr.get('report_date')}  |  HCW affected: {sr.get('healthcare_workers_affected', 0)}")
            if sr.get("notes"):
                st.info(sr["notes"])
        else:
            st.warning("No situation reports available.")

        # Funding coverage gauge
        st.subheader("Funding Coverage")
        coverage = f.get("coverage_percent", 0)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=coverage,
            number={"suffix": "%"},
            delta={"reference": 100, "increasing": {"color": SUCCESS_GREEN}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": WHO_BLUE},
                "steps": [
                    {"range": [0, 40], "color": "#ffd0d0"},
                    {"range": [40, 75], "color": "#fff0c0"},
                    {"range": [75, 100], "color": "#d0f0d0"},
                ],
                "threshold": {"line": {"color": ALERT_RED, "width": 3}, "value": 80},
            },
            title={"text": "Funding Coverage"},
        ))
        fig_gauge.update_layout(height=220, margin=dict(t=40, b=0, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_right:
        st.subheader("Alerts")
        due_data, _ = api_get("resources/reporting-due", {"days": 3})
        if due_data:
            overdue = due_data.get("overdue", [])
            due_soon = due_data.get("due_soon", [])
            if overdue:
                st.markdown(f"**{len(overdue)} overdue reports:**")
                for r in overdue:
                    st.markdown(
                        f"<div class='alert-box'>⚠️ <b>{r['partner_name']}</b> — "
                        f"{r['resource_type']} report overdue since {r['next_report_due']}</div>",
                        unsafe_allow_html=True,
                    )
            if due_soon:
                st.markdown(f"**{len(due_soon)} due within 3 days:**")
                for r in due_soon:
                    st.markdown(
                        f"<div class='alert-box' style='background:#e8f4fd;border-color:{WHO_BLUE};'>"
                        f"📋 <b>{r['partner_name']}</b> — due {r['next_report_due']}</div>",
                        unsafe_allow_html=True,
                    )
            if not overdue and not due_soon:
                st.success("No overdue reports in the next 3 days.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — PARTNER TRACKER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Partner Tracker":
    st.title("Partner Tracker")

    partners, err = api_get("partners")
    if err:
        api_offline_msg(err)
        st.stop()

    df = pd.DataFrame(partners)

    if df.empty:
        st.info("No partners found.")
        st.stop()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        types = ["All"] + sorted(df["partner_type"].unique().tolist())
        sel_type = st.selectbox("Filter by Type", types)
    with col2:
        statuses = ["All"] + sorted(df["status"].unique().tolist())
        sel_status = st.selectbox("Filter by Status", statuses)
    with col3:
        countries = ["All"] + sorted(df["country"].unique().tolist())
        sel_country = st.selectbox("Filter by Country", countries)

    filtered = df.copy()
    if sel_type != "All":
        filtered = filtered[filtered["partner_type"] == sel_type]
    if sel_status != "All":
        filtered = filtered[filtered["status"] == sel_status]
    if sel_country != "All":
        filtered = filtered[filtered["country"] == sel_country]

    st.markdown(f"**{len(filtered)} partners** matching filters")
    st.dataframe(
        filtered[["name", "partner_type", "country", "status", "contact_person", "resource_count", "activity_count"]],
        use_container_width=True, hide_index=True,
        column_config={
            "name": "Partner",
            "partner_type": "Type",
            "country": "Country",
            "status": "Status",
            "contact_person": "Contact",
            "resource_count": "Resources",
            "activity_count": "Activities",
        },
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("By Status")
        fig_pie = px.pie(
            df, names="status", title="Partner Status Distribution",
            color_discrete_map={
                "Active": SUCCESS_GREEN, "Negotiating": WHO_BLUE,
                "Pipeline": WARNING_ORANGE, "Inactive": "#aaa",
            },
            hole=0.4,
        )
        fig_pie.update_layout(height=300, margin=dict(t=40, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.subheader("By Type")
        type_counts = df["partner_type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        fig_bar = px.bar(type_counts, x="Count", y="Type", orientation="h",
                         color_discrete_sequence=[WHO_BLUE])
        fig_bar.update_layout(height=300, margin=dict(t=10, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Add new partner
    st.divider()
    st.subheader("Add New Partner")
    with st.form("add_partner_form"):
        fc1, fc2 = st.columns(2)
        p_name = fc1.text_input("Partner Name *")
        p_type = fc2.selectbox("Type *", ["Government", "NGO", "Private", "Academic", "Military", "Community"])
        fd1, fd2 = st.columns(2)
        p_country = fd1.text_input("Country *")
        p_status = fd2.selectbox("Status", ["Pipeline", "Negotiating", "Active"])
        fe1, fe2 = st.columns(2)
        p_contact = fe1.text_input("Contact Person")
        p_email = fe2.text_input("Contact Email")
        submitted = st.form_submit_button("Add Partner", type="primary")
        if submitted:
            if not p_name or not p_country:
                st.error("Name and Country are required.")
            else:
                resp, code = api_post("partners", {
                    "name": p_name, "partner_type": p_type, "country": p_country,
                    "status": p_status, "contact_person": p_contact, "contact_email": p_email,
                })
                if code in (200, 201):
                    st.success(f"Partner '{p_name}' added successfully!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(resp.get("message", "Error adding partner"))

    # Partner detail
    st.divider()
    st.subheader("Partner Detail")
    partner_names = {p["name"]: p["id"] for p in partners}
    selected_name = st.selectbox("Select partner to view detail", ["— select —"] + list(partner_names))
    if selected_name != "— select —":
        detail, _ = api_get(f"partners/{partner_names[selected_name]}")
        if detail:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Type:** {detail['partner_type']}  |  **Country:** {detail['country']}")
                st.markdown(f"**Status:** {detail['status']}  |  **Contact:** {detail.get('contact_person','')} ({detail.get('contact_email','')})")
                st.markdown("**Resources:**")
                if detail["resources"]:
                    st.dataframe(pd.DataFrame(detail["resources"])[["resource_type", "amount", "currency", "status"]],
                                 hide_index=True, use_container_width=True)
            with c2:
                st.markdown("**Activities:**")
                if detail["activities"]:
                    st.dataframe(pd.DataFrame(detail["activities"])[["activity_type", "location", "status"]],
                                 hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — RESOURCE MOBILIZATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Resource Mobilization":
    st.title("Resource Mobilization")

    resources, err = api_get("resources")
    if err:
        api_offline_msg(err)
        st.stop()

    df = pd.DataFrame(resources)

    gap_data, _ = api_get("resources/funding-gap")
    by_type_data, _ = api_get("resources/total-by-type")

    # Top KPIs
    if gap_data:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Committed (USD)", fmt_usd(gap_data["total_committed_usd"]))
        c2.metric("Total Deployed (USD)", fmt_usd(gap_data["total_deployed_usd"]))
        c3.metric("Funding Gap", fmt_usd(gap_data["gap_usd"]))
        c4.metric("Coverage", f"{gap_data['coverage_percent']}%")

    col1, col2 = st.columns(2)

    with col1:
        if by_type_data:
            st.subheader("Resources by Type (USD)")
            type_df = pd.DataFrame(list(by_type_data.items()), columns=["Type", "Amount (USD)"])
            fig_h = px.bar(type_df.sort_values("Amount (USD)"),
                           x="Amount (USD)", y="Type", orientation="h",
                           color_discrete_sequence=[WHO_BLUE])
            fig_h.update_layout(height=280, margin=dict(t=10, b=0))
            st.plotly_chart(fig_h, use_container_width=True)

    with col2:
        if gap_data:
            st.subheader("Funding Gap Gauge")
            committed = gap_data["total_committed_usd"]
            needed = gap_data["estimated_need_usd"]
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=committed / 1_000_000,
                number={"suffix": "M USD"},
                gauge={
                    "axis": {"range": [0, needed / 1_000_000]},
                    "bar": {"color": WHO_BLUE},
                    "threshold": {
                        "line": {"color": ALERT_RED, "width": 3},
                        "value": needed / 1_000_000,
                    },
                },
                title={"text": f"Funding vs Need ({fmt_usd(needed)} total)"},
            ))
            fig_g.update_layout(height=260, margin=dict(t=50, b=0))
            st.plotly_chart(fig_g, use_container_width=True)

    # Funding timeline
    if not df.empty and "commitment_date" in df.columns:
        st.subheader("Funding Commitments Over Time")
        funding_df = df[df["resource_type"] == "Funding"].copy()
        if not funding_df.empty:
            funding_df["commitment_date"] = pd.to_datetime(funding_df["commitment_date"])
            funding_df = funding_df.sort_values("commitment_date")
            funding_df["cumulative"] = funding_df["amount"].cumsum()
            fig_line = px.line(funding_df, x="commitment_date", y="cumulative",
                               labels={"cumulative": "Cumulative USD", "commitment_date": "Date"},
                               markers=True, color_discrete_sequence=[WHO_BLUE])
            fig_line.update_layout(height=240, margin=dict(t=10, b=0))
            st.plotly_chart(fig_line, use_container_width=True)

    # Resources table with color coding
    st.subheader("All Resource Commitments")
    STATUS_COLORS = {
        "Deployed": "background-color:#d4edda",
        "Committed": "background-color:#fff3cd",
        "Pipeline": "background-color:#ffe0b2",
        "Under Review": "background-color:#f8d7da",
    }

    def color_status(val):
        return STATUS_COLORS.get(val, "")

    display_cols = ["partner_name", "resource_type", "description", "amount", "currency", "status", "next_report_due"]
    display_df = df[display_cols].copy() if all(c in df.columns for c in display_cols) else df
    st.dataframe(
        display_df.style.map(color_status, subset=["status"]) if "status" in display_df.columns else display_df,
        use_container_width=True, hide_index=True,
    )

    # Add resource form
    st.divider()
    st.subheader("Add Resource Commitment")
    partners_data, _ = api_get("partners", {"status": "Active"})
    if partners_data:
        partner_map = {p["name"]: p["id"] for p in partners_data}
        with st.form("add_resource_form"):
            g1, g2 = st.columns(2)
            r_partner = g1.selectbox("Partner *", list(partner_map.keys()))
            r_type = g2.selectbox("Resource Type *", ["Funding", "PPE", "Personnel", "Vaccines", "Logistics", "Technical"])
            g3, g4, g5 = st.columns(3)
            r_amount = g3.number_input("Amount", min_value=0.0, step=1000.0)
            r_currency = g4.selectbox("Currency", ["USD", "EUR", "GBP", "In-kind"])
            r_status = g5.selectbox("Status", ["Pipeline", "Committed", "Deployed", "Under Review"])
            r_desc = st.text_area("Description")
            g6, g7, g8 = st.columns(3)
            r_commit = g6.date_input("Commitment Date", value=date.today())
            r_deploy = g7.date_input("Deployment Date", value=None)
            r_freq = g8.selectbox("Reporting Frequency", ["Monthly", "Weekly", "Biweekly", "Quarterly", "Daily"])
            if st.form_submit_button("Add Resource", type="primary"):
                payload = {
                    "partner_id": partner_map[r_partner],
                    "resource_type": r_type,
                    "amount": r_amount,
                    "currency": r_currency,
                    "status": r_status,
                    "description": r_desc,
                    "commitment_date": r_commit.isoformat(),
                    "deployment_date": r_deploy.isoformat() if r_deploy else None,
                    "reporting_frequency": r_freq,
                }
                resp, code = api_post("resources", payload)
                if code in (200, 201):
                    st.success("Resource added!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(resp.get("message", "Error"))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — 3W MATRIX
# ══════════════════════════════════════════════════════════════════════════════
elif page == "3W Matrix":
    st.title("3W Matrix — Who does What Where")

    matrix_data, err = api_get("activities/3w-matrix")
    if err:
        api_offline_msg(err)
        st.stop()

    if not matrix_data:
        st.warning("No activity data available.")
        st.stop()

    matrix = matrix_data["matrix"]
    locations = matrix_data["locations"]
    activity_types = matrix_data["activity_types"]

    # Build DataFrame for 3W table
    rows = []
    for loc in locations:
        row = {"Location": loc}
        for atype in activity_types:
            partners = matrix.get(loc, {}).get(atype, [])
            row[atype] = ", ".join(partners) if partners else ""
        rows.append(row)
    df_3w = pd.DataFrame(rows)

    st.subheader("Active Response Map (3W)")
    if df_3w.empty or "Location" not in df_3w.columns:
        st.info("No 3W data to display yet.")
    else:
        st.dataframe(df_3w.set_index("Location"), use_container_width=True)

    # Activity map (DRC provinces approximate coords)
    PROVINCE_COORDS = {
        "Equateur Province": {"lat": 0.5, "lon": 22.0},
        "Nord-Ubangi": {"lat": 3.5, "lon": 21.5},
        "Sud-Ubangi": {"lat": 2.5, "lon": 21.0},
        "Mbandaka": {"lat": 0.048, "lon": 18.26},
        "Bikoro": {"lat": -0.7, "lon": 18.1},
        "Ingende": {"lat": -0.26, "lon": 18.94},
        "Bolomba": {"lat": -0.4, "lon": 19.37},
    }

    activities, _ = api_get("activities")
    if activities:
        act_df = pd.DataFrame(activities)
        act_df["lat"] = act_df["location"].map(lambda x: PROVINCE_COORDS.get(x, {}).get("lat"))
        act_df["lon"] = act_df["location"].map(lambda x: PROVINCE_COORDS.get(x, {}).get("lon"))
        act_df_map = act_df.dropna(subset=["lat", "lon"])

        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Activity Locations (DRC)")
            if not act_df_map.empty:
                fig_map = px.scatter_mapbox(
                    act_df_map, lat="lat", lon="lon",
                    color="activity_type", hover_name="partner_name",
                    hover_data={"location": True, "status": True, "lat": False, "lon": False},
                    zoom=4, height=400,
                    mapbox_style="open-street-map",
                )
                fig_map.update_layout(margin=dict(t=0, b=0))
                st.plotly_chart(fig_map, use_container_width=True)

        with col2:
            st.subheader("By Activity Type")
            type_cnt = act_df["activity_type"].value_counts().reset_index()
            type_cnt.columns = ["Activity", "Count"]
            fig_act = px.bar(type_cnt, x="Count", y="Activity", orientation="h",
                             color_discrete_sequence=[WHO_BLUE])
            fig_act.update_layout(height=200, margin=dict(t=10, b=0))
            st.plotly_chart(fig_act, use_container_width=True)

            st.subheader("By Status")
            status_cnt = act_df["status"].value_counts().reset_index()
            status_cnt.columns = ["Status", "Count"]
            fig_st = px.pie(status_cnt, names="Status", values="Count", hole=0.4,
                            color_discrete_map={"Ongoing": SUCCESS_GREEN,
                                                "Planned": WHO_BLUE, "Completed": "#888"})
            fig_st.update_layout(height=200, margin=dict(t=10, b=0))
            st.plotly_chart(fig_st, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — SITUATION REPORTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Situation Reports":
    st.title("Situation Reports")

    sitreps, err = api_get("sitreps")
    if err:
        api_offline_msg(err)
        st.stop()

    if sitreps:
        df_sr = pd.DataFrame(sitreps)
        df_sr["report_date"] = pd.to_datetime(df_sr["report_date"])
        df_sr = df_sr.sort_values("report_date")

        # Cases + deaths over time
        st.subheader("Epidemic Curve")
        fig_epi = go.Figure()
        fig_epi.add_trace(go.Scatter(
            x=df_sr["report_date"], y=df_sr["confirmed_cases"],
            name="Confirmed Cases", mode="lines+markers",
            line=dict(color=WARNING_ORANGE, width=2),
        ))
        fig_epi.add_trace(go.Scatter(
            x=df_sr["report_date"], y=df_sr["deaths"],
            name="Deaths", mode="lines+markers",
            line=dict(color=ALERT_RED, width=2),
        ))
        fig_epi.update_layout(height=300, margin=dict(t=10, b=0),
                               xaxis_title="Date", yaxis_title="Count",
                               legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig_epi, use_container_width=True)

        # CFR trend
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Case Fatality Rate (%)")
            fig_cfr = px.line(df_sr, x="report_date", y="cfr_percent",
                              markers=True, color_discrete_sequence=[ALERT_RED])
            fig_cfr.update_layout(height=220, margin=dict(t=10, b=0))
            st.plotly_chart(fig_cfr, use_container_width=True)

        with col2:
            st.subheader("Funding Mobilized (USD)")
            fig_fund = px.bar(df_sr, x="report_date", y="total_funding_mobilized",
                              color_discrete_sequence=[WHO_BLUE])
            fig_fund.update_layout(height=220, margin=dict(t=10, b=0))
            st.plotly_chart(fig_fund, use_container_width=True)

        # Latest sitrep
        latest = sitreps[0]  # already sorted desc by API
        st.subheader(f"Latest SitRep — Day {latest['outbreak_day']} ({latest['report_date']})")
        lc1, lc2, lc3, lc4, lc5 = st.columns(5)
        lc1.metric("Confirmed Cases", latest["confirmed_cases"])
        lc2.metric("Deaths", latest["deaths"])
        lc3.metric("CFR", f"{latest['cfr_percent']}%")
        lc4.metric("HCW Affected", latest["healthcare_workers_affected"])
        lc5.metric("ETUs Operational", latest["etus_operational"])
        if latest.get("notes"):
            st.info(latest["notes"])

    # New sitrep form
    st.divider()
    st.subheader("Submit New Situation Report")
    with st.form("new_sitrep_form"):
        n1, n2 = st.columns(2)
        s_date = n1.date_input("Report Date", value=date.today())
        s_day = n2.number_input("Outbreak Day *", min_value=1, step=1, value=29)
        n3, n4 = st.columns(2)
        s_cases = n3.number_input("Confirmed Cases", min_value=0, step=1)
        s_deaths = n4.number_input("Deaths", min_value=0, step=1)
        n5, n6, n7 = st.columns(3)
        s_hcw = n5.number_input("HCW Affected", min_value=0, step=1)
        s_etu = n6.number_input("ETUs Operational", min_value=0, step=1)
        s_funding = n7.number_input("Funding Mobilized (USD)", min_value=0.0, step=100_000.0)
        s_gap = st.number_input("Funding Gap (USD)", min_value=0.0, step=100_000.0)
        s_notes = st.text_area("Notes / Key messages")
        s_author = st.text_input("Created By", value="WHO EOC")
        if st.form_submit_button("Submit SitRep", type="primary"):
            payload = {
                "report_date": s_date.isoformat(),
                "outbreak_day": int(s_day),
                "confirmed_cases": int(s_cases),
                "deaths": int(s_deaths),
                "healthcare_workers_affected": int(s_hcw),
                "etus_operational": int(s_etu),
                "total_funding_mobilized": float(s_funding),
                "funding_gap": float(s_gap),
                "notes": s_notes,
                "created_by": s_author,
            }
            resp, code = api_post("sitreps", payload)
            if code in (200, 201):
                st.success("Situation report submitted!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(resp.get("message", "Error"))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — REPORTS & EXPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Reports & Export":
    st.title("Reports & Export")

    partners, _ = api_get("partners")
    resources, _ = api_get("resources")
    activities, _ = api_get("activities")
    sitreps, _ = api_get("sitreps")
    due_data, _ = api_get("resources/reporting-due", {"days": 14})

    # Reporting deadlines
    st.subheader("Upcoming Reporting Deadlines (14 days)")
    if due_data:
        overdue = due_data.get("overdue", [])
        due_soon = due_data.get("due_soon", [])
        if overdue:
            st.error(f"{len(overdue)} overdue reports")
            st.dataframe(pd.DataFrame(overdue)[["partner_name", "resource_type", "next_report_due", "reporting_frequency"]],
                         hide_index=True, use_container_width=True)
        if due_soon:
            st.warning(f"{len(due_soon)} reports due within 14 days")
            st.dataframe(pd.DataFrame(due_soon)[["partner_name", "resource_type", "next_report_due", "reporting_frequency"]],
                         hide_index=True, use_container_width=True)

    # Resource utilization
    if resources:
        st.subheader("Resource Utilization Summary")
        r_df = pd.DataFrame(resources)
        summary_tbl = r_df.groupby(["resource_type", "status"])["amount"].sum().reset_index()
        st.dataframe(summary_tbl, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("Export Data")

    col1, col2, col3, col4 = st.columns(4)

    # CSV exports
    if partners:
        p_df = pd.DataFrame(partners)
        col1.download_button(
            "Partners CSV", p_df.to_csv(index=False).encode(),
            file_name="evd_partners.csv", mime="text/csv",
        )
    if resources:
        r_df = pd.DataFrame(resources)
        col2.download_button(
            "Resources CSV", r_df.to_csv(index=False).encode(),
            file_name="evd_resources.csv", mime="text/csv",
        )
    if activities:
        a_df = pd.DataFrame(activities)
        col3.download_button(
            "Activities CSV", a_df.to_csv(index=False).encode(),
            file_name="evd_activities.csv", mime="text/csv",
        )
    if sitreps:
        s_df = pd.DataFrame(sitreps)
        col4.download_button(
            "SitReps CSV", s_df.to_csv(index=False).encode(),
            file_name="evd_sitreps.csv", mime="text/csv",
        )

    # Excel export
    st.divider()
    if st.button("Generate Full Excel Report"):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            if partners:
                pd.DataFrame(partners).to_excel(writer, sheet_name="Partners", index=False)
            if resources:
                pd.DataFrame(resources).to_excel(writer, sheet_name="Resources", index=False)
            if activities:
                pd.DataFrame(activities).to_excel(writer, sheet_name="Activities", index=False)
            if sitreps:
                pd.DataFrame(sitreps).to_excel(writer, sheet_name="SitReps", index=False)
        buf.seek(0)
        st.download_button(
            "Download Excel Report",
            buf,
            file_name=f"EVD_Response_Report_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.success("Excel report ready for download.")




# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — EVD COVERAGE ANALYSIS  (read-only)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 EVD Coverage Analysis":
    C_BLUE  = "#0093D5"
    C_DARK  = "#003865"
    C_GREEN = "#1E8449"
    C_AMBER = "#D97706"
    C_RED   = "#C0392B"

    @st.cache_data(ttl=60)
    def _evd_summary():
        return api_get("evd/summary")

    @st.cache_data(ttl=60)
    def _evd_activities():
        return api_get("evd/activities")

    @st.cache_data(ttl=60)
    def _evd_gaps():
        return api_get("evd/gaps")

    st.title("EVD Preparedness — Coverage Analysis")
    st.caption(
        "Read-only analytics view. Data entry is done via the Flask portal. "
        "Cache refreshes every 60 seconds."
    )

    col_r, _ = st.columns([1, 6])
    with col_r:
        if st.button("🔄 Refresh", key="cov_refresh"):
            st.cache_data.clear()
            st.rerun()

    summary, err = _evd_summary()
    if err or not summary:
        st.error(f"API offline: {err}")
        st.info("Flask server must be running at: " + API_BASE)
        st.stop()

    # ── Top metrics row ───────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Activities",    summary.get("total_activities", 0))
    m2.metric("Govt Budget (USD)",   f"${summary.get('total_cost_usd', 0):,.0f}")
    m3.metric("Committed (USD)",     f"${summary.get('total_committed_usd', 0):,.0f}")
    m4.metric("Funding Gap (USD)",   f"${summary.get('total_funding_gap', 0):,.0f}")
    m5.metric("Overall Coverage",    f"{summary.get('coverage_pct', 0):.1f}%")

    # Coverage progress bar
    cov = summary.get("coverage_pct", 0)
    bar_col = C_GREEN if cov >= 75 else (C_AMBER if cov >= 40 else C_RED)
    st.markdown(
        f"<div style='margin:8px 0 4px;'>"
        f"<span style='font-weight:700;color:{bar_col};'>{cov:.1f}%</span> of the "
        f"${summary.get('total_cost_usd', 0):,.0f} government plan is covered by partner commitments."
        "</div>",
        unsafe_allow_html=True,
    )
    st.progress(min(int(cov), 100))
    st.divider()

    # ── Per-TA stacked bar + gauge ────────────────────────────────────────────
    by_ta = summary.get("by_technical_area", [])
    if by_ta:
        ta_df = pd.DataFrame(by_ta)
        ta_df["short"] = ta_df["technical_area_number"].apply(
            lambda n: f"TA{n}"
        )

        col_chart, col_gauge = st.columns([2.5, 1])

        with col_chart:
            st.subheader("Committed vs Gap by Technical Area")
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Committed",
                x=ta_df["short"],
                y=ta_df["total_committed"],
                marker_color=C_BLUE,
                text=ta_df["coverage_pct"].apply(lambda v: f"{v:.0f}%"),
                textposition="inside",
                textfont=dict(color="white", size=11),
            ))
            fig_bar.add_trace(go.Bar(
                name="Gap (unfunded)",
                x=ta_df["short"],
                y=ta_df["total_gap"],
                marker_color="#F1948A",
            ))
            fig_bar.update_layout(
                barmode="stack",
                height=340,
                margin=dict(t=20, b=0),
                yaxis_title="USD",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_gauge:
            st.subheader("Overall Coverage")
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=round(cov, 1),
                delta={"reference": 50, "increasing": {"color": C_GREEN}},
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar":  {"color": C_BLUE},
                    "steps": [
                        {"range": [0,  40], "color": "#FADBD8"},
                        {"range": [40, 75], "color": "#FDEBD0"},
                        {"range": [75,100], "color": "#D5F5E3"},
                    ],
                },
            ))
            fig_g.update_layout(height=260, margin=dict(t=20, b=0, l=20, r=20))
            st.plotly_chart(fig_g, use_container_width=True)

    # ── Per-TA summary table ──────────────────────────────────────────────────
    if by_ta:
        st.subheader("Technical Area Summary")
        hdr_cols = st.columns([0.5, 3.5, 1.2, 1.2, 1.2, 0.8, 0.7])
        for hc, ht in zip(hdr_cols,
                          ["TA", "Name", "Govt Cost", "Committed", "Gap", "Cov %", "Acts"]):
            hc.markdown(f"**{ht}**")
        st.divider()
        for row in sorted(by_ta, key=lambda x: x["technical_area_number"]):
            cov_r = row["coverage_pct"]
            cov_c = C_GREEN if cov_r >= 75 else (C_AMBER if cov_r >= 40 else C_RED)
            rc = st.columns([0.5, 3.5, 1.2, 1.2, 1.2, 0.8, 0.7])
            rc[0].markdown(f"**TA{row['technical_area_number']}**")
            rc[1].write(row["technical_area"])
            rc[2].write(f"${row['total_cost']:,.0f}")
            rc[3].markdown(
                f"<span style='color:{C_GREEN};'>${row['total_committed']:,.0f}</span>",
                unsafe_allow_html=True,
            )
            rc[4].markdown(
                f"<span style='color:{C_RED};'>${row['total_gap']:,.0f}</span>",
                unsafe_allow_html=True,
            )
            rc[5].markdown(
                f"<span style='color:{cov_c};font-weight:700;'>{cov_r:.0f}%</span>",
                unsafe_allow_html=True,
            )
            rc[6].write(row["activity_count"])

    # ── Top funding gaps table ────────────────────────────────────────────────
    st.divider()
    st.subheader("Top 20 Largest Funding Gaps")
    gaps, _ = _evd_gaps()
    if gaps:
        g_df = pd.DataFrame(gaps[:20])[[
            "activity_number", "activity_name", "technical_area",
            "total_cost_usd", "total_committed", "funding_gap", "coverage_pct", "priority",
        ]].copy()
        g_df.columns = ["#", "Activity", "Technical Area",
                        "Govt Cost", "Committed", "Gap (USD)", "Cov %", "Priority"]
        for c in ["Govt Cost", "Committed", "Gap (USD)"]:
            g_df[c] = g_df[c].apply(lambda v: f"${v:,.0f}")
        g_df["Cov %"] = g_df["Cov %"].apply(lambda v: f"{v:.0f}%")
        st.dataframe(g_df, hide_index=True, use_container_width=True,
                     height=min(35 * len(g_df) + 38, 600))
    else:
        st.success("No funding gaps found — all activities are fully covered!")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8 — EVD FUNDING MATRIX  (read-only)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 EVD Funding Matrix":
    C_BLUE  = "#0093D5"
    C_DARK  = "#003865"
    C_GREEN = "#1E8449"
    C_AMBER = "#D97706"
    C_RED   = "#C0392B"

    @st.cache_data(ttl=60)
    def _evd_matrix():
        return api_get("evd/matrix")

    st.title("EVD Funding Matrix")
    st.caption(
        "Partner commitments per government activity — read-only. "
        "Enter contributions in the Flask portal (/evd/contributions)."
    )

    col_r2, _ = st.columns([1, 6])
    with col_r2:
        if st.button("🔄 Refresh", key="mx_refresh2"):
            st.cache_data.clear()
            st.rerun()

    matrix_data, err = _evd_matrix()
    if err or not matrix_data:
        st.error(f"API offline: {err}")
        st.info("Flask server must be running at: " + API_BASE)
        st.stop()

    activities    = matrix_data.get("activities", [])
    partner_names = matrix_data.get("partners", [])
    matrix        = matrix_data.get("matrix", {})
    row_totals    = matrix_data.get("row_totals", {})
    col_totals    = matrix_data.get("col_totals", {})
    grand_total   = matrix_data.get("grand_total", 0)

    # ── Per-partner total cards ───────────────────────────────────────────────
    if col_totals:
        sorted_partners = sorted(col_totals.items(), key=lambda x: x[1], reverse=True)
        cols_per_row = 6
        chunks = [sorted_partners[i:i+cols_per_row]
                  for i in range(0, len(sorted_partners), cols_per_row)]
        for chunk in chunks:
            pcols = st.columns(len(chunk))
            for pc, (pname, total) in zip(pcols, chunk):
                pc.metric(pname, f"${total:,.0f}" if total else "$0")
        st.caption(f"**Grand total committed: ${grand_total:,.0f}**")
        st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns(3)
    TA_OPTS = {
        1: "TA1: Leadership and Coordination",
        2: "TA2: Epidemiological Surveillance",
        3: "TA3: Laboratory and Diagnostics",
        4: "TA4: Case Management, IPC/WASH and SDB",
        5: "TA5: Risk Communication and Community Engagement",
        6: "TA6: Operational Support and Logistics",
        7: "TA7: Research and Strategic Information",
    }
    with f1:
        f_ta = st.selectbox("Filter by Technical Area",
                            ["All TAs"] + list(TA_OPTS.values()), key="mx2_ta")
    with f2:
        f_psel = st.multiselect("Show Partners", partner_names,
                                default=partner_names, key="mx2_psel")
    with f3:
        gaps_only = st.toggle("Only activities with gaps", key="mx2_gaps")

    vis_acts = activities
    if f_ta != "All TAs":
        ta_num = int(f_ta.split(":")[0].replace("TA", ""))
        vis_acts = [a for a in activities if a.get("technical_area_number") == ta_num]
    if gaps_only:
        vis_acts = [a for a in vis_acts if a.get("funding_gap", 0) > 0]
    vis_partners = [p for p in partner_names if p in f_psel]

    if not vis_acts:
        st.info("No activities match the current filters.")
        st.stop()

    # ── Build matrix dataframe ────────────────────────────────────────────────
    rows = []
    prev_ta = None
    for a in vis_acts:
        ta_name = a.get("technical_area", "")
        if ta_name != prev_ta:
            prev_ta = ta_name
            rows.append({"__type": "header",
                         "Activity": f"▌ TA{a.get('technical_area_number','')}: {ta_name}"})
        row = {
            "__type": "data",
            "Activity": f"{a.get('activity_number', '')}  {a['activity_name'][:65]}",
            "Govt Cost": a.get("total_cost_usd", 0),
        }
        a_id = str(a["id"])
        for pname in vis_partners:
            cell = matrix.get(a_id, {}).get(pname)
            row[pname] = cell["amount_committed"] if cell else 0
        row["Total Committed"] = float(row_totals.get(a_id, 0))
        row["Gap (USD)"] = max(0, a.get("total_cost_usd", 0) - row["Total Committed"])
        rows.append(row)

    df = pd.DataFrame(rows).fillna(0)
    money_cols = ["Govt Cost"] + vis_partners + ["Total Committed", "Gap (USD)"]
    money_cols = [c for c in money_cols if c in df.columns]

    display_df = df.copy()
    for col in money_cols:
        if col in df.columns:
            display_df[col] = df.apply(
                lambda r: ("" if r["__type"] == "header"
                           else (f"${r[col]:,.0f}" if r[col] > 0 else "—")),
                axis=1,
            )

    def _style_gap(val):
        if val in ("", "—"):
            return ""
        try:
            v = float(str(val).replace("$", "").replace(",", ""))
        except ValueError:
            return ""
        return (f"color:{C_GREEN};font-weight:600" if v == 0
                else f"color:{C_RED};font-weight:600")

    display_df = display_df.drop(columns=["__type"])
    styled = display_df.style
    if "Gap (USD)" in display_df.columns:
        styled = styled.map(_style_gap, subset=["Gap (USD)"])

    st.dataframe(styled, use_container_width=True, hide_index=True,
                 height=min(35 * len(display_df) + 38, 750))

    # Grand total row
    total_cost_vis = sum(a.get("total_cost_usd", 0) for a in vis_acts)
    total_com_vis  = sum(float(row_totals.get(str(a["id"]), 0)) for a in vis_acts)
    total_gap_vis  = total_cost_vis - total_com_vis

    gt_parts = [f"**GRAND TOTAL** ({len(vis_acts)} activities)", f"**${total_cost_vis:,.0f}**"]
    for pname in vis_partners:
        pt = sum(
            matrix.get(str(a["id"]), {}).get(pname, {}).get("amount_committed", 0)
            for a in vis_acts
        )
        gt_parts.append(f"**${pt:,.0f}**" if pt else "**—**")
    gt_parts += [f"**${total_com_vis:,.0f}**", f"**${total_gap_vis:,.0f}**"]

    gt_cols = st.columns([3.5, 1] + [1] * len(vis_partners) + [1.2, 1])
    for gc, gv in zip(gt_cols, gt_parts):
        gc.markdown(gv)

    # ── Excel export ──────────────────────────────────────────────────────────
    st.divider()
    if st.button("📥 Export to Excel", key="mx2_export"):
        buf = io.BytesIO()
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill, Font, Alignment
        from openpyxl.utils import get_column_letter

        wb  = Workbook()
        ws  = wb.active
        ws.title = "Partner Support Matrix"

        hdr_fill  = PatternFill("solid", fgColor="003865")
        ta_fill   = PatternFill("solid", fgColor="1A5276")
        supp_fill = PatternFill("solid", fgColor="0093D5")
        gap_red   = PatternFill("solid", fgColor="F1948A")
        gap_grn   = PatternFill("solid", fgColor="A9DFBF")
        wfont     = Font(color="FFFFFF", bold=True)

        hdr = (["Activity", "Govt Cost (USD)"]
               + vis_partners
               + ["Total Committed (USD)", "Funding Gap (USD)"])
        ws.append(hdr)
        for cell in ws[1]:
            cell.fill = hdr_fill
            cell.font = wfont
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

        prev_xl = None
        for a in vis_acts:
            ta_xl = a.get("technical_area", "")
            if ta_xl != prev_xl:
                prev_xl = ta_xl
                ws.append([f"▌ TA{a['technical_area_number']}: {ta_xl}"]
                          + [""] * (len(hdr) - 1))
                for c in ws[ws.max_row]:
                    c.fill = ta_fill
                    c.font = wfont

            a_id     = str(a["id"])
            row_data = [f"{a.get('activity_number','')} {a['activity_name']}",
                        a.get("total_cost_usd", 0)]
            for pname in vis_partners:
                cell = matrix.get(a_id, {}).get(pname)
                row_data.append(cell["amount_committed"] if cell else 0)
            t_com = float(row_totals.get(a_id, 0))
            gap_v = max(0, a.get("total_cost_usd", 0) - t_com)
            row_data += [t_com, gap_v]
            ws.append(row_data)

            last = ws.max_row
            ws.cell(last, len(hdr)).fill     = gap_grn if gap_v == 0 else gap_red
            ws.cell(last, len(hdr) - 1).fill = supp_fill

        ws.column_dimensions["A"].width = 65
        for i in range(2, len(hdr) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 18

        wb.save(buf)
        buf.seek(0)
        st.download_button(
            "⬇ Download Partner Support Matrix",
            buf,
            file_name=f"EVD_Funding_Matrix_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.success("Excel export ready.")

