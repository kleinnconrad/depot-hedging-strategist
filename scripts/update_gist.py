import os
import sys
import json
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GIST_DESCRIPTION = "Depot Hedging Strategist - Optimal Weights"
FILENAME = "results.json"
FILE_PATH = "data/results.json"
GITHUB_API_URL = "https://api.github.com"

def main():
    logger.info("Starting Gist updater script...")
    gist_token = os.getenv("GIST_TOKEN")
    
    if not gist_token:
        logger.error("GIST_TOKEN environment variable is not set. Cannot update Gist.")
        sys.exit(1)

    if not os.path.exists(FILE_PATH):
        logger.error(f"Results file not found at {FILE_PATH}. Run main.py first.")
        sys.exit(1)

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    headers = {
        "Authorization": f"Bearer {gist_token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # 1. Search for existing Gist
    logger.info("Searching for existing Gist...")
    response = requests.get(f"{GITHUB_API_URL}/gists", headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to fetch gists: {response.status_code} {response.text}")
        sys.exit(1)

    gists = response.json()
    target_gist_id = None
    for gist in gists:
        if gist.get("description") == GIST_DESCRIPTION:
            target_gist_id = gist.get("id")
            break

    payload = {
        "description": GIST_DESCRIPTION,
        "public": False,
        "files": {
            FILENAME: {
                "content": content
            }
        }
    }

    # 2. Create or Update Gist
    if target_gist_id:
        logger.info(f"Found existing Gist (ID: {target_gist_id}). Updating...")
        update_url = f"{GITHUB_API_URL}/gists/{target_gist_id}"
        patch_response = requests.patch(update_url, headers=headers, json=payload)
        if patch_response.status_code == 200:
            logger.info("Successfully updated Gist.")
        else:
            logger.error(f"Failed to update gist: {patch_response.status_code} {patch_response.text}")
            sys.exit(1)
    else:
        logger.info("No existing Gist found. Creating a new one...")
        post_response = requests.post(f"{GITHUB_API_URL}/gists", headers=headers, json=payload)
        if post_response.status_code == 201:
            logger.info("Successfully created new secret Gist.")
        else:
            logger.error(f"Failed to create gist: {post_response.status_code} {post_response.text}")
            sys.exit(1)

if __name__ == "__main__":
    main()
