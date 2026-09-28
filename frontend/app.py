import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="MetricFlow", page_icon="◈", layout="wide")

st.markdown(
    """
    <style>
    :root { --mf-ink: #172033; --mf-muted: #667085; --mf-blue: #2457d6; --mf-line: #e6eaf0; --mf-surface: #ffffff; }
    .stApp { background: #f7f8fb; color: var(--mf-ink); }
    .block-container { max-width: 1440px; padding-top: 2.2rem; padding-bottom: 3rem; animation: mf-fade-in .4s ease both; }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--mf-line); }
    [data-testid="stSidebar"] .block-container { padding: 2rem 1.1rem; }
    [data-testid="stMetric"] { background: var(--mf-surface); border: 1px solid var(--mf-line); border-radius: 12px; padding: 1rem 1.15rem; box-shadow: 0 2px 8px rgba(23,32,51,.03); }
    [data-testid="stMetricLabel"] { color: var(--mf-muted); font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--mf-ink); font-size: 1.65rem; }
    .mf-kicker { color: var(--mf-blue); font-size: .75rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; margin-bottom: .35rem; }
    .mf-title { color: var(--mf-ink); font-size: 2.15rem; font-weight: 750; letter-spacing: -.03em; margin: 0; animation: mf-fade-up .55s cubic-bezier(.2,.8,.2,1) both; }
    .mf-subtitle { color: var(--mf-muted); font-size: 1rem; margin: .35rem 0 1.6rem; animation: mf-fade-up .55s .08s cubic-bezier(.2,.8,.2,1) both; }
    .mf-card { background: var(--mf-surface); border: 1px solid var(--mf-line); border-radius: 12px; padding: 1.25rem; animation: mf-fade-up .5s .12s cubic-bezier(.2,.8,.2,1) both; transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease; }
    .mf-card:hover { border-color: #c9d5ef; box-shadow: 0 10px 24px rgba(23,32,51,.07); transform: translateY(-2px); }
    .mf-card h3 { color: var(--mf-ink); font-size: 1rem; margin: 0 0 .35rem; }
    .mf-card p { color: var(--mf-muted); font-size: .9rem; margin: 0; }
    .mf-step { color: var(--mf-muted); font-size: .82rem; text-align: center; animation: mf-fade-up .5s cubic-bezier(.2,.8,.2,1) both; }
    .mf-step span { display: inline-flex; align-items: center; justify-content: center; width: 1.55rem; height: 1.55rem; border: 1px solid #c9d5ef; border-radius: 50%; color: var(--mf-blue); font-weight: 800; background: #f5f8ff; }
    .mf-step strong { display: block; color: var(--mf-ink); font-size: .9rem; margin-top: .25rem; }
    div.stButton > button, div.stDownloadButton > button { border-radius: 8px; font-weight: 650; transition: transform .16s ease, box-shadow .16s ease, background .16s ease; }
    div.stButton > button:hover, div.stDownloadButton > button:hover { box-shadow: 0 6px 16px rgba(36,87,214,.16); transform: translateY(-1px); }
    div.stButton > button[kind="primary"] { background: var(--mf-blue); border-color: var(--mf-blue); }
    [data-testid="stMetric"] { animation: mf-fade-up .5s cubic-bezier(.2,.8,.2,1) both; transition: transform .18s ease, box-shadow .18s ease; }
    [data-testid="stMetric"]:hover { transform: translateY(-3px); box-shadow: 0 10px 22px rgba(23,32,51,.08); }
    [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { animation: mf-fade-in .7s .1s ease both; }
    @keyframes mf-fade-up { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes mf-fade-in { from { opacity: 0; } to { opacity: 1; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def api(method: str, path: str, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    access_token = st.session_state.get("access_token")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=30, headers=headers, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        detail = getattr(error.response, "text", "") if getattr(error, "response", None) else ""
        if getattr(error, "response", None) is not None and error.response.status_code == 401:
            st.session_state.authenticated = False
            st.session_state.pop("access_token", None)
        st.error(f"Could not reach MetricFlow API. {detail or error}")
        return None


def money(value: float) -> str:
    return f"₹{value:,.2f}"


def page_header(kicker: str, title: str, subtitle: str):
    st.markdown(f'<div class="mf-kicker">{kicker}</div><h1 class="mf-title">{title}</h1><p class="mf-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def date_params():
    today = date.today()
    preset = st.sidebar.selectbox("Date range", ["Last 7 days", "Last 30 days", "Last 90 days", "Custom range"])
    if preset == "Custom range":
        selection = st.sidebar.date_input("Reporting period", (today - timedelta(days=29), today), max_value=today)
        if not isinstance(selection, tuple) or len(selection) != 2:
            st.sidebar.info("Choose both a start and end date.")
            return {}
        start, end = selection
    else:
        days = {"Last 7 days": 6, "Last 30 days": 29, "Last 90 days": 89}[preset]
        start, end = today - timedelta(days=days), today
    st.sidebar.caption(f"{start.strftime('%d %b %Y')} – {end.strftime('%d %b %Y')}")
    return {"start": start.isoformat(), "end": end.isoformat()}


def login_page():
    st.markdown('<div class="mf-kicker">Sales operations workspace</div>', unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.05, 1])
    with center:
        st.markdown('<h1 class="mf-title">Welcome to MetricFlow</h1><p class="mf-subtitle">A clear view of your sales, every week.</p>', unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Work email", value="demo@metricflow.app", placeholder="you@company.com")
            password = st.text_input("Password", value="demo123", type="password")
            submitted = st.form_submit_button("Sign in to workspace", type="primary", use_container_width=True)
        if submitted:
            response = api("POST", "/auth/login", json={"email": email, "password": password})
            if response:
                st.session_state.access_token = response.json()["access_token"]
                st.session_state.authenticated = True
                st.session_state.user_email = response.json()["user"]["email"]
                st.rerun()
        st.info("Demo workspace: demo@metricflow.app · demo123")


def dashboard_page():
    page_header("Overview", "Sales dashboard", "Your e-commerce performance at a glance.")
    params = date_params()
    if not params:
        return
    response = api("GET", "/dashboard/summary", params=params)
    if not response:
        return
    summary = response.json()
    cards = st.columns(4)
    cards[0].metric("Revenue", money(summary["revenue"]), f"{summary['week_over_week_change']:+.1f}% vs previous period")
    cards[1].metric("Orders", f"{summary['orders']:,}", "All valid orders")
    cards[2].metric("Average order value", money(summary["average_order_value"]), "Revenue ÷ orders")
    cards[3].metric("Refund rate", f"{summary['refund_rate']:.1f}%", f"{summary['refunded_orders']} refunded")

    trend_response = api("GET", "/dashboard/trends", params=params)
    status_response = api("GET", "/dashboard/status-breakdown", params=params)
    product_response = api("GET", "/dashboard/top-products", params=params)
    first, second = st.columns([1.55, 1])
    with first:
        st.subheader("Revenue trend")
        trend = pd.DataFrame(trend_response.json() if trend_response else [])
        if trend.empty:
            st.info("Import orders to see your revenue trend.")
        else:
            chart = px.line(trend, x="date", y="revenue", markers=True, labels={"date": "Date", "revenue": "Revenue"})
            chart.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=12, b=0), hovermode="x unified")
            st.plotly_chart(chart, use_container_width=True)
    with second:
        st.subheader("Order status")
        statuses = pd.DataFrame(status_response.json() if status_response else [])
        if statuses.empty:
            st.info("No orders in this period.")
        else:
            chart = px.pie(statuses, names="status", values="count", hole=.55)
            chart.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=12, b=0), legend_title_text="Status")
            st.plotly_chart(chart, use_container_width=True)
    st.subheader("Top products")
    products = pd.DataFrame(product_response.json() if product_response else [])
    if products.empty:
        st.info("Import orders to see your best-selling products.")
    else:
        st.dataframe(products, use_container_width=True, hide_index=True, column_config={"revenue": st.column_config.NumberColumn("Revenue", format="₹%.2f")})


def upload_page():
    page_header("Data workspace", "Import sales data", "Turn your export into a clean, decision-ready dataset in three steps.")
    steps = st.columns(3)
    for index, (column, number, label, detail) in enumerate(zip(steps, ("1", "2", "3"), ("Upload", "Review", "Import"), ("Choose a CSV or Excel file", "Check validation results", "Refresh your dashboard"))):
        with column:
            st.markdown(f'<div class="mf-step" style="animation-delay:{index * 90}ms"><span>{number}</span><strong>{label}</strong>{detail}</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("#### Choose your sales export")
    st.caption("Required columns: order_id, order_date, product_name, quantity, unit_price, status")
    uploaded_file = st.file_uploader("Drop your sales export here", type=["csv", "xlsx", "xls"])
    if not uploaded_file:
        st.info("No file selected yet. CSV, XLS, and XLSX files up to 10 MB are supported.")
        return
    if st.session_state.get("uploaded_filename") != uploaded_file.name:
        st.session_state.pop("validation", None)
        st.session_state.uploaded_filename = uploaded_file.name
    st.success(f"Ready to validate: {uploaded_file.name}")
    try:
        preview = pd.read_csv(uploaded_file) if uploaded_file.name.lower().endswith(".csv") else pd.read_excel(uploaded_file)
        st.caption(f"Previewing the first 10 rows · {len(preview):,} total rows")
        with st.expander("Preview rows", expanded=True):
            st.dataframe(preview.head(10), use_container_width=True, hide_index=True)
        uploaded_file.seek(0)
    except Exception as error:
        st.error(f"Could not preview this file: {error}")
        return
    if st.button("Validate data", type="primary"):
        with st.spinner("Checking columns, types, duplicates, and statuses…"):
            response = api("POST", "/uploads", files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)})
            if response:
                st.session_state.upload_id = response.json()["id"]
                validation = api("POST", f"/uploads/{st.session_state.upload_id}/validate")
                if validation:
                    st.session_state.validation = validation.json()
    validation = st.session_state.get("validation")
    if validation:
        st.divider()
        st.markdown("#### Validation results")
        result_cards = st.columns(2)
        result_cards[0].metric("Valid rows", f"{validation['valid_rows']:,}", f"of {validation['row_count']:,} rows")
        result_cards[1].metric("Status", "Ready to import" if validation["valid"] else "Needs attention")
        if validation["errors"]:
            with st.expander(f"Review {len(validation['errors'])} issue(s)", expanded=True):
                for error in validation["errors"]:
                    st.error(error)
        for warning in validation["warnings"]:
            st.warning(warning)
        st.caption(f"{validation['valid_rows']} of {validation['row_count']} records are valid.")
        if validation["valid"]:
            if st.button("Import data and refresh dashboard", type="primary"):
                with st.spinner("Importing clean records…"):
                    response = api("POST", f"/uploads/{st.session_state.upload_id}/import")
                if response:
                    st.success(f"Imported {response.json()['imported_rows']} new orders. Your dashboard is refreshed.")


def reports_page():
    page_header("Reporting", "Weekly reports", "Create a ready-to-share Excel report for any date range.")
    st.markdown('<div class="mf-card"><h3>What is included</h3><p>Summary KPIs · daily revenue trend · top products by revenue</p></div>', unsafe_allow_html=True)
    st.write("")
    start, end = st.date_input("Report period", (date.today() - timedelta(days=6), date.today()), max_value=date.today())
    if st.button("Generate Excel report", type="primary"):
        with st.spinner("Preparing your report…"):
            response = api("POST", "/reports/generate", params={"start": start.isoformat(), "end": end.isoformat()})
        if response:
            report = response.json()
            st.session_state.report = report
            st.success("Your report is ready.")
    report = st.session_state.get("report")
    if report:
        st.success(f"Report ready · {report['filename']}")
        download = api("GET", f"/reports/{report['id']}")
        if download:
            st.download_button("Download Excel report", download.content, report["filename"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def automation_page():
    page_header("Workflow", "Automation", "Set a recurring reporting rhythm so your team always knows when to check in.")
    st.markdown('<div class="mf-card"><h3>How it works</h3><p>MetricFlow saves your schedule and prepares the report workflow. Email delivery can be connected when you are ready to turn it on.</p></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("#### New schedule")
    with st.form("schedule"):
        report_type = st.selectbox("Report type", ["weekly"])
        frequency = st.selectbox("Frequency", ["weekly", "monthly"])
        delivery_time = st.time_input("Delivery time").strftime("%H:%M")
        submitted = st.form_submit_button("Save schedule", type="primary")
    if submitted:
        response = api("POST", "/schedules", json={"report_type": report_type, "frequency": frequency, "delivery_time": delivery_time})
        if response:
            st.success("Schedule saved. Your recurring workflow is ready.")
    response = api("GET", "/schedules")
    if response and response.json():
        st.subheader("Saved schedules")
        st.dataframe(pd.DataFrame(response.json()), use_container_width=True, hide_index=True)
    elif response:
        st.info("No schedules yet. Add your first weekly or monthly report above.")


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_page()
else:
    with st.sidebar:
        st.markdown('<div class="mf-title" style="font-size:1.3rem;">◈ MetricFlow</div><p style="color:#667085; font-size:.8rem;">Sales operations workspace</p>', unsafe_allow_html=True)
        st.divider()
        page = st.radio("Workspace", ["▦  Dashboard", "⇧  Data Upload", "▤  Reports", "◷  Automation"], label_visibility="visible")
        page = page.split("  ", 1)[1]
        st.divider()
        st.caption("SIGNED IN AS")
        st.markdown(f"**{st.session_state.user_email}**")
        if st.button("Sign out"):
            st.session_state.authenticated = False
            st.session_state.pop("access_token", None)
            st.rerun()
    {"Dashboard": dashboard_page, "Data Upload": upload_page, "Reports": reports_page, "Automation": automation_page}[page]()
