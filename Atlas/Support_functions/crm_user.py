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

def make_crm_user_api_request():
    """Make API request to get all users in Riksja"""
    token_manager = TokenManager()
    
    if ENVIRONMENT == "production":
        url = "https://atlas-api.rickshawnetwork.com/api/crm/user"
    else:
        url = "https://staging-atlas-api.rickshawnetwork.com/api/crm/user"

    # Get current token (without incrementing usage)
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "text/plain,application/json,text/html,application/xhtml+xml,application/xml,*/*;q=0.9",
        "Authorization": f"Bearer {access_token}"
    }

    # No parameters needed for user endpoint
    params = {}

    response = requests.get(url, headers=headers, params=params, timeout=100)

    response.raise_for_status()
    return response.json()

def get_all_users():
    """Get all users in Riksja, filtered by entities == 1"""
    logger.info(" Fetching all users from Riksja CRM...")
    
    try:
        # Make API request with automatic token refresh
        token_manager = TokenManager()
        data = token_manager.api_request_with_token_refresh(make_crm_user_api_request)

        original_length = len(data)
        logger.info(f"✅ Successfully retrieved {original_length} users")
                
        # Handle different response formats
        if isinstance(data, list):
            # Direct list response
            users_list = [user for user in data if user.get("entities") == "1"]
            logger.info(f"✅ Successfully retrieved {len(users_list)} users with entities == 1")
            return {"items": users_list}
        elif isinstance(data, dict) and 'items' in data:
            # Object with items property
            filtered = [user for user in data['items'] if user.get("entities") == "1"]
            logger.info(f"✅ Successfully retrieved {len(filtered)} users with entities == 1")
            return {"items": filtered}
        else:
            # Unexpected format, wrap in items structure
            logger.info(f"✅ Successfully retrieved data in unexpected format")
            filtered = [data] if not isinstance(data, list) and data.get("entities") == "1" else []
            return {"items": filtered}
        
    except Exception as e:
        logger.error(f"❌ Error fetching users: {str(e)}")
        raise

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        # If token provided as command line argument
        access_token = sys.argv[1].strip()
        token_manager = TokenManager()
        token_manager.add_token(access_token)
    
    # Get all users
    users_data = get_all_users()
    
    # Save to JSON file
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "crm_users.json")
    import json
    with open(output_file, 'w') as f:
        json.dump(users_data, f, indent=4)
    logger.info(f"\n📁 Users data saved to: {output_file}")
    
    return users_data

if __name__ == "__main__":
    main()