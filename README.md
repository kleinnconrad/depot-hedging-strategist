# Depot Hedging Strategist

This repository contains a portfolio hedging engine. It ingests predictions from an external ML model and a current depot state, calculates advanced risk metrics (specifically robust Beta), and executes a Markowitz Mean-Variance optimization to find a portfolio allocation that minimizes variance while guaranteeing an expected return (ROI) of at least 10%.

## Folder Structure

- `src/`: Core logic of the application.
  - `ingestion.py`: Handles fetching remote JSON data and environment secrets.
  - `risk_metrics.py`: Contains custom functions for calculating advanced Beta.
  - `optimizer.py`: Contains the SciPy optimization logic.
- `config/`: Configuration and parameter files.
  - `settings.yaml`: Centralized configuration file for all user-defined parameters and thresholds.
- `tests/`: Unit and integration tests.
- `.github/workflows/`: GitHub Actions pipelines.
- `main.py`: Entry point for the pipeline.
- `requirements.in`: High-level dependencies.
- `requirements.txt`: Locked project dependencies (auto-generated via `pip-compile`).
- `.python-version`: Specifies the Python version for the project (e.g. 3.11).

## Setup and Execution

1. **Environment:** Execute local scripts using the Conda `base` environment to ensure consistency across local development setups. If you introduce new dependencies, add them to `requirements.in`, then run `pip-compile requirements.in -o requirements.txt` to generate the lockfile, and update your environment:
   ```bash
   conda install pip
   pip install pip-tools
   pip install -r requirements.txt
   ```

2. **Configuration:** All configurable parameters (e.g., target returns, hedging assets, market variance) are located in `config/settings.yaml`. Do not hardcode these in the Python files.

3. **Execution:** 
   For local execution, provide the current depot state as a JSON string via the `CURRENT_DEPOT_JSON` environment variable in a `.env` file at the root of the repository (you can copy `.env.example` to start):
   ```
   CURRENT_DEPOT_JSON='{"UN0.DE": 0.5, "ALV.DE": 0.5}'
   ```
   Then simply run:
   ```bash
   python main.py
   ```
   When executed via GitHub Actions, the `CURRENT_DEPOT_JSON` environment variable is securely injected from the repository's GitHub Secrets.
