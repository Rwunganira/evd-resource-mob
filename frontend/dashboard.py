"""
WHO EVD Preparedness — Activity Implementation & Budget Dashboard

Read-only analytics over the EVD Activity Register. All data entry is done in
the Flask portal (/evd/activities, /evd/contributions).

Run:  streamlit run dashboard.py
Env:  FLASK_URL  (default http://localhost:5000)
"""
import io
import os
from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

FLASK_URL = os.getenv("FLASK_URL", "http://localhost:5000").rstrip("/")
API_BASE = f"{FLASK_URL}/api"

BLUE, DARK = "#0093D5", "#003865"
GREEN, AMBER, RED = "#1E8449", "#D97706", "#C0392B"
INFO, GREY = "#5DADE2", "#BDC3C7"

IMPL_STATUSES = ["On track", "Delayed", "At risk", "Complete"]
IMPL_COLOR = {"On track": GREEN, "Delayed": AMBER, "At risk": RED,
              "Complete": "#7F8C8D", "No update": GREY}

TA_NAME = {
    1: "Leadership & Coordination",
    2: "Epidemiological Surveillance",
    3: "Laboratory & Diagnostics",
    4: "Case Management, IPC/WASH & SDB",
    5: "Risk Communication & Community Engagement",
    6: "Operational Support & Logistics",
    7: "Research & Strategic Information",
}

