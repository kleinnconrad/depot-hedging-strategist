import numpy as np
import pandas as pd
from scipy.optimize import minimize
import logging
from src.ingestion import load_settings

logger = logging.getLogger(__name__)

def optimize_portfolio(expected_returns: pd.Series, cov_matrix: pd.DataFrame, hedging_assets: list = None) -> pd.Series:
    """
    Execute an optimization to find a portfolio allocation that maximizes expected 
    return while guaranteeing a minimum return under regular circumstances (risk-adjusted).
    """
    settings = load_settings()
    min_portfolio_return = settings.get("min_portfolio_return", 0.10)
    max_stock_weight = settings.get("max_stock_weight", 0.30)
    z_score = settings.get("regular_circumstance_z_score", 1.0)
    
    if hedging_assets is None:
        hedging_assets = settings.get("hedging_assets", ["CASH"])
        
    num_assets = len(expected_returns)
    symbols = expected_returns.index.tolist()
    
    # Objective function: Maximize portfolio return (Minimize negative return)
    def negative_expected_return(weights):
        return -(weights.T @ expected_returns.values)
        
    # Risk-adjusted return constraint
    def risk_adjusted_return_constraint(weights):
        expected_return = weights.T @ expected_returns.values
        variance = weights.T @ cov_matrix.values @ weights
        # Ensure variance is not strictly negative due to floating point inaccuracies
        std_dev = np.sqrt(max(variance, 0.0))
        return expected_return - (z_score * std_dev) - min_portfolio_return

    # Constraints
    # 1. Sum of weights = 1.0
    # 2. Risk-adjusted return >= min_portfolio_return
    constraints = [
        {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1.0},
        {'type': 'ineq', 'fun': risk_adjusted_return_constraint}
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
        negative_expected_return,
        initial_guess,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000}
    )
    
    if not result.success:
        logger.warning(f"Optimization failed to find optimal solution: {result.message}")
        
    logger.info("Optimization completed.")
    return pd.Series(result.x, index=symbols)
