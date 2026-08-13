import logging
import pandas as pd
from src.ingestion import fetch_predictions, load_current_depot, load_settings
from src.risk_metrics import calculate_adjusted_beta, calculate_covariance_matrix
from src.optimizer import optimize_portfolio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Portfolio Hedging Engine pipeline...")
    
    settings = load_settings()
    expected_return_up = settings.get("expected_return_up", 0.20)
    expected_return_not_up = settings.get("expected_return_not_up", 0.00)
    hedging_assets = settings.get("hedging_assets", ["CASH"])

    import sys
    # 1. Ingestion
    try:
        predictions_data = fetch_predictions()
        depot = load_current_depot()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

    expected_returns_dict = {}
    
    if "predictions" in predictions_data:
        pred_list = predictions_data["predictions"]
        for item in pred_list:
            symbol = item.get("stock_name")
            pred = item.get("final_prediction")
            if symbol:
                if pred == "UP_FINAL_BUY":
                    expected_returns_dict[symbol] = expected_return_up
    else:
        logger.warning("No 'predictions' key found in fetched data.")

    # Merge depot symbols if not in expected_returns_dict
    for symbol in depot.keys():
        if symbol not in expected_returns_dict:
            expected_returns_dict[symbol] = expected_return_not_up
            
    # Add hedging assets if not present
    for asset in hedging_assets:
        if asset not in expected_returns_dict:
            expected_returns_dict[asset] = 0.0
        
    expected_returns = pd.Series(expected_returns_dict)
    
    # 2. Risk Metrics
    logger.info("Calculating adjusted Betas...")
    adjusted_betas = {}
    for symbol in expected_returns.index:
        beta, mcap, bench = calculate_adjusted_beta(symbol)
        adjusted_betas[symbol] = beta
        logger.info(f"{symbol} - Adjusted Beta: {beta:.4f} (Index: {bench})")
        
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
    from datetime import datetime
    from pathlib import Path
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "settings": settings,
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
