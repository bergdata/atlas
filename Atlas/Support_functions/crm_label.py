import requests
import sys
import logging
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from the parent Atlas directory
from config import ENVIRONMENT
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

def save_response_to_file(data, filename):
    """Save response data to a JSON file"""
    import json
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, filename)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)
    logger.info(f" Response saved to: {output_file}")

def make_crm_label_api_request():
    """Make API request to get all labels in Riksja"""
    token_manager = TokenManager()
    
    if ENVIRONMENT == "production":
        url = "https://atlas-api.rickshawnetwork.com/api/crm/label"
    else:
        url = "https://staging-atlas-api.rickshawnetwork.com/api/crm/label"

    # Get current token (without incrementing usage)
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "text/plain,application/json,text/html,application/xhtml+xml,application/xml,*/*;q=0.9",
        "Authorization": f"Bearer {access_token}"
    }

    # Remove entityId from params since it doesn't work
    params = {"maxResultCount": 1000}

    response = requests.get(url, headers=headers, params=params, timeout=100)

    response.raise_for_status()
    return response.json()

def get_all_labels():
    """Get all labels in Riksja"""
    try:
        token_manager = TokenManager()
        data = token_manager.api_request_with_token_refresh(make_crm_label_api_request)

        if isinstance(data, list):
            labels_list = [label for label in data if label.get('entityId') == 1]
            logger.info(f"✅ Successfully retrieved {len(labels_list)} labels with entityId = 1 (filtered from {len(data)} total)")
            return {"items": labels_list, "totalCount": len(labels_list)}
        elif isinstance(data, dict) and 'items' in data:
            original_items = data['items']
            filtered_items = [label for label in original_items if label.get('entityId') == 1]
            logger.info(f"✅ Successfully retrieved {len(filtered_items)} labels with entityId = 1 (filtered from {len(original_items)} total)")
            return {"items": filtered_items, "totalCount": len(filtered_items)}
        else:
            return {"items": [data] if not isinstance(data, list) else data, "totalCount": 1}
        
    except Exception as e:
        logger.error(f"❌ Error fetching labels: {str(e)}")
        raise

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        access_token = sys.argv[1].strip()
        token_manager = TokenManager()
        token_manager.add_token(access_token)
    
    labels_data = get_all_labels()
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "crm_labels.json")
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(labels_data, f, indent=4, ensure_ascii=False)
    
    logger.info(f"\n📁 Labels data saved to: {output_file}")

    return labels_data

if __name__ == "__main__":
    main() 