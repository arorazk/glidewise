"""
utils.py
Shared formatting helpers and matplotlib chart builders.
"""

from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_currency(value: float) -> str:
    """Return a compact human-readable dollar string (e.g. $1.25M, $450K)."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


def format_pct(value: float) -> str:
    """Format a decimal as a percentage string."""
    return f"{value * 100:.1f}%"


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

PALETTE = {
    "blue": "#3B6FD4",
    "green": "#27AE60",
    "red": "#E74C3C",
    "orange": "#E67E22",
    "gray": "#7F8C8D",
    "light_blue": "#AEC6E8",
}


def plot_wealth_simulation(
    ages: List[int],
    p10: np.ndarray,
    p50: np.ndarray,
    p90: np.ndarray,
    target_wealth: float,
    retirement_age: int,
) -> plt.Figure:
    """
    Fan chart showing Monte Carlo wealth bands over the investment horizon.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#F8F9FB")
    ax.set_facecolor("#F8F9FB")

    ax.fill_between(
        ages, p10 / 1e6, p90 / 1e6,
        alpha=0.18, color=PALETTE["blue"], label="10th–90th Percentile Band"
    )
    ax.plot(ages, p90 / 1e6, color=PALETTE["blue"], linewidth=1.0, linestyle="--", alpha=0.55)
    ax.plot(ages, p10 / 1e6, color=PALETTE["blue"], linewidth=1.0, linestyle="--", alpha=0.55)
    ax.plot(ages, p50 / 1e6, color=PALETTE["blue"], linewidth=2.5, label="Median Path")

    ax.axhline(
        target_wealth / 1e6, color=PALETTE["red"], linewidth=1.5,
        linestyle=":", label=f"Target: {format_currency(target_wealth)}"
    )
    ax.axvline(
        retirement_age, color=PALETTE["gray"], linewidth=1.2,
        linestyle="--", alpha=0.7, label=f"Retirement (age {retirement_age})"
    )

    ax.set_xlabel("Age", fontsize=11)
    ax.set_ylabel("Portfolio Value ($M)", fontsize=11)
    ax.set_title("Monte Carlo Wealth Simulation  (1,000 paths)", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9, framealpha=0.9)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.1f}M"))
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def plot_glidepath(
    ages: List[int],
    glidepath: List[Dict[str, float]],
) -> plt.Figure:
    """
    Stacked-area chart showing how the 3-ETF allocation evolves over time.
    """
    etfs = list(glidepath[0].keys())
    colors = [PALETTE["blue"], PALETTE["green"], PALETTE["orange"]]

    data = {etf: [g[etf] * 100 for g in glidepath] for etf in etfs}
    df = pd.DataFrame(data, index=ages)

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#F8F9FB")
    ax.set_facecolor("#F8F9FB")

    bottom = np.zeros(len(ages))
    for i, etf in enumerate(etfs):
        ax.bar(
            ages, df[etf], bottom=bottom,
            label=etf, color=colors[i], alpha=0.88, width=0.85
        )
        bottom += df[etf].values

    ax.set_xlabel("Age", fontsize=11)
    ax.set_ylabel("Allocation (%)", fontsize=11)
    ax.set_title("Portfolio Glide Path Over Time", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.set_ylim(0, 108)
    ax.grid(True, alpha=0.25, axis="y", linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def plot_final_wealth_distribution(
    final_wealth: np.ndarray,
    target_wealth: float,
) -> plt.Figure:
    """
    Histogram of terminal wealth across all simulations with target line.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#F8F9FB")
    ax.set_facecolor("#F8F9FB")

    ax.hist(
        final_wealth / 1e6, bins=60, color=PALETTE["blue"],
        alpha=0.75, edgecolor="white", linewidth=0.4
    )
    ax.axvline(
        target_wealth / 1e6, color=PALETTE["red"], linewidth=2,
        linestyle="--", label=f"Target: {format_currency(target_wealth)}"
    )
    ax.axvline(
        np.median(final_wealth) / 1e6, color=PALETTE["green"], linewidth=2,
        linestyle="-", label=f"Median: {format_currency(float(np.median(final_wealth)))}"
    )

    ax.set_xlabel("Final Wealth ($M)", fontsize=11)
    ax.set_ylabel("Number of Simulations", fontsize=11)
    ax.set_title("Distribution of Terminal Wealth", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9, framealpha=0.9)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.1f}M"))
    ax.grid(True, alpha=0.25, axis="y", linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig
