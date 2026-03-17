"""
app.py – GlideWise: Personal Investment Planning App
=====================================================
Run with:
    streamlit run app.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from src.allocation import get_allocation, get_portfolio_stats, ETF_PARAMS, ETF_ROLES
from src.glidepath import generate_glidepath, get_glidepath_stats
from src.simulation import run_monte_carlo, get_percentiles, probability_of_reaching_target
from src.rebalance import build_rebalance_schedule, calculate_drift
from src.pdf_report import generate_pdf_report
from src.utils import (
    format_currency,
    format_pct,
    plot_wealth_simulation,
    plot_glidepath,
    plot_final_wealth_distribution,
)


# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GlideWise — Investment Planner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Hide GitHub link and footer only ─────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
a[href*="github"] {display: none !important;}
/* Desktop only: lock sidebar open */
@media (min-width: 768px) {
    [data-testid="stSidebarCollapseButton"] {display: none !important;}
}
</style>
""", unsafe_allow_html=True)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Metric card */
        [data-testid="stMetric"] {
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 12px 16px;
        }

        /* Tab styling */
        button[data-baseweb="tab"] { font-weight: 600; font-size: 14px; }

        /* Probability badge */
        .prob-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 24px;
            font-weight: 700;
            color: white;
        }

        /* Sidebar section label */
        .sidebar-section {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            opacity: 0.55;
            margin: 14px 0 4px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Sidebar inputs ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 GlideWise")
    st.caption("Personal Investment Planner")
    st.divider()

    st.markdown('<p class="sidebar-section">👤 Personal</p>', unsafe_allow_html=True)
    current_age = st.slider("Current Age", 18, 70, 30, step=1)
    retirement_age = st.slider("Retirement Age", current_age + 5, 80, 65, step=1)
    st.caption(f"Investment horizon: **{retirement_age - current_age} years**")

    st.markdown('<p class="sidebar-section">💰 Finances</p>', unsafe_allow_html=True)
    annual_salary = st.number_input(
        "Annual Salary ($)", min_value=0, max_value=1_000_000,
        value=90_000, step=5_000, format="%d"
    )
    annual_contribution = st.number_input(
        "Annual Contribution ($)", min_value=0, max_value=500_000,
        value=15_000, step=1_000, format="%d"
    )
    current_savings = st.number_input(
        "Current Savings ($)", min_value=0, max_value=10_000_000,
        value=50_000, step=5_000, format="%d"
    )

    st.markdown('<p class="sidebar-section">🎯 Goals</p>', unsafe_allow_html=True)
    risk_tolerance = st.selectbox(
        "Risk Tolerance",
        ["Conservative", "Moderate", "Aggressive"],
        index=1,
    )
    target_wealth = st.number_input(
        "Target Wealth at Retirement ($)", min_value=100_000, max_value=20_000_000,
        value=2_000_000, step=100_000, format="%d"
    )

    st.markdown('<p class="sidebar-section">⚙️ Simulation</p>', unsafe_allow_html=True)
    n_sims = st.select_slider(
        "Monte Carlo Paths", options=[500, 1_000, 2_000, 5_000], value=1_000
    )

    st.divider()
    st.caption(
        "⚠️ Educational tool only · Not financial advice"
    )


# ── Core calculations ────────────────────────────────────────────────────────
horizon = retirement_age - current_age
risk_key = risk_tolerance.lower()

allocation = get_allocation(risk_key)
exp_ret, port_vol = get_portfolio_stats(allocation)
ages, glidepath = generate_glidepath(current_age, retirement_age, risk_key)
# Pass glidepath[:-1] stats: the last allocation is the retirement target;
# no additional growth year occurs after it. This ensures wealth has exactly
# len(ages) columns (one value per age, from current_age to retirement_age).
glidepath_stats = get_glidepath_stats(glidepath[:-1])

wealth = run_monte_carlo(
    current_savings, annual_contribution, glidepath_stats,
    n_simulations=n_sims, seed=42
)
p10, p50, p90 = get_percentiles(wealth)
target_prob = probability_of_reaching_target(wealth, target_wealth)

rebalance_schedule = build_rebalance_schedule(
    ages, glidepath,
    {etf: allocation[etf] * current_savings for etf in allocation},
    annual_contribution,
    assumed_return=exp_ret,
)


# ── Header ───────────────────────────────────────────────────────────────────
col_title, col_author = st.columns([3, 1])
with col_title:
    st.markdown("# 📈 GlideWise")
    st.markdown(
        "**Personal Investment Planner** · 3-ETF allocation · Glide path · Monte Carlo simulation"
    )
with col_author:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("Built by **Parv Arora**")
st.markdown("---")


# ── Summary metric cards ──────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

prob_color = (
    "#27AE60" if target_prob >= 0.70
    else "#E67E22" if target_prob >= 0.40
    else "#E74C3C"
)

c1.metric("Investment Horizon", f"{horizon} yrs")
c2.metric("Median Wealth", format_currency(float(p50[-1])))
c3.metric("10th Percentile", format_currency(float(p10[-1])))
c4.metric("90th Percentile", format_currency(float(p90[-1])))
c5.metric(
    "Target Probability",
    f"{target_prob * 100:.1f}%",
    delta=f"{'On track' if target_prob >= 0.5 else 'Below target'}",
    delta_color="normal" if target_prob >= 0.5 else "inverse",
)

st.markdown("")


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Wealth Projection", "🧭 Glide Path", "⚖️ Rebalancing", "📄 PDF Report"]
)


