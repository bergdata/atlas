import requests
import sys
import logging
import os

# Import from the parent Atlas directory
from config import ENVIRONMENT
from token_manager import TokenManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def make_crm_destination_api_request():
    """Make API request to search destinations in Riksja"""
    token_manager = TokenManager()
    
    # Use the destination-by-entity endpoint for filtering
    url = "https://atlas-api.rickshawnetwork.com/api/crm/destination/destination-by-entity" if ENVIRONMENT == "production" else "https://staging-atlas-api.rickshawnetwork.com/api/crm/destination/destination-by-entity"
    
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "text/plain,application/json,text/html,application/xhtml+xml,application/xml,*/*;q=0.9",
        "Authorization": f"Bearer {access_token}"
    }

    # Parameters for destination search - filtering for Riksja Netherlands (entities=1)
    params = {
        "entities": "1"  # This filters for Riksja Netherlands
    }

    logger.info(f" Making API request to destination-by-entity endpoint with entities=1 to filter for Riksja Netherlands only")
    response = requests.get(url, headers=headers, params=params, timeout=100)
    response.raise_for_status()
    return response.json()

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        token_manager = TokenManager()
        token_manager.add_token(sys.argv[1].strip())
    
    # Get all destinations
    logger.info("🌍 Fetching all destinations from Riksja CRM...")
    token_manager = TokenManager()
    data = token_manager.api_request_with_token_refresh(make_crm_destination_api_request)
    
    # Handle response format
    if isinstance(data, list):
        destinations_data = {"items": data, "totalCount": len(data)}
    elif isinstance(data, dict) and 'items' in data:
        destinations_data = data
    else:
        destinations_data = {"items": [data] if not isinstance(data, list) else data, "totalCount": 1}
    
    # Display results
    logger.info(f"\n📋 Destinations in Riksja ({destinations_data.get('totalCount', len(destinations_data.get('items', [])))} total):")
    for i, destination in enumerate(destinations_data['items'], 1):
        dest_name = destination.get('name', 'N/A')
        dest_id = destination.get('id', 'N/A')
        dest_code = destination.get('code', 'N/A')
        status = "❌ Deleted" if destination.get('isDeleted', False) else "✅ Active"
        logger.info(f"{i}. {dest_name} (ID: {dest_id}, Code: {dest_code}) - {status}")
    
    # Save to JSON file
    import json
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "crm_destinations.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(destinations_data, f, indent=4, ensure_ascii=False)
    logger.info(f"\n📁 Destinations data saved to: {output_file}")
    
    return destinations_data

if __name__ == "__main__":
    main() 