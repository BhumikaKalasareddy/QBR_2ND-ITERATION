import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from app.services.bigquery_service import fetch_distinct_accounts, fetch_customer_profile

st.set_page_config(page_title="QBR Deck Builder", layout="wide")

# State Management
if "active_chart" not in st.session_state: st.session_state.active_chart = "Bar"
if "active_layout" not in st.session_state: st.session_state.active_layout = "Default"
if "ppt_file_data" not in st.session_state: st.session_state.ppt_file_data = None
if "ppt_file_name" not in st.session_state: st.session_state.ppt_file_name = None
if "pdf_file_data" not in st.session_state: st.session_state.pdf_file_data = None
if "pdf_file_name" not in st.session_state: st.session_state.pdf_file_name = None

QUARTER_MONTHS_MAP = {
    "Q1 2026": (["Jan 2026", "Feb 2026", "Mar 2026"], "Q1 2026 includes Jan, Feb, Mar"),
    "Q2 2026": (["Apr 2026", "May 2026", "Jun 2026"], "Q2 2026 includes Apr, May, Jun"),
    "Q3 2026": (["Jul 2026", "Aug 2026", "Sep 2026"], "Q3 2026 includes Jul, Aug, Sep"),
    "Q4 2026": (["Oct 2026", "Nov 2026", "Dec 2026"], "Q4 2026 includes Oct, Nov, Dec")
}

st.markdown("""
<style>
    header[data-testid="stHeader"] { background: transparent !important; z-index: 1 !important; }
    .block-container { padding-top: 3.5rem !important; padding-bottom: 6rem !important; }
    .stApp {
        background: radial-gradient(circle at 80% 20%, rgba(124, 58, 237, 0.25) 0%, transparent 40%),
                    radial-gradient(circle at 10% 80%, rgba(37, 99, 235, 0.25) 0%, transparent 40%),
                    linear-gradient(135deg, #0d081e 0%, #0a1128 50%, #120724 100%) !important;
        color: #F8FAFC !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div { color: #F8FAFC !important; }
    button[kind="primary"] {
        background: linear-gradient(90deg, #8b5cf6 0%, #3b82f6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    .status-available {
        background: rgba(34, 197, 94, 0.2); color: #4ADE80 !important;
        border: 1px solid rgba(34, 197, 94, 0.4); padding: 2px 8px; border-radius: 12px;
        font-size: 10px; font-weight: 600; float: right;
    }
</style>
""", unsafe_allow_html=True)

# SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("<h3 style='margin-bottom:20px;'>QBR Suite</h3>", unsafe_allow_html=True)
    st.markdown("**Deck Builder**")
    st.markdown("**Data Sources**")
    st.markdown("**Slide Library**")
    st.markdown("**Generated Decks**")
    st.markdown("**Settings**")
    st.divider()
    st.write("**Divya Singh**\n\nCSM APAC")

# TOP HEADER & ACTION BUTTONS
t1, t2, t3, t4 = st.columns([2.5, 1, 1, 1])
with t1:
    st.markdown("<h2 style='margin:0; padding-top:0;'>QBR Deck Builder</h2>", unsafe_allow_html=True)
    st.caption("Build data-driven QBR decks for your customers")
with t2: btn_preview = st.button("Preview Full Deck", key="btn_prev_top")
with t3: btn_top_ppt = st.button("Generate PPT", type="primary", key="btn_top_ppt")
with t4: btn_top_pdf = st.button("Generate PDF", key="btn_top_pdf")

