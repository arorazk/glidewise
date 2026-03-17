"""
rebalance.py
Utilities for detecting portfolio drift and calculating rebalancing trades.

In GlideWise the glide path already shifts target weights each year.
These helpers show how far a hypothetical portfolio has drifted from its
current-year target and what trades would restore it.
"""

from typing import Dict, Tuple


def current_weights(portfolio_values: Dict[str, float]) -> Dict[str, float]:
    """Convert dollar holdings to percentage weights."""
    total = sum(portfolio_values.values())
    if total == 0:
        return {k: 0.0 for k in portfolio_values}
    return {k: v / total for k, v in portfolio_values.items()}


def calculate_drift(
    portfolio_values: Dict[str, float],
    target_weights: Dict[str, float],
) -> Dict[str, float]:
    """
    Return the drift (actual weight − target weight) for each ETF.

    Positive drift  → over-weight relative to target.
    Negative drift  → under-weight relative to target.
    """
    actual = current_weights(portfolio_values)
    return {etf: actual.get(etf, 0.0) - target_weights[etf] for etf in target_weights}


def needs_rebalance(
    portfolio_values: Dict[str, float],
    target_weights: Dict[str, float],
    threshold: float = 0.05,
) -> bool:
    """
    Return True if any ETF has drifted more than `threshold` (e.g. 5 pp)
    from its target weight.
    """
    drift = calculate_drift(portfolio_values, target_weights)
    return any(abs(d) > threshold for d in drift.values())


def rebalance_portfolio(
    portfolio_values: Dict[str, float],
    target_weights: Dict[str, float],
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Compute the new dollar holdings after rebalancing to target weights
    and the dollar trades required.

    Returns:
        new_values  – {etf: new_dollar_value} after rebalancing
        trades      – {etf: trade_amount} (positive = buy, negative = sell)
    """
    total = sum(portfolio_values.values())
    new_values = {etf: target_weights[etf] * total for etf in target_weights}
    trades = {etf: new_values[etf] - portfolio_values.get(etf, 0.0) for etf in target_weights}
    return new_values, trades


def build_rebalance_schedule(
    ages: list,
    glidepath: list,
    starting_portfolio: Dict[str, float],
    annual_contribution: float,
    assumed_return: float = 0.06,
) -> list:
    """
    Walk forward year-by-year showing drift and rebalancing actions.

    Uses a single fixed assumed_return for illustration (not the full MC).

    Returns:
        List of dicts with keys: age, values_before, drift, rebalanced,
        needs_rebalance, trades.
    """
    schedule = []
    portfolio = dict(starting_portfolio)

    for i, (age, target_alloc) in enumerate(zip(ages[:-1], glidepath[:-1])):
        total_before = sum(portfolio.values())

        # Grow portfolio by assumed_return for illustration
        grown = {etf: v * (1 + assumed_return) for etf, v in portfolio.items()}

        # Add contribution proportionally to current weights
        w = current_weights(grown)
        grown = {etf: v + w.get(etf, 0.0) * annual_contribution for etf, v in grown.items()}

        drift = calculate_drift(grown, target_alloc)
        rebalance_needed = needs_rebalance(grown, target_alloc)
        new_vals, trades = rebalance_portfolio(grown, target_alloc)

        schedule.append({
            "age": age,
            "total_before": total_before,
            "drift": drift,
            "needs_rebalance": rebalance_needed,
            "trades": trades,
        })

        portfolio = new_vals if rebalance_needed else grown

    return schedule
