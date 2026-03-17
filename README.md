---
title: GlideWise
emoji: 📈
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.32.0"
app_file: app.py
pinned: false
---

# GlideWise — Personal Investment Planner

> Takes age, horizon, salary, and risk to output a 3-ETF allocation + glide path with a printable 1-page PDF. Implements rebalancing logic and a simple Monte Carlo to display probability bands for target wealth.

GlideWise is a portfolio-ready Python project that helps individuals plan their investment journey from today to retirement. It maps your risk profile to a three-fund portfolio, visualises how that allocation should evolve over time (the "glide path"), and runs a Monte Carlo simulation to show you the probability distribution of reaching your target wealth.

**This is an educational planning tool — not financial advice.**

---

## Table of Contents
1. [Features](#features)
2. [Project Structure](#project-structure)
3. [How to Run Locally](#how-to-run-locally)
4. [How the Allocation Works](#how-the-allocation-works)
5. [How the Glide Path Works](#how-the-glide-path-works)
6. [Monte Carlo Explanation](#monte-carlo-explanation)
7. [Rebalancing Logic](#rebalancing-logic)
8. [Assumptions & Limitations](#assumptions--limitations)
9. [Disclaimer](#disclaimer)

---

## Features

- **3-ETF Allocation** — Maps conservative / moderate / aggressive risk profiles to a VTI + VXUS + BND portfolio
- **Glide Path** — Linear shift from starting allocation to a conservative retirement allocation over your horizon
- **Monte Carlo Simulation** — 1,000+ simulated portfolio paths; outputs 10th / 50th / 90th percentile bands
- **Target Probability** — Fraction of simulations that reach your retirement wealth goal
- **Rebalancing Schedule** — Year-by-year log showing when the portfolio needs rebalancing and what trades are required
- **Downloadable PDF** — One-page professional summary with embedded charts, generated entirely in-memory

---

## Project Structure

```
GlideWise/
├── app.py               # Streamlit front-end
├── requirements.txt
├── README.md
├── assets/              # Static assets (logos, etc.)
├── outputs/             # Generated PDFs saved here
└── src/
    ├── __init__.py
    ├── allocation.py    # ETF universe, risk-to-allocation mapping
    ├── glidepath.py     # Year-by-year allocation glide path
    ├── simulation.py    # Monte Carlo wealth simulation
    ├── rebalance.py     # Drift detection & rebalancing trades
    ├── pdf_report.py    # ReportLab PDF generation
    └── utils.py         # Formatters, matplotlib chart builders
```

---

## How to Run Locally

### Prerequisites
- Python 3.10+

### Setup

```bash
# 1. Clone or download the repo
git clone https://github.com/yourname/glidewise.git
cd glidewise

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## How the Allocation Works

GlideWise uses a **3-fund portfolio** (popularised by Bogle/Vanguard) consisting of three broad-market ETFs:

| ETF | Ticker | Role |
|-----|--------|------|
| Vanguard Total Stock Market | VTI | US equity growth |
| Vanguard Total International Stock | VXUS | Global diversification |
| Vanguard Total Bond Market | BND | Stability & income |

Each risk profile maps to a fixed starting allocation:

| Risk | VTI | VXUS | BND |
|------|-----|------|-----|
| Conservative | 30% | 10% | 60% |
| Moderate | 50% | 20% | 30% |
| Aggressive | 60% | 25% | 15% |

At retirement the target converges to **25% / 10% / 65%** regardless of starting profile (capital preservation focus).

---

## How the Glide Path Works

The glide path performs a **linear interpolation** between the starting allocation and the retirement allocation over the investment horizon.

For each year `t ∈ [0, horizon]`:

```
weight(etf, t) = start_weight(etf) × (1 - t/horizon)
               + retirement_weight(etf) × (t/horizon)
```

This means:
- At **age = current_age**: 100% starting allocation
- At **age = retirement_age**: 100% retirement (conservative) allocation
- Every year in between: a proportional blend

The result is that equity exposure falls and bond exposure rises steadily — reducing sequence-of-returns risk as retirement approaches.

---

## Monte Carlo Explanation

GlideWise simulates **1,000 independent portfolio paths** (configurable up to 5,000).

### Return model
Each year, annual returns are drawn from a **log-normal distribution**:

```
log_return ~ Normal(μ - ½σ², σ)
```

where `μ` is the portfolio's weighted expected return and `σ` is the portfolio volatility for that year (both evolve with the glide path). The drift adjustment `−½σ²` ensures the expected arithmetic return equals `μ` (Itô correction).

### Year-end wealth
```
W(t+1) = W(t) × exp(log_return) + annual_contribution
```

### Output percentiles
- **10th percentile** — pessimistic scenario
- **50th percentile (median)** — central estimate
- **90th percentile** — optimistic scenario

### Target probability
The fraction of the 1,000 paths whose terminal wealth `W(horizon) ≥ target_wealth`.

---

## Rebalancing Logic

Every year the glide path shifts the target allocation slightly. A rebalance is triggered when **any ETF drifts more than 5 percentage points** from its current-year target.

When triggered, all positions are re-sold/rebought back to exact target weights. New annual contributions are deployed proportionally to the current-year target weights, which helps reduce drift passively.

The rebalance schedule tab shows:
- Age and portfolio value before rebalancing
- Drift for each ETF (actual weight − target weight)
- Whether a rebalance was triggered
- Dollar amount bought/sold per ETF

---

## Assumptions & Limitations

| Assumption | Value / Detail |
|---|---|
| US Equity (VTI) expected return | 7.5% p.a. |
| International Equity (VXUS) expected return | 6.5% p.a. |
| Bonds (BND) expected return | 3.0% p.a. |
| US Equity volatility | 15.5% p.a. |
| International Equity volatility | 17.0% p.a. |
| Bonds volatility | 5.5% p.a. |
| Equity–equity correlation | 0.75 |
| Equity–bond correlation | −0.05 to −0.10 |
| Inflation adjustment | None (nominal returns) |
| Tax treatment | Not modelled |
| Contribution growth | Fixed (no salary-linked increases) |
| Rebalancing costs | Not modelled |
| Return distribution | Log-normal (no fat tails, no skew) |

These are simplifications intended to make the tool educational and easy to reason about. Real markets exhibit fat tails, serial correlation, regime changes, and other complexities not captured here.

---

## Disclaimer

> GlideWise is an **educational planning tool** and does **not** constitute financial advice. All projections are illustrative estimates based on simplified assumptions. Past performance is not indicative of future results. Asset allocation decisions should be made in consultation with a qualified financial advisor.
