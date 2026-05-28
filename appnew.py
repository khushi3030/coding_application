import os
import streamlit as st
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
from datetime import date, datetime
from dotenv import load_dotenv
import io

load_dotenv()

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Allura CRM – Reports",
    page_icon="📊",
    layout="wide",
)

# ─── Session State Init ────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"
if "nav_open" not in st.session_state:
    st.session_state.nav_open = False

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #f0f4f9;
    }

    .report-header {
        background: linear-gradient(135deg, #0f2942 0%, #1a6ebf 100%);
        color: white;
        padding: 22px 36px;
        border-radius: 12px;
        margin-bottom: 0;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .report-header-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.7rem;
        margin: 0;
    }
    .report-header-sub { font-size: 0.9rem; opacity: 0.75; margin-top: 2px; }

    .criteria-box {
        background: white;
        border: 1px solid #d8e4ef;
        border-radius: 12px;
        padding: 22px 28px;
        margin: 16px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .criteria-title {
        font-weight: 700;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #1a6ebf;
        margin-bottom: 14px;
    }
    .comment-box {
        background: #fff8e6;
        border-left: 4px solid #f0a500;
        padding: 10px 16px;
        border-radius: 0 6px 6px 0;
        margin-top: 12px;
        font-size: 0.9rem;
        color: #5a4000;
    }
    .outcome-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.25rem;
        color: #0f2942;
        margin: 22px 0 10px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #1a6ebf;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        border: 1px solid #d8e4ef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #0f2942; }
    .metric-label { font-size: 0.78rem; color: #8aa5bb; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }

    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.93rem;
        margin-bottom: 1rem;
        border-radius: 10px;
        overflow: hidden;
    }
    .styled-table thead tr {
        background: linear-gradient(90deg, #0f2942, #1a6ebf);
        color: white;
        font-weight: 700;
    }
    .styled-table thead th { padding: 12px 16px; text-align: left; }
    .styled-table tbody tr:nth-child(even) { background-color: #eaf2fb; }
    .styled-table tbody tr:nth-child(odd)  { background-color: #f7fafd; }
    .styled-table tbody td {
        padding: 10px 16px;
        border-bottom: 1px solid #d8e4ef;
        color: #1a2a3a;
    }

    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── DB Connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
    )

# ─── Queries ───────────────────────────────────────────────────────────────────
def fetch_donors(from_date, to_date):
    sql = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY donor_id ASC) AS "S.No",
            donor_id        AS "Donor ID",
            CONCAT(first_name, ' ', last_name) AS "Full Name",
            created_date    AS "Created Date",
            email           AS "Email",
            modified_date   AS "Modified Date",
            created_by      AS "Created By",
            modified_by     AS "Modified By"
        FROM Donor
        WHERE created_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY donor_id ASC;
    """
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, {"from_date": from_date, "to_date": to_date})
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return pd.DataFrame()

def fetch_all_donors():
    sql = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY donor_id ASC) AS "S.No",
            donor_id        AS "Donor ID",
            CONCAT(first_name, ' ', last_name) AS "Full Name",
            created_date    AS "Created Date",
            email           AS "Email",
            modified_date   AS "Modified Date",
            created_by      AS "Created By",
            modified_by     AS "Modified By"
        FROM Donor
        ORDER BY donor_id ASC;
    """
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return pd.DataFrame()

def fetch_donations(from_date, to_date):
    sql = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY d.created_date, dn."DonationID") AS s_no,
            d.created_date                     AS date,
            dn."DonationID"                    AS donation_id,
            d.first_name || ' ' || d.last_name AS donor_full_name,
            dn."DonationAmount"                AS donation_amount
        FROM Donation dn
        JOIN Donor d ON d.donor_id = dn."DonorID"
        WHERE d.created_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY d.created_date, dn."DonationID";
    """
    try:
        conn = get_connection()
        return pd.read_sql_query(sql, conn, params={"from_date": from_date, "to_date": to_date})
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return pd.DataFrame()

def fetch_pledges(from_date, to_date):
    sql = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY d.created_date, p."PledgeID") AS s_no,
            p."PledgeID"                        AS pledge_id,
            d.first_name || ' ' || d.last_name  AS pledger_full_name,
            d.created_date                      AS date_added,
            d.email                             AS email,
            p.PledgeAmount                      AS pledge_amount
        FROM Pledges p
        JOIN Donor d ON d.donor_id = p.DonorID
        WHERE d.created_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY d.created_date, p."PledgeID";
    """
    try:
        conn = get_connection()
        return pd.read_sql_query(sql, conn, params={"from_date": from_date, "to_date": to_date})
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return pd.DataFrame()

# ─── HTML Table Builders ───────────────────────────────────────────────────────
def build_donation_table(df):
    if df.empty:
        body = "<tr><td colspan='5' style='text-align:center;color:#c0392b;padding:20px'>No donations found for selected period.</td></tr>"
    else:
        rows = ""
        for _, row in df.iterrows():
            rows += (
                f"<tr><td>{int(row['s_no'])}</td>"
                f"<td>{pd.to_datetime(row['date']).strftime('%d-%b-%Y')}</td>"
                f"<td>{row['donation_id']}</td>"
                f"<td>{row['donor_full_name']}</td>"
                f"<td>{float(row['donation_amount']):,.2f}</td></tr>"
            )
        body = rows
    return (
        '<table class="styled-table"><thead><tr>'
        "<th>S.No</th><th>Date</th><th>Donation ID</th><th>Donor Full Name</th><th>Donation Amount</th>"
        f"</tr></thead><tbody>{body}</tbody></table>"
    )

def build_pledge_table(df):
    if df.empty:
        body = "<tr><td colspan='4' style='text-align:center;color:#c0392b;padding:20px'>No pledges found for selected period.</td></tr>"
    else:
        rows = ""
        for _, row in df.iterrows():
            rows += (
                f"<tr><td>{int(row['s_no'])}</td>"
                f"<td>{row['pledge_id']}</td>"
                f"<td>{row['pledger_full_name']}</td>"
                f"<td>{float(row['pledge_amount']):,.2f}</td></tr>"
            )
        body = rows
    return (
        '<table class="styled-table"><thead><tr>'
        "<th>S.No</th><th>Pledge ID</th><th>Pledger Full Name</th><th>Pledge Amount</th>"
        f"</tr></thead><tbody>{body}</tbody></table>"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  NAV  — pure st.markdown HTML/CSS (no Streamlit buttons in the nav at all)
#  Clicking "Reports" HTML button sets ?nav=open via a query param trick,
#  but Streamlit doesn't support that well — so we use st.markdown + st.button
#  ONLY for the invisible trigger, and render the visual bar in pure HTML.
# ══════════════════════════════════════════════════════════════════════════════
def render_nav():

    # ───────────────── CSS ─────────────────
    st.markdown("""
    <style>

    /* REMOVE DEFAULT STREAMLIT BUTTON STYLING */
    div.stButton > button {
        width: 100%;
        border: none !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 700 !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* ───────── REPORTS BUTTON ───────── */
    
div.stButton > button[kind="secondary"] {

    background: linear-gradient(135deg, #8fd14c 0%, #c4f08f 100%) !important;

    color: #163000 !important;

    border: 2px solid #6fb12e !important;

    font-size: 22px !important;

    border-radius: 14px 14px 0 0 !important;

    padding: 16px 0 !important;

    box-shadow: 0 4px 16px rgba(111,177,46,0.28) !important;
}


    div.stButton > button[kind="secondary"]:hover {
        filter: brightness(1.05) !important;
        transform: translateY(-1px);
    }

    /* ───────── DONOR BUTTON ───────── */
    button[aria-label="🧑‍🤝‍🧑 Donor"] {

    background: linear-gradient(135deg, #9edb72 0%, #caf0a6 100%) !important;

    color: #163300 !important;

    border: 2px solid #6eb13d !important;

    border-radius: 0 0 0 14px !important;

    font-size: 17px !important;

    font-weight: 700 !important;

    padding: 14px 0 !important;
}

    
/* ───────── DONATION BUTTON ───────── */
button[aria-label="💰 Donation"] {

    background: linear-gradient(135deg, #ffb3b3 0%, #ffd6d6 100%) !important;

    color: #5a1010 !important;

    border: 2px solid #e57373 !important;

    border-radius: 0 !important;

    font-size: 17px !important;

    font-weight: 700 !important;

    padding: 14px 0 !important;

}            
    
button[aria-label="🤝 Pledge"] {

    background: linear-gradient(135deg, #8fe0f5 0%, #c8f4ff 100%) !important;

    color: #00485c !important;

    border: 2px solid #4dc8ea !important;

    border-radius: 0 0 14px 0 !important;

    font-size: 17px !important;

    font-weight: 700 !important;

    padding: 14px 0 !important;
}
    
    
            
    

    /* ───────── HOVER EFFECT ───────── */
    div.stButton > button:hover {
        transform: translateY(-2px);
        filter: brightness(1.06);
    }

    </style>
    """, unsafe_allow_html=True)

    # ───────────────── CENTER NAV ─────────────────
    _, nav_col, _ = st.columns([1, 2, 1])

    with nav_col:

        # GREEN REPORTS BUTTON
        if st.button(
            "📊 Reports",
            use_container_width=True,
            key="btn_reports",
            type="secondary"
        ):
            st.session_state.nav_open = not st.session_state.nav_open

            if not st.session_state.nav_open:
                st.session_state.page = "home"

            st.rerun()

        # SUB BUTTONS
        if st.session_state.nav_open:

            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button(
                    "🧑‍🤝‍🧑 Donor",
                    use_container_width=True,
                    key="btn_donor"
                ):
                    st.session_state.page = "donor"
                    st.rerun()

            with c2:
                if st.button(
                    "💰 Donation",
                    use_container_width=True,
                    key="btn_donation"
                ):
                    st.session_state.page = "donation"
                    st.rerun()

            with c3:
                if st.button(
                    "🤝 Pledge",
                    use_container_width=True,
                    key="btn_pledge"
                ):
                    st.session_state.page = "pledge"
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════
def page_home():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align:center;font-family:DM Serif Display,serif;"
        "font-size:2.8rem;color:#0f2942;margin-bottom:4px'>📊 Allura CRM Reports</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;font-size:1.1rem;color:#5a7a96;"
        "margin-bottom:36px'>Click <b>Reports</b> above to select a report</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DONOR REPORT
# ══════════════════════════════════════════════════════════════════════════════
def page_donor():
    st.markdown(
        f"""
        <div class="report-header">
            <span style="font-size:2rem">🧑‍🤝‍🧑</span>
            <div>
                <div class="report-header-title">Donor Report</div>
                <div class="report-header-sub">Allura CRM · Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filter_mode = st.radio(
        "Filter mode",
        ["By Created Date Range", "Show All Donors"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown('<div class="criteria-box">', unsafe_allow_html=True)
    st.markdown('<div class="criteria-title">Input Criteria – Period</div>', unsafe_allow_html=True)

    from_date = to_date = None
    if filter_mode == "By Created Date Range":
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            from_date = st.date_input("From Date", value=date(2020, 1, 1), key="d_from")
        with c2:
            to_date = st.date_input("To Date", value=date.today(), key="d_to")
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            generate = st.button("🔍 Generate", use_container_width=True, key="d_gen")
    else:
        generate = st.button("🔍 Load All Donors", use_container_width=True, key="d_all")

    st.markdown(
        '<div class="comment-box"><b>Comment:</b> How many donors exist in the system '
        "between these two dates if the record is not deleted already.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if filter_mode == "By Created Date Range" and from_date and to_date:
        if from_date > to_date:
            st.warning("⚠️ 'From Date' cannot be after 'To Date'.")
            st.stop()
        df = fetch_donors(from_date, to_date)
    elif filter_mode == "Show All Donors":
        df = fetch_all_donors()
    else:
        df = pd.DataFrame()

    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{len(df)}</div>'
            '<div class="metric-label">Total Donors Found</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">'
            f'{from_date.strftime("%d %b %Y") if from_date else "—"}</div>'
            '<div class="metric-label">From Date</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">'
            f'{to_date.strftime("%d %b %Y") if to_date else "—"}</div>'
            '<div class="metric-label">To Date</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="outcome-title">Outcome</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("No donor records found for the selected criteria.")
    else:
        cols = ["S.No", "Donor ID", "Full Name", "Created Date", "Email"]
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button(
            "⬇️ Export as CSV",
            data=buf.getvalue(),
            file_name=f"donor_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DONATION REPORT
# ══════════════════════════════════════════════════════════════════════════════
def page_donation():
    st.markdown(
        f"""
        <div class="report-header">
            <span style="font-size:2rem">💰</span>
            <div>
                <div class="report-header-title">Donation Report</div>
                <div class="report-header-sub">Allura CRM · Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="criteria-box">', unsafe_allow_html=True)
    st.markdown('<div class="criteria-title">Input Criteria – Period</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
    with c1:
        st.markdown("<div style='padding-top:8px'><b>Period Selection</b></div>", unsafe_allow_html=True)
    with c2:
        from_date = st.date_input("From Date", value=date(2026, 4, 1), key="don_from")
    with c3:
        to_date = st.date_input("To Date", value=date.today(), key="don_to")
    with c4:
        st.markdown("<div style='padding-top:4px'></div>", unsafe_allow_html=True)
        generate = st.button("🔍 Generate", type="primary", use_container_width=True, key="don_gen")

    st.markdown(
        '<div class="comment-box"><b>Comment:</b> How many distinct donations exist in the system '
        "between these two dates if the record is not deleted already.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="outcome-title">Outcome</div>', unsafe_allow_html=True)

    if generate:
        if from_date > to_date:
            st.error("'From Date' must be on or before 'To Date'.")
            st.markdown(build_donation_table(pd.DataFrame()), unsafe_allow_html=True)
        else:
            with st.spinner("Fetching donations…"):
                df = fetch_donations(from_date, to_date)
            st.markdown(build_donation_table(df), unsafe_allow_html=True)
            if not df.empty:
                st.caption(
                    f"Total distinct donations found: **{len(df)}**  |  "
                    f"Period: {from_date.strftime('%d-%b-%Y')} → {to_date.strftime('%d-%b-%Y')}"
                )
                buf = io.StringIO()
                df.to_csv(buf, index=False)
                st.download_button(
                    "⬇️ Export as CSV",
                    data=buf.getvalue(),
                    file_name=f"donation_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
    else:
        st.markdown(build_donation_table(pd.DataFrame()), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: PLEDGE REPORT
# ══════════════════════════════════════════════════════════════════════════════
def page_pledge():
    st.markdown(
        f"""
        <div class="report-header">
            <span style="font-size:2rem">🤝</span>
            <div>
                <div class="report-header-title">Pledge Report</div>
                <div class="report-header-sub">Allura CRM · Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="criteria-box">', unsafe_allow_html=True)
    st.markdown('<div class="criteria-title">Input Criteria – Period</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
    with c1:
        st.markdown("<div style='padding-top:8px'><b>Period Selection</b></div>", unsafe_allow_html=True)
    with c2:
        from_date = st.date_input("From Date", value=date(2026, 4, 1), key="pl_from")
    with c3:
        to_date = st.date_input("To Date", value=date.today(), key="pl_to")
    with c4:
        st.markdown("<div style='padding-top:4px'></div>", unsafe_allow_html=True)
        generate = st.button("🔍 Generate", type="primary", use_container_width=True, key="pl_gen")

    st.markdown(
        '<div class="comment-box"><b>Comment:</b> How many pledges exist in the system '
        "between these two dates if the record is not deleted already.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="outcome-title">Outcome</div>', unsafe_allow_html=True)

    if generate:
        if from_date > to_date:
            st.error("'From Date' must be on or before 'To Date'.")
            st.markdown(build_pledge_table(pd.DataFrame()), unsafe_allow_html=True)
        else:
            with st.spinner("Fetching pledges…"):
                df = fetch_pledges(from_date, to_date)
            st.markdown(build_pledge_table(df), unsafe_allow_html=True)
            if not df.empty:
                st.caption(
                    f"Total pledges found: **{len(df)}**  |  "
                    f"Period: {from_date.strftime('%d-%b-%Y')} → {to_date.strftime('%d-%b-%Y')}"
                )
                buf = io.StringIO()
                df.to_csv(buf, index=False)
                st.download_button(
                    "⬇️ Export as CSV",
                    data=buf.getvalue(),
                    file_name=f"pledge_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
    else:
        st.markdown(build_pledge_table(pd.DataFrame()), unsafe_allow_html=True)


# ─── Footer ────────────────────────────────────────────────────────────────────
def footer():
    st.markdown("---")
    st.caption(f"Allura CRM Reporting  •  {datetime.now().strftime('%d %b %Y, %H:%M')}")


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER — nav only on home, back button only on report pages
# ══════════════════════════════════════════════════════════════════════════════
page = st.session_state.page

if page == "home":
    render_nav()
    page_home()
else:
    # ── Back button on report pages ──
    if st.button("← Back to Reports", key="back"):
        st.session_state.page = "home"
        st.session_state.nav_open = True   # re-open sub-tabs when going back
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

    if page == "donor":
        page_donor()
    elif page == "donation":
        page_donation()
    elif page == "pledge":
        page_pledge()

footer()
