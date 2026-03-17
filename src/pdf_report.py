"""
pdf_report.py
Generates a professional 1-page PDF summary using ReportLab.
"""

import io
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.utils import PALETTE, format_currency


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
NAVY      = colors.HexColor("#1A3A5C")
NAVY_LIGHT= colors.HexColor("#2C5282")
LIGHT_ROW = colors.HexColor("#F0F4FA")
ACCENT    = colors.HexColor("#3B6FD4")
MID_GRAY  = colors.HexColor("#666666")
RULE_GRAY = colors.HexColor("#CCCCCC")
WHITE     = colors.white


def _fig_to_image(fig: plt.Figure, width: float, height: float) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def _wealth_chart(ages, p10, p50, p90, target_wealth, retirement_age):
    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FAFBFD")
    ax.fill_between(ages, p10 / 1e6, p90 / 1e6, alpha=0.15, color=PALETTE["blue"])
    ax.plot(ages, p90 / 1e6, color=PALETTE["blue"], lw=0.8, ls="--", alpha=0.45)
    ax.plot(ages, p10 / 1e6, color=PALETTE["blue"], lw=0.8, ls="--", alpha=0.45)
    ax.plot(ages, p50 / 1e6, color=PALETTE["blue"], lw=2.2, label="Median")
    ax.axhline(target_wealth / 1e6, color=PALETTE["red"], lw=1.3, ls=":",
               label=f"Target {format_currency(target_wealth)}")
    ax.axvline(retirement_age, color=PALETTE["gray"], lw=1.0, ls="--", alpha=0.5)
    ax.set_xlabel("Age", fontsize=7.5)
    ax.set_ylabel("Value ($M)", fontsize=7.5)
    ax.set_title("Monte Carlo Wealth Simulation", fontsize=8.5, fontweight="bold", pad=4)
    ax.legend(fontsize=6.5, framealpha=0.9, loc="upper left")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.1f}M"))
    ax.tick_params(labelsize=6.5)
    ax.grid(True, alpha=0.18, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.6)
    return fig


def _glidepath_chart(ages, glidepath):
    import pandas as pd
    etfs = list(glidepath[0].keys())
    chart_colors = [PALETTE["blue"], PALETTE["green"], PALETTE["orange"]]
    data = {etf: [g[etf] * 100 for g in glidepath] for etf in etfs}
    df = pd.DataFrame(data, index=ages)
    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FAFBFD")
    bottom = np.zeros(len(ages))
    for i, etf in enumerate(etfs):
        ax.bar(ages, df[etf], bottom=bottom,
               label=etf.split(" (")[0], color=chart_colors[i], alpha=0.88, width=0.85)
        bottom += df[etf].values
    ax.set_xlabel("Age", fontsize=7.5)
    ax.set_ylabel("Allocation (%)", fontsize=7.5)
    ax.set_title("Portfolio Glide Path", fontsize=8.5, fontweight="bold", pad=4)
    ax.legend(loc="upper right", fontsize=6.5, framealpha=0.9)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.set_ylim(0, 115)
    ax.tick_params(labelsize=6.5)
    ax.grid(True, alpha=0.18, axis="y", linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.6)
    return fig


