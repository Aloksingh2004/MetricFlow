import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="MetricFlow", page_icon="◈", layout="wide")


def api(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=30, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        detail = getattr(error.response, "text", "") if getattr(error, "response", None) else ""
        st.error(f"Could not reach MetricFlow API. {detail or error}")
        return None


def money(value: float) -> str:
    return f"₹{value:,.2f}"


def date_params():
    selection = st.sidebar.date_input(
        "Reporting period",
        (date.today() - timedelta(days=29), date.today()),
        max_value=date.today(),
    )
    if len(selection) != 2:
        st.sidebar.info("Choose a start and end date.")
        return {}
    return {"start": selection[0].isoformat(), "end": selection[1].isoformat()}


def login_page():
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        st.title("MetricFlow")
        st.caption("Sales reporting, without spreadsheet cleanup.")
        with st.form("login"):
            email = st.text_input("Email", value="demo@metricflow.app")
            password = st.text_input("Password", value="demo123", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            response = api("POST", "/auth/login", json={"email": email, "password": password})
            if response:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
        st.caption("Demo: `demo@metricflow.app` / `demo123`")


def dashboard_page():
    st.title("Dashboard")
    st.caption("Your e-commerce performance at a glance.")
    params = date_params()
    if not params:
        return
    response = api("GET", "/dashboard/summary", params=params)
    if not response:
        return
    summary = response.json()
    cards = st.columns(4)
    cards[0].metric("Revenue", money(summary["revenue"]), f"{summary['week_over_week_change']:+.1f}% vs previous period")
    cards[1].metric("Orders", f"{summary['orders']:,}")
    cards[2].metric("Average order value", money(summary["average_order_value"]))
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
            st.plotly_chart(px.line(trend, x="date", y="revenue", markers=True), use_container_width=True)
    with second:
        st.subheader("Order status")
        statuses = pd.DataFrame(status_response.json() if status_response else [])
        if statuses.empty:
            st.info("No orders in this period.")
        else:
            st.plotly_chart(px.pie(statuses, names="status", values="count", hole=.55), use_container_width=True)
    st.subheader("Top products")
    products = pd.DataFrame(product_response.json() if product_response else [])
    if products.empty:
        st.info("Import orders to see your best-selling products.")
    else:
        st.dataframe(products, use_container_width=True, hide_index=True, column_config={"revenue": st.column_config.NumberColumn("Revenue", format="₹%.2f")})


def upload_page():
    st.title("Import sales data")
    st.caption("Upload a CSV or Excel export. Required fields: order_id, order_date, product_name, quantity, unit_price, status.")
    uploaded_file = st.file_uploader("Drop your sales export here", type=["csv", "xlsx", "xls"])
    if not uploaded_file:
        return
    st.success(f"Ready to validate: {uploaded_file.name}")
    try:
        preview = pd.read_csv(uploaded_file) if uploaded_file.name.lower().endswith(".csv") else pd.read_excel(uploaded_file)
        st.dataframe(preview.head(10), use_container_width=True, hide_index=True)
        uploaded_file.seek(0)
    except Exception as error:
        st.error(f"Could not preview this file: {error}")
        return
    if st.button("Validate data", type="primary"):
        response = api("POST", "/uploads", files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)})
        if response:
            st.session_state.upload_id = response.json()["id"]
            validation = api("POST", f"/uploads/{st.session_state.upload_id}/validate")
            if validation:
                st.session_state.validation = validation.json()
    validation = st.session_state.get("validation")
    if validation:
        if validation["errors"]:
            for error in validation["errors"]:
                st.error(error)
        for warning in validation["warnings"]:
            st.warning(warning)
        st.caption(f"{validation['valid_rows']} of {validation['row_count']} records are valid.")
        if validation["valid"] and st.button("Import data"):
            response = api("POST", f"/uploads/{st.session_state.upload_id}/import")
            if response:
                st.success(f"Imported {response.json()['imported_rows']} new orders. Your dashboard is refreshed.")


def reports_page():
    st.title("Weekly reports")
    st.caption("Generate a ready-to-share Excel report with KPIs, revenue trend, and top products.")
    start, end = st.date_input("Report period", (date.today() - timedelta(days=6), date.today()), max_value=date.today())
    if st.button("Generate weekly report", type="primary"):
        response = api("POST", "/reports/generate", params={"start": start.isoformat(), "end": end.isoformat()})
        if response:
            report = response.json()
            st.session_state.report = report
            st.success("Your report is ready.")
    report = st.session_state.get("report")
    if report:
        download = api("GET", f"/reports/{report['id']}")
        if download:
            st.download_button("Download Excel report", download.content, report["filename"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def automation_page():
    st.title("Automation")
    st.caption("Save a recurring schedule now. The worker hook is ready for deployment when you enable report delivery.")
    with st.form("schedule"):
        report_type = st.selectbox("Report type", ["weekly"])
        frequency = st.selectbox("Frequency", ["weekly", "monthly"])
        delivery_time = st.time_input("Delivery time").strftime("%H:%M")
        submitted = st.form_submit_button("Save schedule", type="primary")
    if submitted:
        response = api("POST", "/schedules", json={"report_type": report_type, "frequency": frequency, "delivery_time": delivery_time})
        if response:
            st.success("Schedule saved.")
    response = api("GET", "/schedules")
    if response and response.json():
        st.subheader("Saved schedules")
        st.dataframe(pd.DataFrame(response.json()), use_container_width=True, hide_index=True)


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_page()
else:
    with st.sidebar:
        st.title("◈ MetricFlow")
        page = st.radio("Navigate", ["Dashboard", "Data Upload", "Reports", "Automation"])
        st.caption(st.session_state.user_email)
        if st.button("Sign out"):
            st.session_state.authenticated = False
            st.rerun()
    {"Dashboard": dashboard_page, "Data Upload": upload_page, "Reports": reports_page, "Automation": automation_page}[page]()
