import os
import json
import requests
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_settings() -> dict:
    """Load settings from config/settings.yaml."""
    settings_path = Path(__file__).resolve().parent.parent / "config" / "settings.yaml"
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load settings from {settings_path}: {e}")
        raise

def fetch_predictions() -> dict:
    """Fetch the latest JSON predictions dynamically via HTTP GET."""
    settings = load_settings()
    predictor_url = settings.get("predictor_url")
    if not predictor_url:
        raise ValueError("predictor_url is missing in settings.yaml")
        
    logger.info(f"Fetching predictions from {predictor_url}")
    response = requests.get(predictor_url)
    response.raise_for_status()
    return response.json()

def load_current_depot() -> dict:
    """Load the existing portfolio state dynamically from the environment variable CURRENT_DEPOT_JSON."""
    # Load environment variables from .env file (useful for local development)
    load_dotenv()
    
    depot_json_str = os.environ.get("CURRENT_DEPOT_JSON")
    if not depot_json_str:
        logger.error("Environment variable CURRENT_DEPOT_JSON is missing.")
        raise ValueError("Environment variable CURRENT_DEPOT_JSON is missing.")
    
    try:
        depot = json.loads(depot_json_str)
        logger.info("Successfully loaded CURRENT_DEPOT_JSON.")
        return depot
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse CURRENT_DEPOT_JSON: {e}")
        raise ValueError(f"CURRENT_DEPOT_JSON is malformed: {e}")
