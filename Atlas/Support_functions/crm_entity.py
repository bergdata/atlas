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

def make_crm_entity_api_request():
    """Make API request to get entities in Riksja"""
    token_manager = TokenManager()
    
    url = "https://atlas-api.rickshawnetwork.com/api/crm/entity" if ENVIRONMENT == "production" else "https://staging-atlas-api.rickshawnetwork.com/api/crm/entity"
    
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "text/plain,application/json,text/html,application/xhtml+xml,application/xml,*/*;q=0.9",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, timeout=100)
    response.raise_for_status()
    return response.json()

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        token_manager = TokenManager()
        token_manager.add_token(sys.argv[1].strip())
    
    # Get all entities
    logger.info("🏢 Fetching all entities from Riksja CRM...")
    token_manager = TokenManager()
    data = token_manager.api_request_with_token_refresh(make_crm_entity_api_request)
    
    # Handle response format
    if isinstance(data, list):
        entities_data = {"items": data, "totalCount": len(data)}
    elif isinstance(data, dict) and 'items' in data:
        entities_data = data
    else:
        entities_data = {"items": [data] if not isinstance(data, list) else data, "totalCount": 1}
    
    # Display results
    logger.info(f"\n Entities in Riksja ({entities_data.get('totalCount', len(entities_data.get('items', [])))} total):")
    for i, entity in enumerate(entities_data['items'], 1):
        entity_name = entity.get('name', 'N/A')
        entity_id = entity.get('id', 'N/A')
        entity_code = entity.get('code', 'N/A')
        status = "❌ Deleted" if entity.get('isDeleted', False) else "✅ Active"
        logger.info(f"{i}. {entity_name} (ID: {entity_id}, Code: {entity_code}) - {status}")
    
    # Save to JSON file
    import json
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "crm_entities.json")
    with open(output_file, 'w') as f:
        json.dump(entities_data, f, indent=4)
    logger.info(f"\n📁 Entities data saved to: {output_file}")
    
    return entities_data

if __name__ == "__main__":
    main() 