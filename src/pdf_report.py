"""
pdf_report.py
Generates a professional 1-page PDF summary using ReportLab.
Charts are rendered via matplotlib, converted to PNG in-memory,
and embedded directly into the document.
"""

import io
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
# Color constants
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#1A3A5C")
LIGHT_ROW = colors.HexColor("#EEF2F7")
MID_GRAY = colors.HexColor("#888888")


def _fig_to_image(fig: plt.Figure, width: float, height: float) -> Image:
    """Render a matplotlib figure to a ReportLab Image flowable."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def _make_mini_wealth_chart(
    ages: List[int],
    p10: np.ndarray,
    p50: np.ndarray,
    p90: np.ndarray,
    target_wealth: float,
    retirement_age: int,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6.5, 2.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.fill_between(ages, p10 / 1e6, p90 / 1e6, alpha=0.18, color=PALETTE["blue"])
    ax.plot(ages, p90 / 1e6, color=PALETTE["blue"], linewidth=0.8, linestyle="--", alpha=0.5)
    ax.plot(ages, p10 / 1e6, color=PALETTE["blue"], linewidth=0.8, linestyle="--", alpha=0.5)
    ax.plot(ages, p50 / 1e6, color=PALETTE["blue"], linewidth=2.0, label="Median")
    ax.axhline(target_wealth / 1e6, color=PALETTE["red"], linewidth=1.2, linestyle=":",
               label=f"Target {format_currency(target_wealth)}")
    ax.axvline(retirement_age, color=PALETTE["gray"], linewidth=1.0, linestyle="--", alpha=0.6)

    ax.set_xlabel("Age", fontsize=8)
    ax.set_ylabel("Value ($M)", fontsize=8)
    ax.set_title("Monte Carlo Wealth Paths", fontsize=9, fontweight="bold")
    ax.legend(fontsize=7, framealpha=0.9)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.1f}M"))
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.2, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.5)
    return fig


def _make_mini_glidepath_chart(
    ages: List[int],
    glidepath: List[Dict[str, float]],
) -> plt.Figure:
    import pandas as pd

    etfs = list(glidepath[0].keys())
    chart_colors = [PALETTE["blue"], PALETTE["green"], PALETTE["orange"]]
    data = {etf: [g[etf] * 100 for g in glidepath] for etf in etfs}
    df = pd.DataFrame(data, index=ages)

    fig, ax = plt.subplots(figsize=(6.5, 2.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bottom = np.zeros(len(ages))
    for i, etf in enumerate(etfs):
        short_name = etf.split(" (")[0]
        ax.bar(ages, df[etf], bottom=bottom, label=short_name,
               color=chart_colors[i], alpha=0.88, width=0.85)
        bottom += df[etf].values

    ax.set_xlabel("Age", fontsize=8)
    ax.set_ylabel("Allocation (%)", fontsize=8)
    ax.set_title("Glide Path", fontsize=9, fontweight="bold")
    ax.legend(loc="upper right", fontsize=7, framealpha=0.9)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.set_ylim(0, 112)
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.2, axis="y", linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.5)
    return fig


def _table(data: List[List[str]], col_widths: List[float]) -> Table:
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_ROW]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
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
    """
    Build a one-page PDF summary and return the raw bytes.

    Parameters mirror the data already computed by the Streamlit app so
    nothing needs to be re-calculated here.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
        topMargin=0.40 * inch,
        bottomMargin=0.35 * inch,
    )

    styles = getSampleStyleSheet()
    W = letter[0] - 0.90 * inch   # usable page width

    def style(name: str, **kw) -> ParagraphStyle:
        base = styles.get(name, styles["Normal"])
        return ParagraphStyle(f"_custom_{name}", parent=base, **kw)

    title_st = style("Normal", fontSize=20, textColor=NAVY, fontName="Helvetica-Bold",
                     alignment=TA_CENTER, spaceAfter=2)
    sub_st = style("Normal", fontSize=9, textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=4)
    h2_st = style("Normal", fontSize=10, textColor=NAVY, fontName="Helvetica-Bold",
                  spaceBefore=5, spaceAfter=3)
    disc_st = style("Normal", fontSize=6.5, textColor=MID_GRAY, alignment=TA_CENTER)

    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("GlideWise — Investment Plan Summary", title_st))
    story.append(Paragraph("Personal finance planning tool · Not financial advice", sub_st))
    story.append(HRFlowable(width=W, thickness=1.5, color=NAVY, spaceAfter=6))

    # ── Two-column layout: Inputs | Allocation + Outcomes ───────────────────
    horizon = user_inputs["retirement_age"] - user_inputs["current_age"]

    input_rows = [
        ["Parameter", "Value"],
        ["Current Age", str(user_inputs["current_age"])],
        ["Retirement Age", str(user_inputs["retirement_age"])],
        ["Investment Horizon", f"{horizon} years"],
        ["Annual Salary", f"${user_inputs['annual_salary']:,.0f}"],
        ["Annual Contribution", f"${user_inputs['annual_contribution']:,.0f}"],
        ["Current Savings", f"${user_inputs['current_savings']:,.0f}"],
        ["Risk Tolerance", user_inputs["risk_tolerance"].capitalize()],
        ["Target Wealth", f"${user_inputs['target_wealth']:,.0f}"],
    ]

    etf_roles = {
        "US Equity (VTI)": "Growth – Domestic",
        "International Equity (VXUS)": "Growth – Global",
        "Bonds (BND)": "Stability – Ballast",
    }
    alloc_rows = [["ETF", "Weight", "Role"]]
    for etf, w in allocation.items():
        alloc_rows.append([etf, f"{w*100:.0f}%", etf_roles.get(etf, "")])

    outcome_rows = [
        ["Metric", "Value"],
        ["Median Wealth at Retirement", format_currency(float(p50[-1]))],
        ["10th Pctile (Pessimistic)", format_currency(float(p10[-1]))],
        ["90th Pctile (Optimistic)", format_currency(float(p90[-1]))],
        ["Target Wealth", format_currency(user_inputs["target_wealth"])],
        ["Probability of Reaching Target", f"{target_prob * 100:.1f}%"],
    ]

    col_half = W / 2 - 0.05 * inch
    left_table = _table(input_rows, [col_half * 0.55, col_half * 0.45])
    right_block_alloc = _table(alloc_rows, [col_half * 0.42, col_half * 0.15, col_half * 0.43])
    right_block_outcomes = _table(outcome_rows, [col_half * 0.62, col_half * 0.38])

    two_col = Table(
        [[left_table, [right_block_alloc, Spacer(1, 6), right_block_outcomes]]],
        colWidths=[col_half, col_half + 0.1 * inch],
    )
    two_col.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(two_col)
    story.append(Spacer(1, 6))

    # ── Charts ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=4))
    story.append(Paragraph("Projected Outcomes", h2_st))

    chart_w = W / 2 - 0.1 * inch
    fig_wealth = _make_mini_wealth_chart(ages, p10, p50, p90,
                                         user_inputs["target_wealth"],
                                         user_inputs["retirement_age"])
    fig_glide = _make_mini_glidepath_chart(ages, glidepath)

    img_wealth = _fig_to_image(fig_wealth, chart_w, 1.80 * inch)
    img_glide = _fig_to_image(fig_glide, chart_w, 1.55 * inch)

    chart_table = Table([[img_wealth, img_glide]], colWidths=[chart_w, chart_w])
    chart_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(chart_table)

    # ── Disclaimer ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#CCCCCC"),
                             spaceBefore=6, spaceAfter=4))
    story.append(Paragraph(
        "DISCLAIMER: GlideWise is an educational planning tool and does not constitute financial advice. "
        "Projections are based on simplified return assumptions and log-normal return models. "
        "Past performance is not indicative of future results. "
        "Consult a qualified financial advisor before making investment decisions.",
        disc_st,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
