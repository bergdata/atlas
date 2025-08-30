import requests
import sys
import datetime
import pandas as pd
import numpy as np
import os
import logging
from config import ENVIRONMENT
from token_manager import TokenManager
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def make_api_request():
    """Make API request using token manager"""
    token_manager = TokenManager()
    
    if ENVIRONMENT == "production":
        url = "https://atlas-api.rickshawnetwork.com/api/crm/task"
    else:
        url = "https://staging-atlas-api.rickshawnetwork.com/api/crm/task"

    # Get current token (without incrementing usage)
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {access_token}"
    }

    # Calculate dynamic visibleTo date (now, UTC, ISO format)
    now = datetime.datetime.now(datetime.UTC)
    visible_to = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "destinationIds": "53", #["111", "93"],
        "entityId": "1",
        "visibleTo": visible_to,
        "done": "false",
        "skipCount": "0",
        "maxResultCount": "5",#0",
        "sorting": "deadlineDate desc"
    }

    response = requests.get(url, headers=headers, params=params, timeout=100)
    response.raise_for_status()
    return response.json()

# Initialize token manager
token_manager = TokenManager()

# Get initial access token
if len(sys.argv) > 1:
    access_token = sys.argv[1].strip()
    # Add the command line token to the manager (this will clear all old tokens)
    token_manager.add_token(access_token)
else:
    # Try to get existing token, generate new one if none exists
    access_token = token_manager.get_active_token_value()
    if not access_token:
        access_token = token_manager._generate_new_token()

if not access_token:
    logger.error("No access token provided and no active token found.")
    logger.error("Please run 'python access_token.py' to generate a new token.")
    sys.exit(1)

logger.info("\n✅ CRM Task Search API Response:\n")

# Make API request with automatic token refresh
data = token_manager.api_request_with_token_refresh(make_api_request)

# If the response contains a list of tasks under a key like 'items', extract it
if 'items' in data:
    data_list = data['items']
else:
    data_list = data  # fallback if the response is a list

df = pd.DataFrame(data_list)

# Function to truncate strings to 40 characters
def truncate_string(value, max_length=250):
    # Handle empty arrays and other special cases
    try:
        if hasattr(value, 'size') and value.size == 0:
            return value
        if isinstance(value, (list, np.ndarray)) and len(value) == 0:
            return value
        if pd.isna(value) or value is None:
            return value
    except (ValueError, TypeError):
        # If checking for NaN fails, just proceed with string conversion
        pass
    
    str_value = str(value)
    return str_value[:max_length] if len(str_value) > max_length else str_value

# Apply truncation to all columns
for column in df.columns:
    df[column] = df[column].apply(truncate_string)

# Print the final result (only once)
logger.info(df)

# Create output directory if it doesn't exist
output_dir = "output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save JSON to output folder
output_file = os.path.join(output_dir, "crm_task.json")
# Convert DataFrame to list of dictionaries for JSON serialization
json_data = df.to_dict('records')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)
logger.info(f"\n📁 JSON saved to: {output_file}")
logger.info(f"📊 Final dataset contains {len(json_data)} records")