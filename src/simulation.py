"""
simulation.py
Monte Carlo simulation of portfolio growth over the investment horizon.

Each simulation path evolves the portfolio year-by-year using log-normal
returns drawn from the glide-path's time-varying expected return and volatility.
Annual contributions are added at the end of each year.
"""

from typing import Dict, List, Tuple

import numpy as np


def run_monte_carlo(
    current_savings: float,
    annual_contribution: float,
    glidepath_stats: List[Dict[str, float]],
    n_simulations: int = 1_000,
    seed: int = 42,
) -> np.ndarray:
    """
    Simulate portfolio wealth over n_years.

    Args:
        current_savings:      Starting portfolio value ($).
        annual_contribution:  Fixed dollar amount added every year.
        glidepath_stats:      List of {expected_return, volatility} dicts,
                              one per year of the horizon.
        n_simulations:        Number of Monte Carlo paths.
        seed:                 RNG seed for reproducibility.

    Returns:
        wealth  – np.ndarray of shape (n_simulations, n_years + 1)
                  Column 0 is the starting value; column k is wealth after year k.
    """
    rng = np.random.default_rng(seed)
    n_years = len(glidepath_stats)

    wealth = np.zeros((n_simulations, n_years + 1))
    wealth[:, 0] = current_savings

    for year_idx, stats in enumerate(glidepath_stats):
        mu = stats["expected_return"]
        sigma = stats["volatility"]

        # Draw log-normal annual returns; drift adjustment keeps E[R] = mu
        log_returns = rng.normal(mu - 0.5 * sigma ** 2, sigma, n_simulations)

        wealth[:, year_idx + 1] = (
            wealth[:, year_idx] * np.exp(log_returns) + annual_contribution
        )

    return wealth


def get_percentiles(
    wealth: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract the 10th, 50th (median), and 90th percentile wealth paths.

    Returns:
        (p10, p50, p90)  – each an array of length n_years + 1
    """
    p10 = np.percentile(wealth, 10, axis=0)
    p50 = np.percentile(wealth, 50, axis=0)
    p90 = np.percentile(wealth, 90, axis=0)
    return p10, p50, p90


def probability_of_reaching_target(wealth: np.ndarray, target: float) -> float:
    """
    Fraction of simulation paths whose final portfolio value meets or exceeds `target`.

    Returns:
        Probability as a float in [0, 1].
    """
    return float(np.mean(wealth[:, -1] >= target))