def _data_table(rows: List[List[str]], col_widths: List[float]) -> Table:
    t = Table(rows, colWidths=col_widths)
    n = len(rows)
    t.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",   (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 7.5),
        # Body rows
        ("FONTSIZE",     (0, 1), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_ROW]),
        # Grid
        ("LINEBELOW",    (0, 0), (-1, -1), 0.3, RULE_GRAY),
        ("LINEAFTER",    (0, 0), (-1, -1), 0.3, RULE_GRAY),
        # Padding
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3.5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def generate_pdf_report(
    user_inputs: Dict,
    allocation: Dict[str, float],
    glidepath: List[Dict[str, float]],
    ages: List[int],
    p10: np.ndarray,
    p50: np.ndarray,
    p90: np.ndarray,
    target_prob: float,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.40 * inch,
        bottomMargin=0.35 * inch,
    )

    W = letter[0] - 1.0 * inch

    styles = getSampleStyleSheet()
    def S(name="Normal", **kw):
        return ParagraphStyle(f"_s_{name}_{id(kw)}", parent=styles["Normal"], **kw)

    story = []

    # ── 1. HEADER BLOCK ──────────────────────────────────────────────────────
    header_title_st = S(fontSize=17, textColor=WHITE, fontName="Helvetica-Bold",
                        alignment=TA_LEFT, leading=20)
    header_sub_st   = S(fontSize=8,  textColor=colors.HexColor("#A8C4E0"),
                        alignment=TA_LEFT)
    header_name_st  = S(fontSize=9,  textColor=WHITE, fontName="Helvetica-Bold",
                        alignment=TA_RIGHT, leading=12)
    header_date_st  = S(fontSize=7.5, textColor=colors.HexColor("#A8C4E0"),
                        alignment=TA_RIGHT)

    header_left  = [Paragraph("GlideWise", header_title_st),
                    Paragraph("Investment Plan Summary", header_sub_st)]
    header_right = [Paragraph("Parv Arora", header_name_st),
                    Paragraph("Personal Finance Planner", header_date_st)]

    header_inner = Table(
        [[header_left, header_right]],
        colWidths=[W * 0.6, W * 0.4],
    )
    header_inner.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ]))

    header_outer = Table([[header_inner]], colWidths=[W])
    header_outer.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    story.append(header_outer)
    story.append(Spacer(1, 10))

    # ── 2. KEY METRICS STRIP ─────────────────────────────────────────────────
    horizon = user_inputs["retirement_age"] - user_inputs["current_age"]
    prob_color = (colors.HexColor("#27AE60") if target_prob >= 0.70
                  else colors.HexColor("#E67E22") if target_prob >= 0.40
                  else colors.HexColor("#E74C3C"))

    metric_label_st = S(fontSize=6.5, textColor=MID_GRAY, alignment=TA_CENTER)
    metric_value_st = S(fontSize=13,  fontName="Helvetica-Bold",
                        textColor=NAVY, alignment=TA_CENTER, leading=16)
    prob_value_st   = S(fontSize=13,  fontName="Helvetica-Bold",
                        textColor=prob_color, alignment=TA_CENTER, leading=16)

    def metric_cell(label, value, val_style=None):
        vs = val_style or metric_value_st
        return [Paragraph(value, vs), Paragraph(label, metric_label_st)]

    mw = W / 4 - 2
    metrics_row = [
        metric_cell("Investment Horizon",  f"{horizon} yrs"),
        metric_cell("Median Wealth",       format_currency(float(p50[-1]))),
        metric_cell("Target Probability",  f"{target_prob*100:.1f}%", prob_value_st),
        metric_cell("90th Percentile",     format_currency(float(p90[-1]))),
    ]
    metrics_table = Table([metrics_row], colWidths=[mw, mw, mw, mw])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_ROW),
        ("LINEAFTER",    (0, 0), (2, -1),  0.5, RULE_GRAY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",          (0, 0), (-1, -1), 0.4, RULE_GRAY),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 8))

    # ── 3. YOUR PLAN: inputs | allocation + outcomes ─────────────────────────
    section_st = S(fontSize=8, fontName="Helvetica-Bold", textColor=NAVY_LIGHT,
                   spaceBefore=0, spaceAfter=3)

    etf_roles = {
        "US Equity (VTI)":            "Growth – Domestic",
        "International Equity (VXUS)":"Growth – Global",
        "Bonds (BND)":                "Stability – Ballast",
    }

    input_rows = [
        ["Parameter", "Value"],
        ["Current Age",        str(user_inputs["current_age"])],
        ["Retirement Age",     str(user_inputs["retirement_age"])],
        ["Horizon",            f"{horizon} yrs"],
        ["Annual Salary",      f"${user_inputs['annual_salary']:,.0f}"],
        ["Contribution / yr",  f"${user_inputs['annual_contribution']:,.0f}"],
        ["Current Savings",    f"${user_inputs['current_savings']:,.0f}"],
        ["Risk Tolerance",     user_inputs["risk_tolerance"].capitalize()],
        ["Target Wealth",      f"${user_inputs['target_wealth']:,.0f}"],
    ]

    alloc_rows = [["ETF", "Wt", "Role"]]
    for etf, w in allocation.items():
        alloc_rows.append([etf, f"{w*100:.0f}%", etf_roles.get(etf, "")])

    outcome_rows = [
        ["Projected Metric", "Value"],
        ["Median Wealth",        format_currency(float(p50[-1]))],
        ["10th Pctile",          format_currency(float(p10[-1]))],
        ["90th Pctile",          format_currency(float(p90[-1]))],
        ["Target",               format_currency(user_inputs["target_wealth"])],
        ["Prob. of Reaching Target", f"{target_prob*100:.1f}%"],
    ]

    col_L = W * 0.38
    col_R = W * 0.62 - 6

    left_block  = _data_table(input_rows, [col_L * 0.56, col_L * 0.44])

    a_w = col_R
    right_alloc   = _data_table(alloc_rows,   [a_w*0.40, a_w*0.11, a_w*0.49])
    right_outcomes = _data_table(outcome_rows, [a_w*0.60, a_w*0.40])

    right_stack = Table(
        [[right_alloc], [Spacer(1, 5)], [right_outcomes]],
        colWidths=[col_R],
    )
    right_stack.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))

    plan_table = Table(
        [[left_block, right_stack]],
        colWidths=[col_L, col_R],
        hAlign="LEFT",
    )
    plan_table.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(0,-1),  5),
        ("RIGHTPADDING", (1,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))

    story.append(Paragraph("YOUR PLAN", section_st))
    story.append(plan_table)
    story.append(Spacer(1, 8))

    # ── 4. CHARTS ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.4, color=RULE_GRAY, spaceAfter=5))
    story.append(Paragraph("PROJECTED OUTCOMES", section_st))

    chart_w = W / 2 - 4
    img_w = _fig_to_image(
        _wealth_chart(ages, p10, p50, p90,
                      user_inputs["target_wealth"], user_inputs["retirement_age"]),
        chart_w, 1.95 * inch,
    )
    img_g = _fig_to_image(_glidepath_chart(ages, glidepath), chart_w, 1.95 * inch)

    chart_row = Table([[img_w, img_g]], colWidths=[chart_w, chart_w])
    chart_row.setStyle(TableStyle([
        ("ALIGN",        (0,0),(-1,-1), "CENTER"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    story.append(chart_row)

    # ── 5. FOOTER ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.4, color=RULE_GRAY,
                             spaceBefore=6, spaceAfter=4))
    disc_st  = S(fontSize=6.2, textColor=MID_GRAY, alignment=TA_LEFT)
    name_st  = S(fontSize=7,   textColor=MID_GRAY,  alignment=TA_RIGHT,
                 fontName="Helvetica-Bold")

    footer = Table(
        [[
            Paragraph(
                "For educational purposes only. Not financial advice. "
                "Projections use simplified assumptions. Consult a qualified advisor before investing.",
                disc_st,
            ),
            Paragraph("Parv Arora", name_st),
        ]],
        colWidths=[W * 0.80, W * 0.20],
    )
    footer.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    story.append(footer)

    doc.build(story)
    buf.seek(0)
    return buf.read()
