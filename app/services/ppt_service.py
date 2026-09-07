import io
import os
import re
import matplotlib.pyplot as plt
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

COLOR_BLUE          = RGBColor(0x00, 0x66, 0xFF)
COLOR_ORANGE        = RGBColor(0xF9, 0x73, 0x16)
COLOR_NAVY          = RGBColor(0x0F, 0x17, 0x2A)
COLOR_WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_MUTED_BG      = RGBColor(0xF5, 0xF7, 0xFA)
COLOR_GREEN_HEADER = RGBColor(0x1B, 0xC5, 0xBD)
COLOR_GRAY_BORDER   = RGBColor(0xE0, 0xE0, 0xE0)

# =========================================================
# HELPER FUNCTIONS & COMPONENTS
# =========================================================

def _add_header_banner(slide, title_text: str):
    """Standard top header banner for content slides."""
    banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.9))
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_BLUE
    banner.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.12), Inches(12.0), Inches(0.7))
    p = tb.text_frame.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

def _add_transition_slide(prs, title_text: str):
    """Full blue transition slide (for Executive Summary, What's Next, etc.)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_BLUE
    bg.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.8), Inches(3.2), Inches(11.0), Inches(2.0))
    p = tb.text_frame.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    return slide

def _add_kpi_card(slide, x: float, y: float, w: float, h: float, label: str, val: str, sub: str = ""):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_MUTED_BG
    card.line.color.rgb = COLOR_GRAY_BORDER

    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.1)
    tf.margin_left = Inches(0.15)
    
    p1 = tf.paragraphs[0]
    p1.text = label.upper()
    p1.font.size = Pt(8)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(120, 120, 120)

    p2 = tf.add_paragraph()
    p2.text = str(val)
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_BLUE

    if sub:
        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(8)
        p3.font.color.rgb = RGBColor(40, 167, 69)

def _generate_chart_image(categories: list, values: list, title: str, chart_type: str = "Bar", figsize=(5, 3.5)) -> io.BytesIO:
    plt.figure(figsize=figsize, dpi=100)
    color = "#0066FF"
    total_val = sum(values) if values else 0

    if chart_type in ["Donut", "Pie"]:
        if total_val == 0:
            categories = ["No Active Data"]
            values = [1]
            colors = ["#94A3B8"]
        else:
            colors = ["#0066FF", "#3B82F6", "#60A5FA", "#A855F7"]
            
        wedge = dict(width=0.4) if chart_type == "Donut" else dict()
        plt.pie(values, labels=categories, colors=colors, wedgeprops=wedge, autopct='%1.0f%%' if total_val > 0 else '')
    elif chart_type == "Line":
        plt.plot(categories, values, marker='o', color=color, linewidth=2)
    elif chart_type == "Area":
        plt.fill_between(range(len(categories)), values, color=color, alpha=0.4)
    else:
        bars = plt.bar(categories, values, color=color, width=0.5)
        if total_val > 0:
            plt.bar_label(bars, fmt='%.1f', padding=3, fontsize=8)

    plt.title(title, fontsize=10, fontweight='bold', pad=10)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf

# =========================================================
# INDIVIDUAL SLIDE RENDERERS
# =========================================================

# SLIDE 1: Title Slide
def render_slide_1_title(prs, account_name: str, date_str: str = "June 2026"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_NAVY
    bg.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.8), Inches(11.333), Inches(3.0))
    p1 = tb.text_frame.paragraphs[0]
    p1.text = f"Quarterly Business Review\n{account_name}"
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE

    p2 = tb.text_frame.add_paragraph()
    p2.text = f"\nPrepared by CS Team | {date_str}"
    p2.font.size = Pt(16)
    p2.font.color.rgb = RGBColor(148, 163, 184)

# SLIDE 2: Agenda Slide
def render_slide_2_agenda(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Agenda")

    # Left Agenda Bullets
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(1.3), Inches(6.5), Inches(5.5))
    tf = tb.text_frame
    tf.word_wrap = True

    items = [
        ("Team Introduction", []),
        ("Executive Summary", ["Mutual Value Plan Summary", "Services & Engagement", "Voice of Customer", "Next Steps"]),
        ("Operational Metrics", ["Support Engagement", "Adoption Map", "Shadow Summary"]),
        ("What's Next?", ["Why DSPM?"])
    ]

    for title, subs in items:
        p = tf.add_paragraph()
        p.text = f"•  {title}"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_NAVY
        for sub in subs:
            sp = tf.add_paragraph()
            sp.text = f"    ◦  {sub}"
            sp.font.size = Pt(13)
            sp.font.color.rgb = RGBColor(71, 85, 105)

# SLIDE 3: Dedicated Partnership Team
def render_slide_3_partnership_team(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Dedicated Partnership Team")

    roles = [
        ("Divya Singh", "Customer Success Manager"),
        ("Technical Specialist", "CS Consultant / Architect"),
        ("Account Executive", "Commercial Manager"),
        ("Support Engineer", "Lead Technical Support")
    ]

    for idx, (name, title) in enumerate(roles):
        x = 0.8 + (idx % 2) * 5.8
        y = 1.6 + (idx // 2) * 2.6
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(5.2), Inches(2.2))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_MUTED_BG
        card.line.color.rgb = COLOR_GRAY_BORDER

        tf = card.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = name
        p1.font.size = Pt(18)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_BLUE

        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_NAVY

# SLIDE 4: Executive Summary Transition
def render_slide_4_executive_summary(prs):
    _add_transition_slide(prs, "Executive Summary")

# SLIDE 5: Mutual Value Plan Summary
def render_slide_5_mutual_value_plan(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Mutual Value Plan Summary")

    tbl_shape = slide.shapes.add_table(4, 3, Inches(0.6), Inches(1.5), Inches(12.133), Inches(5.0))
    tbl = tbl_shape.table
    
    col_widths = [Inches(3.5), Inches(5.5), Inches(3.133)]
    for i, w in enumerate(col_widths):
        tbl.columns[i].width = w

    headers = ["Goal / Objective", "Value Delivered & Progress", "Status"]
    for i, h in enumerate(headers):
        cell = tbl.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_BLUE
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.color.rgb = COLOR_WHITE

    goals = [
        ("Shadow IT Visibility", "Configured risk rules and audited 100+ cloud services.", "Completed"),
        ("CASB User Onboarding", "Scaled active user base to targets across Q2.", "In Progress"),
        ("DLP Policy Enforcement", "Enforced policy checks across core tenant instances.", "On Track")
    ]

    for idx, (g, p, s) in enumerate(goals):
        tbl.cell(idx+1, 0).text = g
        tbl.cell(idx+1, 1).text = p
        tbl.cell(idx+1, 2).text = s

# SLIDE 6: Key Metrics
def render_slide_6_kpi(prs, kpi_metrics: list):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Key Operational Metrics")

    for idx, item in enumerate(kpi_metrics[:6]):
        x = 0.6 + (idx % 3) * 4.15
        y = 1.8 if idx < 3 else 4.4
        _add_kpi_card(slide, x, y, 3.8, 2.2, item.get("label", ""), item.get("num", "$0"), item.get("sub", ""))

# SLIDE 7: CASB Overview
def render_casb_slide_7(prs, df: pd.DataFrame, chart_type: str = "Bar"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "CASB Adoption KPIs & Summary")
    if df.empty: return

    row = df.iloc[0]
    _add_kpi_card(slide, 0.6, 1.3, 2.8, 1.1, "Total Account ARR", f"${row.get('account_arr', 0):,.0f}")
    _add_kpi_card(slide, 3.6, 1.3, 2.8, 1.1, "Active Users", f"{row.get('CASB_Active_user', 0):,}", f"{(row.get('casb_user_adoption_pct', 0)*100):.1f}% Active")
    _add_kpi_card(slide, 6.6, 1.3, 2.8, 1.1, "Licensed Users", f"{row.get('CASB_User_Licensed', 0):,}")
    _add_kpi_card(slide, 9.6, 1.3, 2.8, 1.1, "Active Apps (excl MS)", f"{row.get('feature_adoption_active_saa_s_deployed_count_excl_ms', 0):,}")

    tbl_shape = slide.shapes.add_table(2, 5, Inches(0.6), Inches(2.7), Inches(12.133), Inches(3.8))
    tbl = tbl_shape.table
    for i, h in enumerate(["Account Name", "Active Users", "Licensed Users", "User Adoption Tier", "CASB Feature Tier"]):
        cell = tbl.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_BLUE
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.color.rgb = COLOR_WHITE

    tbl.cell(1, 0).text = str(row.get("consolidated_account_name", ""))
    tbl.cell(1, 1).text = f"{row.get('CASB_Active_user', 0):,}"
    tbl.cell(1, 2).text = f"{row.get('CASB_User_Licensed', 0):,}"
    tbl.cell(1, 3).text = str(row.get("casb_user_adoption_category", "N/A"))
    tbl.cell(1, 4).text = str(row.get("casb_adoption_category", "N/A"))

# SLIDE 8: CASB Feature Adoption
def render_casb_slide_8(prs, df: pd.DataFrame, chart_type: str = "Bar"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "CASB Cloud Tenant & Feature Deployment Analytics")
    if df.empty: return

    cats = ["Active SaaS Apps", "Active IaaS Apps"]
    vals = [df["Active_SaaS_Apps_Deployed_Count"].sum(), df["Active_IaaS_Apps_Deployed_Count"].sum()]
    img_buf = _generate_chart_image(cats, vals, "Cloud App Deployment Breakdown", chart_type=chart_type, figsize=(5.2, 3.8))
    slide.shapes.add_picture(img_buf, Inches(0.6), Inches(1.5), width=Inches(5.2))

    tbl_shape = slide.shapes.add_table(min(len(df) + 1, 5), 4, Inches(6.0), Inches(1.5), Inches(6.7), Inches(3.8))
    tbl = tbl_shape.table
    for i, h in enumerate(["Tenant Name", "Environment", "SaaS Active", "IaaS Active"]):
        cell = tbl.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_GREEN_HEADER
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.color.rgb = COLOR_WHITE

    for idx, r in df.head(4).reset_index(drop=True).iterrows():
        tbl.cell(idx + 1, 0).text = str(r.get("Tenant_Name", ""))
        tbl.cell(idx + 1, 1).text = str(r.get("Environment", ""))
        tbl.cell(idx + 1, 2).text = str(r.get("Active_SaaS_Apps_Deployed_Count", 0))
        tbl.cell(idx + 1, 3).text = str(r.get("Active_IaaS_Apps_Deployed_Count", 0))

# SLIDES 9-10: Adoption Maps
def render_slide_9_adoption_map_1(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Product Adoption Map — Part 1")

def render_slide_10_adoption_map_2(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Product Adoption Map — Part 2")

# SLIDE 11: Support Health
def render_slide_11_support_health(prs, support_data: dict, chart_type: str = "Bar"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Support Health")

    # Left Text Narrative
    tb = slide.shapes.add_textbox(Inches(0.4), Inches(1.2), Inches(3.3), Inches(5.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "Health Trend: Case creation peaked in April 2026 with 17 cases but has since stabilized. Currently, about 64% of cases are resolved, while a small portion remains 'With Engineering' or 'Work in Progress,' indicating a healthy throughput."
    p1.font.size = Pt(9)

    p2 = tf.add_paragraph()
    p2.text = "\nKey Patterns and Themes\nAn analysis of the case summaries reveals recurring themes related to user access and identity management. Key terms frequently appearing include:\n• Users/User: Mentioned in 14 cases\n• Login/Access: Mentioned in 11 cases\n• Tenant/Portal: Mentioned in 9 cases\n• Certificate: Mentioned in 3 cases"
    p2.font.size = Pt(8.5)

    # Chart 4: Pie Chart with Zero Check
    df4 = support_data.get("chart4", pd.DataFrame())
    fig4, ax4 = plt.subplots(figsize=(4.0, 2.4), dpi=150)
    
    statuses = df4.get("case_status", ["Resolved", "Customer", "Engineering"]).tolist() if not df4.empty else ["No Cases"]
    counts = df4.get("case_count", [1]).tolist() if not df4.empty else [1]
    
    if sum(counts) == 0:
        counts = [1]
        statuses = ["No Cases"]

    ax4.pie(counts, labels=statuses, autopct='%1.0f%%' if sum(counts) > 1 else '', textprops={'fontsize': 6})
    ax4.set_title("Current Case Status Distribution", fontsize=9, fontweight='bold')
    plt.tight_layout()
    b4 = io.BytesIO(); plt.savefig(b4, format='png'); plt.close(); b4.seek(0)

    b1 = _generate_chart_image(["Apr", "May", "Jun"], [5, 10, 6], "Monthly Case Creation Trend", chart_type="Line")
    b2 = _generate_chart_image(["Resolved", "How-To"], [6, 17], "Resolution Categories for Closed Cases", chart_type="Bar")
    b3 = _generate_chart_image(["CASB", "DLP"], [23, 6], "Case Breakdown by Product", chart_type="Column")

    slide.shapes.add_picture(b1, Inches(3.8), Inches(1.2), width=Inches(4.4))
    slide.shapes.add_picture(b2, Inches(8.4), Inches(1.2), width=Inches(4.4))
    slide.shapes.add_picture(b3, Inches(3.8), Inches(4.2), width=Inches(4.4))
    slide.shapes.add_picture(b4, Inches(8.4), Inches(4.2), width=Inches(4.4))

# SLIDE 12: Support Engagement
def render_slide_12_support_engagement(prs, case_trends: dict, chart_type: str = "Bar"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_header_banner(slide, "Support Engagement")

    tb = slide.shapes.add_textbox(Inches(0.4), Inches(1.2), Inches(5.5), Inches(3.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Case Volume:\n  1. 54 new cases entered, with 51 cases closed.\n  2. Entered incident volume remained stable.\n• Resolution Times:\n  1. Average Resolution Time (ART): 17 days.\n• Case Severity:\n  High-severity incidents dropped significantly."
    p.font.size = Pt(10)

    df_s1 = case_trends.get("slide1_summary", pd.DataFrame())
    tbl_shape = slide.shapes.add_table(4, 4, Inches(6.2), Inches(1.2), Inches(6.5), Inches(1.8))
    tbl = tbl_shape.table
    headers = ["Month", "Total Entered", "Total Closed", "ART"]
    for i, h in enumerate(headers):
        cell = tbl.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(230, 230, 230)
        cell.text_frame.paragraphs[0].font.bold = True

    for idx, r in df_s1.head(3).iterrows():
        tbl.cell(idx+1, 0).text = str(r.get("cases_open_dt_month_label", ""))
        tbl.cell(idx+1, 1).text = str(r.get("cases_total_entered_1", ""))
        tbl.cell(idx+1, 2).text = str(r.get("cases_total_closed_1", ""))
        tbl.cell(idx+1, 3).text = f"{r.get('cases_art_1', 0):.1f}"

    fig, ax1 = plt.subplots(figsize=(6.2, 3.2), dpi=150)
    months = df_s1.get("cases_open_dt_month_label", ["Apr-26", "May-26", "Jun-26"])
    entered = df_s1.get("cases_total_entered_1", [10, 24, 20])
    art = df_s1.get("cases_art_1", [19.2, 13.7, 19.2])

    ax1.bar(months, entered, color='#3b82f6', width=0.4)
    ax2 = ax1.twinx()
    ax2.plot(months, art, color='#f97316', marker='o')
    
    plt.title("Total Closed — ART (days)", fontsize=10, fontweight='bold')
    plt.tight_layout()
    b = io.BytesIO(); plt.savefig(b, format='png'); plt.close(); b.seek(0)
    slide.shapes.add_picture(b, Inches(6.2), Inches(3.4), width=Inches(6.5))

# SLIDE 13: What's Next Transition
def render_slide_13_whats_next(prs, data: dict = None):
    _add_transition_slide(prs, "What's Next")

# SLIDE 14: Thank You Closing
def render_slide_14_thank_you(prs, account_name: str):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_NAVY
    bg.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(1.0), Inches(3.0), Inches(11.333), Inches(2.0))
    p = tb.text_frame.paragraphs[0]
    p.text = "Thank you!"
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

# =========================================================
# MAIN PRESENTATION GENERATION PIPELINE
# =========================================================

def generate_qbr_presentation(
    account_name: str, 
    quarter: str, 
    product_choice: str, 
    selected_slides: list, 
    chart_type: str = "Bar", 
    layout_style: str = "Default", 
    kpi_data=None, 
    casb1_df=None, 
    casb2_df=None, 
    swg1_df=None, 
    swg2_df=None, 
    support_data=None, 
    case_trends=None, 
    whats_next_data=None
) -> str:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    if 1 in selected_slides: render_slide_1_title(prs, account_name)
    if 2 in selected_slides: render_slide_2_agenda(prs)
    if 3 in selected_slides: render_slide_3_partnership_team(prs)
    if 4 in selected_slides: render_slide_4_executive_summary(prs)
    if 5 in selected_slides: render_slide_5_mutual_value_plan(prs)
    if 6 in selected_slides: render_slide_6_kpi(prs, kpi_data or [])

    if 7 in selected_slides:
        if product_choice.upper() == "CASB": render_casb_slide_7(prs, casb1_df if casb1_df is not None else pd.DataFrame(), chart_type=chart_type)
        else: render_casb_slide_7(prs, swg1_df if swg1_df is not None else pd.DataFrame(), chart_type=chart_type)
            
    if 8 in selected_slides:
        if product_choice.upper() == "CASB": render_casb_slide_8(prs, casb2_df if casb2_df is not None else pd.DataFrame(), chart_type=chart_type)
        else: render_casb_slide_8(prs, swg2_df if swg2_df is not None else pd.DataFrame(), chart_type=chart_type)

    if 9 in selected_slides: render_slide_9_adoption_map_1(prs)
    if 10 in selected_slides: render_slide_10_adoption_map_2(prs)

    if 11 in selected_slides: render_slide_11_support_health(prs, support_data or {}, chart_type=chart_type)
    if 12 in selected_slides: render_slide_12_support_engagement(prs, case_trends or {}, chart_type=chart_type)
    if 13 in selected_slides: render_slide_13_whats_next(prs, whats_next_data or {})
    if 14 in selected_slides: render_slide_14_thank_you(prs, account_name)

    out_dir = "app/templates"
    os.makedirs(out_dir, exist_ok=True)
    safe_account_name = re.sub(r'[\\/*?:"<>|]', '_', account_name).replace(' ', '_')
    out_path = os.path.join(out_dir, f"generated_qbr_{safe_account_name}.pptx")
    prs.save(out_path)
    return out_path