st.markdown("<br>", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_accounts():
    accounts = fetch_distinct_accounts()
    defaults = ["Majid Al Futtaim Management Services Llc", "Grupo Salinas / Typhoon No.2", "Axa Asia"]
    for acc in defaults:
        if acc not in accounts: accounts.append(acc)
    return sorted(list(set(accounts)))

c_acc, c_qtr, c_mth = st.columns(3)
with c_acc:
    account_list = load_accounts()
    account_name = st.selectbox("Account", options=account_list, index=0)
with c_qtr:
    quarter = st.selectbox("Quarter", list(QUARTER_MONTHS_MAP.keys()), index=1)
    month_options, quarter_caption = QUARTER_MONTHS_MAP[quarter]
    st.caption(quarter_caption)
with c_mth: month = st.selectbox("Month", month_options, index=1)

profile = fetch_customer_profile(account_name, quarter)
left_col, mid_col, right_col = st.columns([1.1, 1.8, 1.4])

# LEFT COLUMN: ACCOUNT SUMMARY
with left_col:
    st.markdown("##### ACCOUNT SUMMARY")
    with st.container(border=True):
        st.write(f"**CSM:** {profile.get('csm_name', 'Divya Singh')}")
        st.write(f"**Region:** {profile.get('region', 'APAC')}")
        health_val = str(profile.get('health', 'Healthy'))
        health_color = "#4ADE80" if health_val.lower() != "nan" else "#94A3B8"
        st.write(f"**Health:** <span style='color:{health_color}; font-weight:700;'>{health_val}</span>", unsafe_allow_html=True)
        st.write(f"**ARR ({quarter}):** {profile.get('arr', '$2.40M')}")
        st.write(f"**Vertical:** {profile.get('vertical', 'Financial Services')}")

    st.markdown("##### AVAILABLE DATA SOURCES")
    with st.container(border=True):
        st.markdown("Product Adoption <span class='status-available'>Available</span>", unsafe_allow_html=True)
        st.markdown("Cases / Support <span class='status-available'>Available</span>", unsafe_allow_html=True)
        st.markdown("ARR Telemetry <span class='status-available'>Available</span>", unsafe_allow_html=True)
        st.markdown("TAU Dashboard <span class='status-available'>Available</span>", unsafe_allow_html=True)

# MIDDLE COLUMN: SLIDE SELECTION
with mid_col:
    st.markdown("##### SELECT SLIDES")
    selected_slides = []

    st.markdown("<span style='font-size:11px; color:#60A5FA; font-weight:700;'>COMMON SLIDES</span>", unsafe_allow_html=True)
    st.checkbox("1. Intro (Title Slide)", value=True, disabled=True)
    st.checkbox("2. Agenda", value=True, disabled=True)
    st.checkbox("3. Dedicated Partnership Team", value=True, disabled=True)
    st.checkbox("4. Executive Summary", value=True, disabled=True)
    st.checkbox("5. Mutual Value Plan Summary", value=True, disabled=True)
    st.checkbox("6. Key Metrics (Slide 6)", value=True, disabled=True)
    selected_slides.extend([1, 2, 3, 4, 5, 6])

    st.markdown("<span style='font-size:11px; color:#60A5FA; font-weight:700;'>PRODUCT & ADOPTION</span>", unsafe_allow_html=True)
    product_choice = st.selectbox("Select Product Focus", ["CASB", "SWG"], index=0)
    if st.checkbox("7. Product Overview", value=True): selected_slides.append(7)
    if st.checkbox("8. Feature Adoption", value=True): selected_slides.append(8)

    st.markdown("<span style='font-size:11px; color:#60A5FA; font-weight:700;'>ADOPTION MAP</span>", unsafe_allow_html=True)
    if st.checkbox("9. Adoption Map 1", value=True): selected_slides.append(9)
    if st.checkbox("10. Adoption Map 2", value=True): selected_slides.append(10)

    st.markdown("<span style='font-size:11px; color:#60A5FA; font-weight:700;'>OPERATIONS & SUPPORT</span>", unsafe_allow_html=True)
    if st.checkbox("11. Support Health", value=True): selected_slides.append(11)
    if st.checkbox("12. Case Trends & ART", value=True): selected_slides.append(12)

    st.markdown("<span style='font-size:11px; color:#60A5FA; font-weight:700;'>CLOSING</span>", unsafe_allow_html=True)
    if st.checkbox("13. What's Next", value=True): selected_slides.append(13)
    if st.checkbox("14. Thank You", value=True): selected_slides.append(14)

# RIGHT COLUMN: VISUALIZATION OPTIONS
with right_col:
    st.markdown("##### CHART & LAYOUT OPTIONS")
    with st.container(border=True):
        chart_choice = st.radio("Chart Type", ["Bar", "Line", "Area", "Column", "Donut", "Pie"], horizontal=True)
        st.session_state.active_chart = chart_choice

    st.markdown("##### SLIDE PREVIEW")
    with st.container(border=True):
        st.caption(f"{product_choice} Overview | {account_name}")
        dummy_df = pd.DataFrame({"Month": month_options, "Active Users": [8500, 11200, 14800]})
        fig = px.bar(dummy_df, x="Month", y="Active Users", color_discrete_sequence=["#3B82F6"])
        fig.update_layout(height=130, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"), margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key="main_preview_chart")

# MODAL PREVIEW
@st.dialog("Full Presentation Deck Preview", width="large")
def render_deck_preview_dialog(acc_name, qtr, mth, prod, slides, chart_fmt):
    st.markdown(f"### {acc_name} — QBR Deck Sequence")
    st.caption(f"Quarter: {qtr} ({mth}) | Product Focus: {prod} | Chart Style: {chart_fmt}")
    st.divider()

    slide_titles = {
        1: "1. Intro Slide", 2: "2. Agenda", 3: "3. Partnership Team", 4: "4. Executive Summary",
        5: "5. Mutual Value Plan", 6: "6. Key Metrics", 7: f"7. {prod} Overview", 8: f"8. {prod} Adoption",
        9: "9. Adoption Map 1", 10: "10. Adoption Map 2", 11: "11. Support Health",
        12: "12. Support Engagement", 13: "13. What's Next", 14: "14. Thank You"
    }

    for s_num in slides:
        with st.container():
            st.markdown(f"#### {slide_titles.get(s_num, f'Slide {s_num}')}")
            if s_num in [7, 8, 11, 12]:
                dummy_df = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [10, 20, 15]})
                fig = px.bar(dummy_df, x="Category", y="Value", color_discrete_sequence=["#3B82F6"])
                fig.update_layout(height=140, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"dialog_chart_{s_num}")
            else:
                st.info(f"Slide {s_num} layout container.")
            st.divider()

