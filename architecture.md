# Project Setup: Intelligent Hedging and Portfolio Allocation Model

## 1. Project Goal
Build a Python repository that acts as a portfolio hedging engine. It must ingest predictions from an external ML model and a current depot state, calculate advanced risk metrics (specifically robust Beta), and execute a Markowitz Mean-Variance optimization to find a portfolio allocation that minimizes variance while guaranteeing an expected return (ROI) of at least 10%.

## 2. Repository Structure
Set up the repository with the following structure:
- `main.py`: Entry point for the pipeline.
- `ingestion.py`: Handles fetching remote JSON data and environment secrets.
- `risk_metrics.py`: Contains custom functions for calculating advanced Beta.
- `optimizer.py`: Contains the SciPy optimization logic.
- `requirements.txt`: Dependencies (e.g., `requests`, `numpy`, `scipy`, `pandas`, `yfinance`).
- `.github/workflows/run_hedger.yml`: GitHub Actions pipeline for automated execution.

## 3. Data Ingestion Specifications
The model must strictly decouple data sources from local files:
- **Predictor Results:** Fetch the latest JSON predictions dynamically via HTTP GET from:
  `https://raw.githubusercontent.com/kleinnconrad/stock-predictor/main/data/processed/full_batch_report.json`
- **Current Depot:** Load the existing portfolio state dynamically from the environment variable `CURRENT_DEPOT_JSON`. The agent must parse this variable using `json.loads()`. Implement error handling to fail fast if the environment variable is missing or malformed.

## 4. Risk Metrics (The Correct Beta Implementation)
Do not use standard Ordinary Least Squares (OLS) Beta. Small-cap Xetra stocks require robust risk adjustments. Implement a Beta calculation pipeline in `risk_metrics.py` that applies the following transformations using historical market data (e.g., via `yfinance`):
1. **Downside Beta:** Calculate covariance strictly on trading days where the benchmark index yielded a negative return. Upside volatility should not penalize the risk score.
2. **Scholes-Williams Adjustment:** To account for illiquidity in smaller Xetra stocks, calculate the Downside Beta using the sum of covariances with the benchmark's previous day, current day, and next day returns.
3. **Blume's Adjustment:** Apply mean reversion to the final calculation to estimate forward-looking Beta: `Adjusted_Beta = (0.67 * Scholes_Williams_Downside_Beta) + (0.33 * 1.0)`.
4. **Dynamic Benchmarking:** Ensure the Beta calculation maps the specific stock to the correct German index (DAX, MDAX, SDAX) based on its market capitalization, rather than defaulting to a global index.

## 5. Optimization Engine (SciPy)
Implement a solver in `optimizer.py` using `scipy.optimize.minimize` (SLSQP method) with the following parameters:
- **Objective:** Minimize portfolio variance (calculated via a covariance matrix derived from the adjusted Betas and expected returns).
- **Constraints:** 
  1. The sum of all asset weights must equal exactly 1.0 (100% capital deployed).
  2. The expected portfolio return must be >= 0.10 (10% ROI target).
- **Bounds:** No short selling of physical stocks (min weight 0.0). Cap individual stock exposure at 30% (max weight 0.3) to enforce diversification. Allow hedging assets (like cash or bond ETFs) to reach 100% (max weight 1.0).

## 6. CI/CD Pipeline
Create a GitHub Actions workflow (`.github/workflows/run_hedger.yml`) that:
- Runs on `workflow_dispatch` and a daily schedule.
- Sets up Python 3.11 and installs `requirements.txt`.
- Injects the repository secret `CURRENT_DEPOT_JSON` into the environment before executing `main.py`.
- Logs the resulting optimal portfolio weights to the standard output.