st.set_page_config(page_title="EVD Activity & Budget", page_icon="🏥",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
  [data-testid="stSidebar"] {{ background-color: {DARK}; }}
  [data-testid="stSidebar"] * {{ color: #fff !important; }}
  [data-testid="stMetricValue"] {{ font-size: 1.5rem; }}
</style>
""", unsafe_allow_html=True)


# ── API ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=45)
def api_get(endpoint: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}/{endpoint.lstrip('/')}", params=params, timeout=8)
        r.raise_for_status()
        return r.json().get("data"), None
    except requests.exceptions.ConnectionError:
        return None, "API unavailable — the Flask portal is not reachable."
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def guard(err):
    if err:
        st.error(err)
        st.caption(f"Expected API at: {API_BASE}")
        st.stop()


def usd(v) -> str:
    return f"${(v or 0):,.0f}"


def compact(v) -> str:
    v = v or 0
    if abs(v) >= 1e6:
        return f"${v / 1e6:.2f}M"
    if abs(v) >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:8px 0;'>"
        "<div style='font-size:1.8rem;'>🏥</div>"
        "<div style='font-weight:800;'>WHO EOC</div>"
        "<div style='font-size:.72rem;color:#a0c4e8;'>EVD Preparedness</div></div>"
        "<hr style='border-color:#1a5276;'>", unsafe_allow_html=True)
    page = st.radio("Navigation", [
        "EVD Coverage Analysis",
        "EVD Funding Matrix",
        "Overview",
        "Implementation Status",
    ], label_visibility="collapsed")
    st.markdown("<hr style='border-color:#1a5276;'>", unsafe_allow_html=True)
    if st.button("🔄 Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Loaded {datetime.now():%H:%M:%S} · cache 45s")


def load_activities():
    data, err = api_get("evd/activities")
    guard(err)
    flat = (data or {}).get("flat", [])
    return pd.DataFrame(flat), flat


# ═════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ═════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("EVD Activity Register — Overview")
    summary, err = api_get("evd/summary")
    guard(err)
    df, flat = load_activities()

    budget    = summary.get("total_cost_usd", 0)
    committed = summary.get("total_committed_usd", 0)
    availed   = summary.get("total_disbursed_usd", 0)
    executed  = summary.get("total_executed_usd", 0)
    comm_gap  = summary.get("total_funding_gap", 0)
    avail_gap = summary.get("disbursement_gap", 0)
    cov       = summary.get("coverage_pct", 0)
    exe       = summary.get("execution_pct", 0)

    a, b, c, d, e = st.columns(5)
    a.metric("Activities", summary.get("total_activities", 0))
    b.metric("Govt Budget", compact(budget))
    c.metric("Committed", compact(committed), delta=f"{cov:.0f}% of budget", delta_color="off")
    d.metric("Budget Availed", compact(availed))
    e.metric("Budget Executed", compact(executed),
             delta=f"{exe:.0f}% of availed", delta_color="off")

    a, b, c, d = st.columns(4)
    a.metric("Commitment Gap", compact(comm_gap), help="Govt Budget − Committed")
    b.metric("Availed Budget Gap", compact(avail_gap), help="Govt Budget − Availed")
    c.metric("Coverage %", f"{cov:.1f}%", help="Committed ÷ Govt Budget")
    d.metric("Execution %", f"{exe:.1f}%", help="Executed ÷ Availed")

    st.divider()
    left, right = st.columns(2)

    # Implementation status of activities (from latest comment)
    with left:
        st.subheader("Implementation status")
        if not df.empty:
            s = (df["latest_impl_status"].fillna("No update")
                 .value_counts()
                 .reindex(IMPL_STATUSES + ["No update"], fill_value=0))
            fig = go.Figure(go.Pie(
                labels=s.index, values=s.values, hole=.55,
                marker=dict(colors=[IMPL_COLOR[k] for k in s.index]),
                sort=False,
            ))
            fig.update_layout(height=280, margin=dict(t=10, b=0, l=0, r=0),
                              legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig, width="stretch")
            logged = int((df["latest_impl_status"].notna()).sum())
            st.caption(f"{logged} of {len(df)} activities have a status update logged.")

    # Sub-activity completion
    with right:
        st.subheader("Sub-activity completion")
        subs = pd.json_normalize(df["subtask_summary"]) if not df.empty else pd.DataFrame()
        if not subs.empty and subs["total"].sum():
            done, total = int(subs["done"].sum()), int(subs["total"].sum())
            with_subs = int((subs["total"] > 0).sum())
            st.metric("Sub-activities completed", f"{done} / {total}",
                      delta=f"{(done / total * 100):.0f}%", delta_color="off")
            st.progress(min(done / total, 1.0))
            st.caption(f"{with_subs} of {len(df)} activities have sub-activities defined.")
            # activity workflow status
            ws = df["status"].value_counts()
            fig = go.Figure(go.Bar(x=ws.values, y=ws.index, orientation="h",
                                   marker_color=BLUE))
            fig.update_layout(height=170, margin=dict(t=6, b=0), xaxis_title="Activities")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No sub-activities defined yet.")

    st.divider()
    st.subheader("By Technical Area")
    by_ta = summary.get("by_technical_area", [])
    if by_ta:
        t = pd.DataFrame(by_ta).sort_values("technical_area_number")
        t["Availed Gap"] = t["disbursement_gap"]
        show = t[["technical_area_number", "technical_area", "total_cost",
                  "total_committed", "total_disbursed", "total_gap",
                  "Availed Gap", "coverage_pct", "activity_count"]].copy()
        show.columns = ["TA", "Technical Area", "Govt Cost", "Committed", "Availed",
                        "Commitment Gap", "Availed Gap", "Cov %", "Acts"]
        for col in ["Govt Cost", "Committed", "Availed", "Commitment Gap", "Availed Gap"]:
            show[col] = show[col].map(usd)
        show["Cov %"] = show["Cov %"].map(lambda v: f"{v:.0f}%")
        st.dataframe(show, hide_index=True, width="stretch")


# ═════════════════════════════════════════════════════════════════════════════
# BUDGET ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "EVD Coverage Analysis":
    st.title("EVD Coverage Analysis")
    summary, err = api_get("evd/summary")
    guard(err)
    df, flat = load_activities()

    budget    = summary.get("total_cost_usd", 0)
    committed = summary.get("total_committed_usd", 0)
    availed   = summary.get("total_disbursed_usd", 0)
    executed  = summary.get("total_executed_usd", 0)

    st.subheader("Resource mobilization funnel")
    stages = ["Govt Budget", "Committed", "Availed", "Executed"]
    vals = [budget, committed, availed, executed]
    fig = go.Figure(go.Funnel(
        y=stages, x=vals,
        textinfo="value+percent initial",
        marker=dict(color=[DARK, BLUE, INFO, GREEN]),
    ))
    fig.update_layout(height=300, margin=dict(t=10, b=0))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"Of the {usd(budget)} government plan, {usd(committed)} is committed by partners, "
        f"{usd(availed)} has been released to government, and {usd(executed)} spent."
    )

    st.divider()
    by_ta = summary.get("by_technical_area", [])
    if by_ta:
        t = pd.DataFrame(by_ta).sort_values("technical_area_number")
        t["ta"] = t["technical_area_number"].map(lambda n: f"TA{n}")

        metric = st.radio("View", ["Commitment (Committed vs Gap)",
                                   "Availed budget (Availed vs Gap)"],
                          horizontal=True)
        if metric.startswith("Commitment"):
            got, gap, got_c = t["total_committed"], t["total_gap"], BLUE
        else:
            got, gap, got_c = t["total_disbursed"], t["disbursement_gap"], INFO

        fig = go.Figure()
        fig.add_bar(name="Secured", x=t["ta"], y=got, marker_color=got_c)
        fig.add_bar(name="Gap", x=t["ta"], y=gap, marker_color="#F1948A")
        fig.update_layout(barmode="stack", height=340, yaxis_title="USD",
                          margin=dict(t=10, b=0),
                          legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig, width="stretch")

    st.divider()
    if not df.empty:
        st.subheader("Largest gaps")
        g = df.copy()
        g["ta"] = g["technical_area_number"].map(lambda n: f"TA{n}")
        c1, c2 = st.columns(2)
        with c1:
            st.caption("**Commitment gap** — Govt Cost − Committed")
            top = g[g["funding_gap"] > 0].nlargest(12, "funding_gap")
            tbl = top[["activity_number", "activity_name", "ta", "total_cost_usd",
                       "total_committed", "funding_gap", "coverage_pct"]].copy()
            tbl.columns = ["#", "Activity", "TA", "Cost", "Committed", "Gap", "Cov %"]
            for col in ["Cost", "Committed", "Gap"]:
                tbl[col] = tbl[col].map(usd)
            tbl["Cov %"] = tbl["Cov %"].map(lambda v: f"{v:.0f}%")
            st.dataframe(tbl, hide_index=True, width="stretch", height=430)
        with c2:
            st.caption("**Availed budget gap** — Govt Cost − Availed")
            top = g[g["disbursement_gap"] > 0].nlargest(12, "disbursement_gap")
            tbl = top[["activity_number", "activity_name", "ta", "total_cost_usd",
                       "total_disbursed", "disbursement_gap"]].copy()
            tbl.columns = ["#", "Activity", "TA", "Cost", "Availed", "Gap"]
            for col in ["Cost", "Availed", "Gap"]:
                tbl[col] = tbl[col].map(usd)
            st.dataframe(tbl, hide_index=True, width="stretch", height=430)

        # overspend flag
        over = df[(df["total_disbursed"] > 0) & (df["execution_pct"] > 100)]
        if not over.empty:
            st.warning(f"{len(over)} activities have spent more than has been availed "
                       f"(Execution % > 100).")
            o = over[["activity_number", "activity_name", "total_disbursed",
                      "budget_executed_usd", "execution_pct"]].copy()
            o.columns = ["#", "Activity", "Availed", "Executed", "Exec %"]
            for col in ["Availed", "Executed"]:
                o[col] = o[col].map(usd)
            o["Exec %"] = o["Exec %"].map(lambda v: f"{v:.0f}%")
            st.dataframe(o, hide_index=True, width="stretch")


# ═════════════════════════════════════════════════════════════════════════════
# IMPLEMENTATION STATUS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Implementation Status":
    st.title("Implementation Status")
    df, flat = load_activities()
    if df.empty:
        st.info("No activities found.")
        st.stop()

    df["ta"] = df["technical_area_number"].map(lambda n: f"TA{n}")
    df["impl"] = df["latest_impl_status"].fillna("No update")
    sub = pd.json_normalize(df["subtask_summary"])
    df["sub_done"], df["sub_total"], df["sub_pct"] = sub["done"], sub["total"], sub["pct"]

    f1, f2, f3 = st.columns(3)
    ta_opt = f1.selectbox("Technical Area", ["All"] + [f"TA{n}: {v}" for n, v in TA_NAME.items()])
    impl_opt = f2.selectbox("Implementation status", ["All", "No update"] + IMPL_STATUSES)
    wf_opt = f3.selectbox("Workflow status", ["All"] + sorted(df["status"].unique()))

    view = df
    if ta_opt != "All":
        view = view[view["technical_area_number"] == int(ta_opt.split(":")[0][2:])]
    if impl_opt != "All":
        view = view[view["impl"] == impl_opt]
    if wf_opt != "All":
        view = view[view["status"] == wf_opt]

    # charts
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Implementation status by TA")
        piv = (df.groupby(["ta", "impl"]).size().unstack(fill_value=0)
               .reindex(columns=IMPL_STATUSES + ["No update"], fill_value=0))
        fig = go.Figure()
        for s in IMPL_STATUSES + ["No update"]:
            fig.add_bar(name=s, x=piv.index, y=piv[s], marker_color=IMPL_COLOR[s])
        fig.update_layout(barmode="stack", height=280, margin=dict(t=10, b=0),
                          legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Sub-activity completion")
        tot = int(df["sub_total"].sum())
        done = int(df["sub_done"].sum())
        if tot:
            fig = go.Figure(go.Bar(
                x=[done, tot - done], y=["Sub-activities", "Sub-activities"],
                orientation="h", marker_color=[GREEN, GREY],
                base=[0, done], showlegend=False,
            ))
            fig.update_layout(barmode="stack", height=120, margin=dict(t=10, b=0),
                              xaxis_title="")
            st.plotly_chart(fig, width="stretch")
            st.metric("Completed", f"{done} / {tot}",
                      delta=f"{done / tot * 100:.0f}%", delta_color="off")
        else:
            st.info("No sub-activities defined yet.")
        st.metric("Activities with a status update",
                  f"{int(df['latest_impl_status'].notna().sum())} / {len(df)}")

    st.divider()
    st.subheader(f"Activities ({len(view)})")
    tbl = view[["activity_number", "activity_name", "ta", "status", "impl",
                "sub_done", "sub_total", "comment_count",
                "coverage_pct", "execution_pct"]].copy()
    tbl["Sub-activities"] = tbl.apply(
        lambda r: f"{r['sub_done']}/{r['sub_total']}" if r["sub_total"] else "—", axis=1)
    tbl = tbl.drop(columns=["sub_done", "sub_total"])
    tbl.columns = ["#", "Activity", "TA", "Workflow", "Impl. status",
                   "Comments", "Cov %", "Exec %", "Sub-activities"]
    tbl = tbl[["#", "Activity", "TA", "Workflow", "Impl. status",
               "Sub-activities", "Comments", "Cov %", "Exec %"]]
    tbl["Cov %"] = tbl["Cov %"].map(lambda v: f"{v:.0f}%")
    tbl["Exec %"] = tbl["Exec %"].map(lambda v: f"{v:.0f}%" if v else "—")
    st.dataframe(tbl, hide_index=True, width="stretch",
                 height=min(35 * len(tbl) + 40, 480))

    st.divider()
    st.subheader("Activity detail")
    labels = {f"{a['activity_number']}  {a['activity_name']}": a["id"] for a in flat}
    pick = st.selectbox("Select an activity", ["— select —"] + list(labels))
    if pick != "— select —":
        d, e = api_get(f"evd/activities/{labels[pick]}")
        if e:
            st.error(e)
        elif d:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Govt Cost", usd(d["total_cost_usd"]))
            m2.metric("Committed", usd(d["total_committed"]))
            m3.metric("Availed", usd(d["total_disbursed"]))
            m4.metric("Executed", usd(d["budget_executed_usd"]))

            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown("**Sub-activities**")
                subs = d.get("sub_activities", [])
                if subs:
                    sdf = pd.DataFrame(subs)[["name", "status", "notes"]]
                    sdf.columns = ["Sub-activity", "Status", "Notes"]
                    st.dataframe(sdf, hide_index=True, width="stretch")
                else:
                    st.caption("None defined.")
            with cc2:
                st.markdown("**Implementation status log**")
                comments = d.get("comments", [])
                if comments:
                    for c in comments:
                        colr = IMPL_COLOR.get(c["impl_status"], GREY)
                        when = (c["created_at"] or "")[:16].replace("T", " ")
                        st.markdown(
                            f"<div style='border-left:3px solid {colr};padding:2px 10px;"
                            f"margin-bottom:8px;'>"
                            f"<span style='color:{colr};font-weight:700;'>{c['impl_status']}</span>"
                            f" &nbsp;<span style='color:#888;font-size:.85em;'>"
                            f"{c.get('author_name') or 'Unknown'} · {when}"
                            f"{' (edited)' if c.get('edited') else ''}</span><br>"
                            f"{c['body']}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No updates logged.")


# ═════════════════════════════════════════════════════════════════════════════
# PARTNER FUNDING MATRIX
# ═════════════════════════════════════════════════════════════════════════════
elif page == "EVD Funding Matrix":
    st.title("EVD Funding Matrix")
    st.caption("Partner amounts per government activity. Enter these in the Flask portal "
               "(/evd/contributions).")

    data, err = api_get("evd/matrix")
    guard(err)
    activities = data.get("activities", [])
    partners = data.get("partners", [])
    matrix = data.get("matrix", {})
    row_totals = data.get("row_totals", {})

    basis = st.radio("Amount", ["Committed", "Availed (disbursed)"], horizontal=True)
    key = "amount_committed" if basis == "Committed" else "amount_disbursed"

    f1, f2, f3 = st.columns(3)
    ta_opt = f1.selectbox("Technical Area",
                          ["All"] + [f"TA{n}: {v}" for n, v in TA_NAME.items()])
    psel = f2.multiselect("Partners", partners, default=partners)
    gaps_only = f3.toggle("Only activities with a commitment gap")

    acts = activities
    if ta_opt != "All":
        n = int(ta_opt.split(":")[0][2:])
        acts = [a for a in acts if a.get("technical_area_number") == n]
    if gaps_only:
        acts = [a for a in acts if a.get("funding_gap", 0) > 0]
    vis_p = [p for p in partners if p in psel]
    if not acts:
        st.info("No activities match the filters.")
        st.stop()

    rows = []
    prev = None
    for a in acts:
        ta = a.get("technical_area", "")
        if ta != prev:
            prev = ta
            rows.append({"Activity": f"▌ TA{a.get('technical_area_number','')}: {ta}",
                         "_hdr": True})
        aid = str(a["id"])
        r = {"Activity": f"{a.get('activity_number','')}  {a['activity_name'][:60]}",
             "Govt Cost": a.get("total_cost_usd", 0), "_hdr": False}
        secured = 0.0
        for p in vis_p:
            cell = matrix.get(aid, {}).get(p)
            v = (cell or {}).get(key, 0) if cell else 0
            r[p] = v
            secured += v
        r["Secured"] = secured
        r["Gap"] = max(0, a.get("total_cost_usd", 0) - secured)
        rows.append(r)

    df = pd.DataFrame(rows).fillna(0)
    money_cols = ["Govt Cost"] + vis_p + ["Secured", "Gap"]
    disp = df.copy()
    for c in money_cols:
        disp[c] = df.apply(
            lambda x: "" if x["_hdr"] else (f"${x[c]:,.0f}" if x[c] > 0 else "—"), axis=1)
    disp = disp.drop(columns=["_hdr"])
    st.dataframe(disp, hide_index=True, width="stretch",
                 height=min(34 * len(disp) + 40, 700))

    tot_cost = sum(a.get("total_cost_usd", 0) for a in acts)
    tot_sec = sum(
        (matrix.get(str(a["id"]), {}).get(p, {}) or {}).get(key, 0)
        for a in acts for p in vis_p)
    k1, k2, k3 = st.columns(3)
    k1.metric("Govt Cost (filtered)", usd(tot_cost))
    k2.metric(f"{basis} (filtered)", usd(tot_sec))
    k3.metric("Gap (filtered)", usd(max(0, tot_cost - tot_sec)))

    if st.button("📥 Export matrix to Excel"):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            disp.to_excel(w, index=False, sheet_name="Funding Matrix")
        buf.seek(0)
        st.download_button("⬇ Download", buf,
                           file_name=f"EVD_Funding_Matrix_{date.today()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument."
                                "spreadsheetml.sheet")
