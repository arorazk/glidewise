"""
allocation.py
Defines the 3-ETF universe, return/volatility assumptions, and risk-to-allocation mapping.
"""

from typing import Dict, Tuple

# ---------------------------------------------------------------------------
# ETF universe: expected annual return and annualized volatility
# These are long-run approximations for planning purposes only.
# ---------------------------------------------------------------------------
ETF_PARAMS: Dict[str, Dict[str, float]] = {
    "US Equity (VTI)": {
        "return": 0.075,       # ~7.5% annualized
        "volatility": 0.155,   # ~15.5% annualized std dev
    },
    "International Equity (VXUS)": {
        "return": 0.065,       # ~6.5% annualized
        "volatility": 0.170,   # ~17.0% annualized std dev
    },
    "Bonds (BND)": {
        "return": 0.030,       # ~3.0% annualized
        "volatility": 0.055,   # ~5.5% annualized std dev
    },
}

ETF_ROLES: Dict[str, str] = {
    "US Equity (VTI)": "Growth – Domestic markets",
    "International Equity (VXUS)": "Growth – Global diversification",
    "Bonds (BND)": "Stability – Income & ballast",
}

# Correlation assumptions between assets
# Equity–equity high positive, equity–bond slight negative (diversification)
CORRELATIONS: Dict[Tuple[str, str], float] = {
    ("US Equity (VTI)", "US Equity (VTI)"): 1.00,
    ("US Equity (VTI)", "International Equity (VXUS)"): 0.75,
    ("US Equity (VTI)", "Bonds (BND)"): -0.10,
    ("International Equity (VXUS)", "US Equity (VTI)"): 0.75,
    ("International Equity (VXUS)", "International Equity (VXUS)"): 1.00,
    ("International Equity (VXUS)", "Bonds (BND)"): -0.05,
    ("Bonds (BND)", "US Equity (VTI)"): -0.10,
    ("Bonds (BND)", "International Equity (VXUS)"): -0.05,
    ("Bonds (BND)", "Bonds (BND)"): 1.00,
}

# ---------------------------------------------------------------------------
# Risk-tolerance → initial ETF allocation
# ---------------------------------------------------------------------------
RISK_ALLOCATIONS: Dict[str, Dict[str, float]] = {
    "conservative": {
        "US Equity (VTI)": 0.30,
        "International Equity (VXUS)": 0.10,
        "Bonds (BND)": 0.60,
    },
    "moderate": {
        "US Equity (VTI)": 0.50,
        "International Equity (VXUS)": 0.20,
        "Bonds (BND)": 0.30,
    },
    "aggressive": {
        "US Equity (VTI)": 0.60,
        "International Equity (VXUS)": 0.25,
        "Bonds (BND)": 0.15,
    },
}

# The allocation the glide path converges to at retirement
RETIREMENT_ALLOCATION: Dict[str, float] = {
    "US Equity (VTI)": 0.25,
    "International Equity (VXUS)": 0.10,
    "Bonds (BND)": 0.65,
}


def get_allocation(risk_tolerance: str) -> Dict[str, float]:
    """Return the starting ETF allocation for a given risk tolerance."""
    key = risk_tolerance.lower().strip()
    if key not in RISK_ALLOCATIONS:
        raise ValueError(f"Unknown risk tolerance '{risk_tolerance}'. Choose conservative, moderate, or aggressive.")
    return dict(RISK_ALLOCATIONS[key])


def get_portfolio_stats(weights: Dict[str, float]) -> Tuple[float, float]:
    """
    Compute weighted expected return and portfolio volatility.

    Volatility uses a 2-asset covariance formula extended to 3 assets
    with the pre-defined correlation matrix.

    Returns:
        (expected_return, portfolio_volatility) both as decimals
    """
    etfs = list(weights.keys())

    exp_return = sum(weights[e] * ETF_PARAMS[e]["return"] for e in etfs)

    variance = 0.0
    for e1 in etfs:
        for e2 in etfs:
            corr = CORRELATIONS.get((e1, e2), 0.0)
            variance += (
                weights[e1]
                * weights[e2]
                * ETF_PARAMS[e1]["volatility"]
                * ETF_PARAMS[e2]["volatility"]
                * corr
            )

    return exp_return, variance ** 0.5
