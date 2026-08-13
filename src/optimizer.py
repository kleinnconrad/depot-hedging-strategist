import numpy as np
import pandas as pd
from scipy.optimize import minimize
import logging
from src.ingestion import load_settings

logger = logging.getLogger(__name__)

def optimize_portfolio(expected_returns: pd.Series, cov_matrix: pd.DataFrame, hedging_assets: list = None) -> pd.Series:
    """
    Execute a Markowitz Mean-Variance optimization to find a portfolio allocation
    that minimizes variance while guaranteeing an expected return (ROI) of at least 10%.
    """
    settings = load_settings()
    min_portfolio_return = settings.get("min_portfolio_return", 0.10)
    max_stock_weight = settings.get("max_stock_weight", 0.30)
    
    if hedging_assets is None:
        hedging_assets = settings.get("hedging_assets", ["CASH"])
        
    num_assets = len(expected_returns)
    symbols = expected_returns.index.tolist()
    
    # Objective function: Minimize portfolio variance
    def portfolio_variance(weights):
        return weights.T @ cov_matrix.values @ weights
        
    # Constraints
    # 1. Sum of weights = 1.0
    # 2. Expected portfolio return >= min_portfolio_return
    constraints = [
        {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1.0},
        {'type': 'ineq', 'fun': lambda weights: weights.T @ expected_returns.values - min_portfolio_return}
    ]
    
    # Bounds
    # Stocks: [0.0, max_stock_weight]
    # Hedging assets: [0.0, 1.0]
    bounds = []
    for symbol in symbols:
        if symbol in hedging_assets or "CASH" in symbol:
            bounds.append((0.0, 1.0))
        else:
            bounds.append((0.0, max_stock_weight))
            
    # Initial guess: Equal weight distribution
    initial_guess = np.array([1.0 / num_assets] * num_assets)
    
    # Run optimization
    logger.info("Starting SciPy optimization (SLSQP)...")
    result = minimize(
        portfolio_variance,
        initial_guess,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    
    if not result.success:
        logger.warning(f"Optimization failed to find optimal solution: {result.message}")
        
    logger.info("Optimization completed.")
    return pd.Series(result.x, index=symbols)
