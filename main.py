import logging
import pandas as pd
from src.ingestion import fetch_predictions, load_current_depot, load_settings
from src.risk_metrics import calculate_adjusted_beta, calculate_covariance_matrix, calculate_expected_return
from src.optimizer import optimize_portfolio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Portfolio Hedging Engine pipeline...")
    
    settings = load_settings()
    expected_return_up = settings.get("expected_return_up", 0.10)
    hedging_assets = settings.get("hedging_assets", ["CASH"])

    import sys
    # 1. Ingestion
    try:
        predictions_data = fetch_predictions()
        depot = load_current_depot()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

    # 2. Risk Metrics & Expected Returns
    logger.info("Calculating adjusted Betas and Expected Returns...")
    
    symbols_to_process = set(depot.keys())
    predicted_up_symbols = set()
    
    if "predictions" in predictions_data:
        for item in predictions_data["predictions"]:
            symbol = item.get("stock_name")
            pred = item.get("final_prediction")
            if symbol and pred == "UP_FINAL_BUY":
                symbols_to_process.add(symbol)
                predicted_up_symbols.add(symbol)
    else:
        logger.warning("No 'predictions' key found in fetched data.")
        
    for asset in hedging_assets:
        symbols_to_process.add(asset)
        
    adjusted_betas = {}
    expected_returns_dict = {}
    
    for symbol in symbols_to_process:
        beta, mcap, bench = calculate_adjusted_beta(symbol)
        adjusted_betas[symbol] = beta
        logger.info(f"{symbol} - Adjusted Beta: {beta:.4f} (Index: {bench})")
        
        if symbol in predicted_up_symbols:
            expected_returns_dict[symbol] = expected_return_up
        elif symbol == "CASH":
            expected_returns_dict[symbol] = settings.get("cash_beta", -0.025)
            logger.info(f"{symbol} - Expected Return (Inflation Adjusted): {expected_returns_dict[symbol]:.4%}")
        else:
            expected_returns_dict[symbol] = calculate_expected_return(beta)
            logger.info(f"{symbol} - CAPM Expected Return: {expected_returns_dict[symbol]:.4%}")
            
    expected_returns = pd.Series(expected_returns_dict)
        
    logger.info("Calculating Covariance Matrix...")
    cov_matrix = calculate_covariance_matrix(adjusted_betas)
    
    # 3. Optimization
    logger.info("Running optimization...")
    optimal_weights = optimize_portfolio(expected_returns, cov_matrix, hedging_assets)
    
    # 4. Output Results
    logger.info("=== Optimal Portfolio Weights ===")
    print("\nOptimal Portfolio Weights:")
    for symbol, weight in optimal_weights.items():
        if weight > 0.001:  # Only print non-zero weights
            print(f"{symbol}: {weight:.2%}")
            
    total_weight = optimal_weights.sum()
    print(f"\nTotal Weight: {total_weight:.2%}")
    expected_portfolio_return = optimal_weights.T @ expected_returns.values
    print(f"Expected Portfolio Return: {expected_portfolio_return:.2%}")

    # 5. Save Results to JSON
    import json
    from datetime import datetime, timezone
    from pathlib import Path
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "settings": settings,
        "asset_expected_returns": expected_returns.to_dict(),
        "weights": optimal_weights.to_dict(),
        "total_weight": float(total_weight),
        "expected_return": float(expected_portfolio_return)
    }
    
    results_path = data_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Results successfully saved to {results_path}")

if __name__ == "__main__":
    main()