# ────────────────────────────────────────────────────────────────────────────
# TAB 1 – Wealth Projection
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Monte Carlo Wealth Simulation")
        fig_wealth = plot_wealth_simulation(ages, p10, p50, p90, target_wealth, retirement_age)
        st.pyplot(fig_wealth, use_container_width=True)

        st.subheader("Terminal Wealth Distribution")
        fig_dist = plot_final_wealth_distribution(wealth[:, -1], target_wealth)
        st.pyplot(fig_dist, use_container_width=True)

    with col_right:
        st.subheader("Allocation at a Glance")

        alloc_data = {
            "ETF": list(allocation.keys()),
            "Weight": [f"{v*100:.0f}%" for v in allocation.values()],
            "Role": [ETF_ROLES[e] for e in allocation],
        }
        st.dataframe(
            pd.DataFrame(alloc_data).set_index("ETF"),
            use_container_width=True,
            height=145,
        )

        st.markdown("")
        st.subheader("Portfolio Assumptions")
        param_rows = []
        for etf, params in ETF_PARAMS.items():
            param_rows.append({
                "ETF": etf,
                "Exp. Return": f"{params['return']*100:.1f}%",
                "Volatility": f"{params['volatility']*100:.1f}%",
            })
        st.dataframe(
            pd.DataFrame(param_rows).set_index("ETF"),
            use_container_width=True,
            height=145,
        )

        st.markdown("")
        st.subheader("Starting Portfolio Stats")
        st.markdown(
            f"""
            | Metric | Value |
            |---|---|
            | Expected Return | **{exp_ret*100:.2f}%** |
            | Portfolio Volatility | **{port_vol*100:.2f}%** |
            | Contribution Rate | **{(annual_contribution / max(annual_salary, 1))*100:.1f}%** |
            | Years to Retirement | **{horizon}** |
            """
        )

        # Probability badge
        st.markdown("")
        st.subheader("Target Wealth Probability")
        st.markdown(
            f"""
            <div style="text-align:center; margin-top:8px;">
                <div class="prob-badge" style="background:{prob_color}; font-size:36px; padding:12px 28px;">
                    {target_prob*100:.1f}%
                </div>
                <p style="color:#5A6A7E; font-size:13px; margin-top:8px;">
                    of {n_sims:,} simulations reached<br>
                    <strong>{format_currency(target_wealth)}</strong> by retirement
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 2 – Glide Path
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("ETF Allocation Glide Path")
        fig_glide = plot_glidepath(ages, glidepath)
        st.pyplot(fig_glide, use_container_width=True)

    with col_right:
        st.subheader("How the Glide Path Works")
        st.markdown(
            f"""
            Starting from your **{risk_tolerance}** profile, the portfolio
            linearly shifts toward a conservative allocation over your **{horizon}-year** horizon.

            **Starting allocation:**
            """
        )
        for etf, w in allocation.items():
            st.markdown(f"- {etf}: **{w*100:.0f}%**")

        st.markdown("**Retirement allocation:**")
        from src.allocation import RETIREMENT_ALLOCATION
        for etf, w in RETIREMENT_ALLOCATION.items():
            st.markdown(f"- {etf}: **{w*100:.0f}%**")

    # Glide path data table
    st.markdown("---")
    st.subheader("Year-by-Year Allocation Table")
    gp_df = pd.DataFrame(glidepath, index=ages)
    gp_df.index.name = "Age"
    gp_df.columns = [c.split(" (")[0] for c in gp_df.columns]
    gp_df = (gp_df * 100).round(1)

    # Show every 5 years
    step = max(1, len(ages) // 20)
    st.dataframe(
        gp_df.iloc[::step].style.format("{:.1f}%").background_gradient(
            subset=["US Equity", "International Equity", "Bonds"],
            cmap="RdYlGn_r",
        ),
        use_container_width=True,
    )

    # Expected return and volatility over the glide path
    st.markdown("---")
    st.subheader("Portfolio Risk/Return Through Time")
    stats_df = pd.DataFrame(glidepath_stats, index=ages[:-1])
    stats_df.index.name = "Age"
    stats_df["expected_return"] = (stats_df["expected_return"] * 100).round(2)
    stats_df["volatility"] = (stats_df["volatility"] * 100).round(2)
    stats_df.columns = ["Expected Return (%)", "Volatility (%)"]

    st.line_chart(stats_df.iloc[::step], use_container_width=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 3 – Rebalancing
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Annual Rebalancing Schedule")
    st.markdown(
        """
        The table below shows a simulated year-by-year rebalancing log using your
        starting allocation and a simplified fixed-return assumption.
        A rebalance is triggered when any ETF drifts more than **5 percentage points**
        from its target weight.
        """
    )

    if rebalance_schedule:
        rows = []
        for entry in rebalance_schedule[:min(len(rebalance_schedule), 30)]:
            drift_str = ", ".join(
                f"{etf.split(' (')[0]}: {d*100:+.1f}pp"
                for etf, d in entry["drift"].items()
            )
            trades_str = ", ".join(
                f"{etf.split(' (')[0]}: {format_currency(abs(v))} {'buy' if v > 0 else 'sell'}"
                for etf, v in entry["trades"].items()
                if abs(v) > 1
            )
            rows.append({
                "Age": entry["age"],
                "Portfolio Value": format_currency(entry["total_before"]),
                "Rebalance?": "✅ Yes" if entry["needs_rebalance"] else "—",
                "Drift Summary": drift_str,
                "Trades": trades_str if entry["needs_rebalance"] else "None",
            })

        df_rebal = pd.DataFrame(rows).set_index("Age")
        st.dataframe(df_rebal, use_container_width=True, height=420)
    else:
        st.info("No rebalancing data available for this horizon.")

    st.markdown("---")
    st.subheader("Rebalancing Logic Explained")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            **What triggers a rebalance?**

            Any ETF position that drifts more than ±5 percentage points
            from its current-year target weight triggers a full rebalance.

            **What happens during a rebalance?**

            All ETF positions are sold/bought back to the exact target weights
            for that year, using the portfolio's total current value.
            """
        )
    with col_b:
        st.markdown(
            """
            **Why does the target change each year?**

            The glide path shifts target weights annually — becoming more
            conservative as you approach retirement. So even without market
            drift, the "correct" allocation evolves every year.

            **Contribution allocation:**

            New contributions are deployed proportionally to the current
            target weights, helping the portfolio stay on track passively.
            """
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 4 – PDF Report
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Generate Your 1-Page PDF Summary")
    st.markdown(
        """
        Click the button below to generate and download a professional one-page
        PDF summary of your GlideWise plan. The report includes:

        - Your inputs and 3-ETF allocation
        - Glide path and wealth projection charts
        - Target wealth probability and projected outcomes
        - Important disclaimer
        """
    )

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("Building your PDF…"):
                user_inputs = {
                    "current_age": current_age,
                    "retirement_age": retirement_age,
                    "annual_salary": annual_salary,
                    "annual_contribution": annual_contribution,
                    "current_savings": current_savings,
                    "risk_tolerance": risk_tolerance,
                    "target_wealth": target_wealth,
                }
                pdf_bytes = generate_pdf_report(
                    user_inputs=user_inputs,
                    allocation=allocation,
                    glidepath=glidepath,
                    ages=ages,
                    p10=p10,
                    p50=p50,
                    p90=p90,
                    target_prob=target_prob,
                )

                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"glidewise_plan_age{current_age}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    with col_info:
        st.info(
            "The PDF is generated entirely in-memory using ReportLab — "
            "no data ever leaves your machine."
        )
