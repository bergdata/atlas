import requests
import sys
import datetime
import pandas as pd
import numpy as np
import os
import logging
import json
import argparse
from config import ENVIRONMENT, DESTINATION_CONFIGS
from token_manager import TokenManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def make_api_request(skip_count=0, destination_ids=None):
    """Make API request using token manager with pagination support"""
    token_manager = TokenManager()
    
    if ENVIRONMENT == "production":
        url = "https://atlas-api.rickshawnetwork.com/api/crm/mail/search"
    else:
        url = "https://staging-atlas-api.rickshawnetwork.com/api/crm/mail/search"

    logger.info(f"Using environment: {ENVIRONMENT}")

    # Get current token (without incrementing usage)
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "application/json,text/html,application/xhtml+xml,application/xml,text/*;q=0.9, image/*;q=0.8, */*;q=0.7",
        "Authorization": f"Bearer {access_token}"
    }

    # Calculate dynamic dates using timezone-aware UTC
    now = datetime.datetime.now(datetime.UTC)
    # Set end_date to the final hour of the current day (23:59:59)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Set start_date to 60 days before the current date
    start_date = (now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info(f"Start date: {start_date}")
    logger.info(f"End date: {end_date}")

    # Use provided destination_ids or default to Vietnam destination configuration
    if destination_ids is None:
        # Get Vietnam destination configuration
        vietnam_config = DESTINATION_CONFIGS["vietnam"]
        destination_ids = vietnam_config["destination_ids"]
    
    logger.info(f"Using destination IDs: {destination_ids}")

    params = {
        "sorting": "sentDateTime desc",
        "destinationsId": destination_ids,
        "skipCount": str(skip_count),
        "maxResultCount": "100",
        "entityId": "1",
        "type": "0",
        "done": "false",
        "draft": "false",
        "trash": "false",
        "startDate": start_date,
        "endDate": end_date
    }

    response = requests.get(url, headers=headers, params=params, timeout=100)
    response.raise_for_status()
    return response.json()

def fetch_all_mail_data(destination_ids=None):
    """Fetch all mail data using pagination"""
    # Create token manager instance
    token_manager = TokenManager()
    
    all_items = []
    skip_count = 0
    total_count = None
    
    logger.info("Starting to fetch all mail data with pagination...")
    
    while True:
        logger.info(f" Fetching page with skipCount: {skip_count}")
        
        # Make API request with automatic token refresh
        data = token_manager.api_request_with_token_refresh(lambda: make_api_request(skip_count, destination_ids))
        
        # Get total count from first response
        if total_count is None:
            total_count = data.get('totalCount', 0)
            logger.info(f"Total items to fetch: {total_count}")
        
        items = data.get('items', [])
        if not items:
            logger.info("No more items to fetch")
            break
            
        all_items.extend(items)
        logger.info(f" Fetched {len(items)} items (Total so far: {len(all_items)}/{total_count})")
        
        # Check if we've fetched all items
        if len(all_items) >= total_count:
            logger.info("All items fetched successfully")
            break
            
        # Move to next page
        skip_count += len(items)
        
        # Safety check to prevent infinite loops
        if skip_count > total_count:
            logger.warning("Safety check triggered - stopping pagination")
            break
    
    logger.info(f"Successfully fetched {len(all_items)} items out of {total_count} total items")
    return all_items

def parse_destination_ids(destination_input):
    """Parse destination IDs from various input formats"""
    if not destination_input:
        return None
    
    # If it's a destination name (like "vietnam"), get the IDs from config
    if destination_input.lower() in DESTINATION_CONFIGS:
        return DESTINATION_CONFIGS[destination_input.lower()]["destination_ids"]
    
    # If it's a comma-separated string, split it
    if isinstance(destination_input, str):
        return [id.strip() for id in destination_input.split(',')]
    
    # If it's already a list, return as is
    if isinstance(destination_input, list):
        return destination_input
    
    return None

def main():
    """Main function with command-line argument support"""
    parser = argparse.ArgumentParser(description='Fetch CRM mail data with configurable destination IDs')
    parser.add_argument('--destinations', '-d', 
                       help='Destination IDs (comma-separated) or destination name (e.g., "vietnam", "proposal")')
    parser.add_argument('--token', '-t', 
                       help='Access token (optional, will use existing token if not provided)')
    parser.add_argument('--output', '-o', 
                       default='crm_mail_search.json',
                       help='Output filename (default: crm_mail_search.json)')
    
    args = parser.parse_args()
    
    # Initialize token manager
    token_manager = TokenManager()

    # Get initial access token
    if args.token:
        access_token = args.token.strip()
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

    # Parse destination IDs
    destination_ids = parse_destination_ids(args.destinations)
    
    logger.info("\n📬 CRM Mail Search API Response:\n")

    # Fetch all mail data using pagination
    data_list = fetch_all_mail_data(destination_ids)

    # Create DataFrame from all fetched items
    df = pd.DataFrame([{k: v for k, v in item.items() if k != 'destination'} for item in data_list])

    # Function to truncate strings to 40 characters
    def truncate_string(value, max_length=40):
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

    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save JSON to output folder
    output_file = os.path.join(output_dir, args.output)
    # Convert DataFrame to list of dictionaries for JSON serialization
    json_data = df.to_dict('records')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    logger.info(f"\n📁 JSON saved to: {output_file}")
    logger.info(f"📊 Final dataset contains {len(json_data)} records")

if __name__ == "__main__":
    main()