if btn_preview:
    render_deck_preview_dialog(account_name, quarter, month, product_choice, selected_slides, st.session_state.active_chart)

# BACKEND DECK GENERATION
trigger_ppt = btn_top_ppt
trigger_pdf = btn_top_pdf

if trigger_ppt or trigger_pdf:
    export_as_pdf = True if trigger_pdf else False
    ext = "pdf" if export_as_pdf else "pptx"
    
    with st.spinner(f"Compiling {len(selected_slides)}-slide deck for '{account_name}'..."):
        payload = {
            "account_name": account_name,
            "quarter": quarter,
            "product": product_choice,
            "selected_slides": selected_slides,
            "chart_type": st.session_state.active_chart,
            "layout_style": st.session_state.active_layout,
            "export_pdf": export_as_pdf
        }
        try:
            res = requests.post("http://127.0.0.1:8000/api/v1/export/generate-ppt", json=payload)
            if res.status_code == 200:
                safe_name = account_name.replace(' ', '_')
                if export_as_pdf:
                    st.session_state.pdf_file_data = res.content
                    st.session_state.pdf_file_name = f"QBR_{safe_name}_{quarter}_{product_choice}.pdf"
                else:
                    st.session_state.ppt_file_data = res.content
                    st.session_state.ppt_file_name = f"QBR_{safe_name}_{quarter}_{product_choice}.pptx"
                st.success("Deck compiled successfully!")
            else:
                st.error(f"Generation error: {res.text}")
        except Exception as e:
            st.error(f"Backend connection error: {e}")

# PERSISTENT DOWNLOAD BUTTONS
if st.session_state.ppt_file_data is not None or st.session_state.pdf_file_data is not None:
    st.markdown("---")
    st.markdown("##### DOWNLOAD GENERATED DECKS")
    dl_col1, dl_col2 = st.columns(2)
    
    with dl_col1:
        if st.session_state.ppt_file_data is not None:
            st.download_button(
                label=f"⬇️ Save {st.session_state.ppt_file_name}",
                data=st.session_state.ppt_file_data,
                file_name=st.session_state.ppt_file_name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key="btn_dl_ppt_cached",
                type="primary"
            )

    with dl_col2:
        if st.session_state.pdf_file_data is not None:
            st.download_button(
                label=f"⬇️ Save {st.session_state.pdf_file_name}",
                data=st.session_state.pdf_file_data,
                file_name=st.session_state.pdf_file_name,
                mime="application/pdf",
                key="btn_dl_pdf_cached",
                type="primary"
            )