# Source Code

## Table of Contents
- [Overview](#overview)
- [Scripts](#scripts)
  - [`ingestion.py`](#ingestionpy)
  - [`risk_metrics.py`](#risk_metricspy)
  - [`optimizer.py`](#optimizerpy)
- [Architecture Diagram](#architecture-diagram)

## Overview

This directory contains the core logic of the application. It consists of modules for data ingestion, risk metric calculation, and portfolio optimization.

## Scripts

### `ingestion.py`

This script handles loading configuration and external data. It provides functions to load settings from the central configuration file (`config/settings.yaml`), fetch the latest expected returns (predictions) from an external HTTP endpoint, and load the current portfolio state from environment variables.

### `risk_metrics.py`

This script calculates risk metrics for the portfolio assets. It retrieves historical market data, determines appropriate benchmark indices based on market capitalization, calculates adjusted downside betas (incorporating Scholes-Williams and Blume's adjustments), and computes a covariance matrix using the Single-Index Model approach.

### `optimizer.py`

This script performs the core portfolio optimization. It executes a Markowitz Mean-Variance optimization process to find an asset allocation that minimizes portfolio variance while adhering to a specified minimum expected return and defined asset weight boundaries.

## Architecture Diagram

The following diagram illustrates the interactions between the modules:

```mermaid
sequenceDiagram
    participant Main as main.py
    participant Ingestion as src/ingestion.py
    participant RiskMetrics as src/risk_metrics.py
    participant Optimizer as src/optimizer.py
    participant External as External APIs (yfinance, HTTP)

    Note over Main,Ingestion: 1. Data Ingestion
    Main->>Ingestion: load_settings()
    Ingestion-->>Main: settings dict
    
    Main->>Ingestion: fetch_predictions()
    Ingestion->>External: HTTP GET
    External-->>Ingestion: JSON predictions
    Ingestion-->>Main: predictions dict
    
    Main->>Ingestion: load_current_depot()
    Ingestion-->>Main: depot dict
    
    Note over Main,RiskMetrics: 2. Risk Metrics Calculation
    loop For each symbol
        Main->>RiskMetrics: calculate_adjusted_beta(symbol)
        RiskMetrics->>External: Fetch Market Data (yf.download)
        External-->>RiskMetrics: Historical Prices
        RiskMetrics-->>Main: beta, mcap, benchmark
    end
    
    Main->>RiskMetrics: calculate_covariance_matrix(betas)
    RiskMetrics-->>Main: cov_matrix
    
    Note over Main,Optimizer: 3. Portfolio Optimization
    Main->>Optimizer: optimize_portfolio(expected_returns, cov_matrix)
    Optimizer-->>Main: optimal_weights
```
