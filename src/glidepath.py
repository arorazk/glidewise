"""
glidepath.py
Generates a year-by-year allocation glide path that linearly transitions
from the user's starting allocation to a conservative retirement allocation.
"""

from typing import Dict, List, Tuple

from src.allocation import (
    get_allocation,
    get_portfolio_stats,
    RETIREMENT_ALLOCATION,
)


def generate_glidepath(
    current_age: int,
    retirement_age: int,
    risk_tolerance: str,
) -> Tuple[List[int], List[Dict[str, float]]]:
    """
    Build a linear glide path from starting allocation to retirement allocation.

    The path steps one year at a time. At t=0 (current_age) the portfolio
    matches the risk-tolerance allocation; at t=1 (retirement_age) it matches
    RETIREMENT_ALLOCATION exactly.

    Returns:
        ages       – list of integer ages from current_age to retirement_age
        glidepath  – list of allocation dicts (one per age)
    """
    start_alloc = get_allocation(risk_tolerance)
    end_alloc = RETIREMENT_ALLOCATION
    years = max(retirement_age - current_age, 1)

    ages: List[int] = []
    glidepath: List[Dict[str, float]] = []

    for step in range(years + 1):
        t = step / years          # 0.0 → 1.0
        alloc: Dict[str, float] = {}
        for etf in start_alloc:
            alloc[etf] = start_alloc[etf] * (1 - t) + end_alloc[etf] * t
        ages.append(current_age + step)
        glidepath.append(alloc)

    return ages, glidepath


def get_glidepath_stats(glidepath: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """
    Attach expected_return and volatility to each year in the glide path.

    Returns a list of dicts with keys 'expected_return' and 'volatility'.
    """
    stats: List[Dict[str, float]] = []
    for alloc in glidepath:
        exp_ret, vol = get_portfolio_stats(alloc)
        stats.append({"expected_return": exp_ret, "volatility": vol})
    return stats
