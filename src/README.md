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
graph TD
    Settings["config/settings.yaml"] -.-> Ingestion
    
    subgraph src["src directory"]
        Ingestion["ingestion.py"]
        RiskMetrics["risk_metrics.py"]
        Optimizer["optimizer.py"]
    end
    
    Ingestion -->|Provides load_settings()| RiskMetrics
    Ingestion -->|Provides load_settings()| Optimizer
    
    RiskMetrics -->|Calculates Covariance Matrix| Optimizer
    
    Optimizer -->|Produces| Allocation["Optimal Portfolio Allocation"]
```
