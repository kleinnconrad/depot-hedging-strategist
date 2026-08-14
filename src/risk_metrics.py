import yfinance as yf
import pandas as pd
import numpy as np
import logging
from src.ingestion import load_settings

logger = logging.getLogger(__name__)

def get_benchmark_symbol(market_cap: float) -> str:
    """Map market capitalization to the correct German index."""
    if market_cap is None:
        return "^SDAXI" # Default to SDAX if unknown
    
    if market_cap > 10_000_000_000:
        return "^GDAXI"  # DAX
    elif market_cap > 2_000_000_000:
        return "^MDAXI"  # MDAX
    else:
        return "^SDAXI"  # SDAX

def calculate_adjusted_beta(stock_symbol: str) -> tuple[float, float, str]:
    """
    Calculate the robust Beta for a stock.
    Returns (Adjusted_Beta, Market_Cap, Benchmark_Symbol)
    """
    try:
        if stock_symbol == "CASH":
            settings = load_settings()
            cash_beta = settings.get("cash_beta", 0.025)
            return cash_beta, 0.0, "NONE"
            
        ticker = yf.Ticker(stock_symbol)
        info = ticker.info
        market_cap = info.get("marketCap", None)
        
        bench_symbol = get_benchmark_symbol(market_cap)
        
        # Fetch historical data
        stock_data = yf.download(stock_symbol, period="2y", interval="1d", progress=False)["Close"].squeeze()
        bench_data = yf.download(bench_symbol, period="2y", interval="1d", progress=False)["Close"].squeeze()
        
        # Check if the data is a Series and is not empty. Sometimes yfinance returns empty for invalid tickers
        if not isinstance(stock_data, pd.Series) or stock_data.empty:
            logger.warning(f"Could not fetch sufficient stock data for {stock_symbol}.")
            return 1.0, market_cap, bench_symbol

        if not isinstance(bench_data, pd.Series) or bench_data.empty:
            logger.warning(f"Could not fetch sufficient benchmark data for {bench_symbol}.")
            return 1.0, market_cap, bench_symbol
            
        df = pd.DataFrame({'stock': stock_data, 'bench': bench_data}).pct_change(fill_method=None).dropna()
        
        df['bench_t_minus_1'] = df['bench'].shift(1)
        df['bench_t_plus_1'] = df['bench'].shift(-1)
        
        # Filter for Downside Beta (only days where benchmark is negative)
        downside_df = df[df['bench'] < 0].dropna()
        
        if len(downside_df) < 10:
            logger.warning(f"Not enough downside days for {stock_symbol}. Returning default Beta 1.0.")
            return 1.0, market_cap, bench_symbol
            
        # Scholes-Williams Adjustment (Sum of covariances / Benchmark variance)
        cov_t = downside_df['stock'].cov(downside_df['bench'])
        cov_t_minus_1 = downside_df['stock'].cov(downside_df['bench_t_minus_1'])
        cov_t_plus_1 = downside_df['stock'].cov(downside_df['bench_t_plus_1'])
        
        var_bench = downside_df['bench'].var()
        
        if var_bench == 0:
            sw_downside_beta = 1.0
        else:
            sw_downside_beta = (cov_t_minus_1 + cov_t + cov_t_plus_1) / var_bench
            
        # Blume's Adjustment
        adjusted_beta = (0.67 * sw_downside_beta) + (0.33 * 1.0)
        
        return adjusted_beta, market_cap, bench_symbol
        
    except Exception as e:
        logger.error(f"Error calculating beta for {stock_symbol}: {e}")
        return 1.0, None, "^SDAXI"

def calculate_covariance_matrix(adjusted_betas: dict) -> pd.DataFrame:
    """
    Calculate covariance matrix using the Single-Index Model approach.
    Loads market_variance and idiosyncratic_variance from settings.
    """
    settings = load_settings()
    market_variance = settings.get("market_variance", 0.04)
    idio_variance = settings.get("idiosyncratic_variance", 0.02)
    
    symbols = list(adjusted_betas.keys())
    cov_matrix = pd.DataFrame(index=symbols, columns=symbols, dtype=float)
    
    for i in symbols:
        for j in symbols:
            if i == j:
                # Diagonal: Variance of the stock.
                if i == "CASH":
                    cov_matrix.loc[i, j] = (adjusted_betas[i] ** 2) * market_variance
                else:
                    cov_matrix.loc[i, j] = (adjusted_betas[i] ** 2) * market_variance + idio_variance
            else:
                # Off-diagonal: Covariance
                cov_matrix.loc[i, j] = adjusted_betas[i] * adjusted_betas[j] * market_variance
                
    return cov_matrix
