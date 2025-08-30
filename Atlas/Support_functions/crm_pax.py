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

def get_mails_for_pax_id(pax_id):
    """Get mails for a specific PaxId"""
    token_manager = TokenManager()
    
    if ENVIRONMENT == "production":
        url = "https://atlas-api.rickshawnetwork.com/api/crm/mail/mails-with-pax-id"
    else:
        url = "https://staging-atlas-api.rickshawnetwork.com/api/crm/mail/mails-with-pax-id"

    # Get current token
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "text/plain,application/json,text/html,application/xhtml+xml,application/xml,*/*;q=0.9",
        "Authorization": f"Bearer {access_token}"
    }

    # Parameters for mail endpoint
    params = {
        "sorting": "sentDateTime desc",
        "skipCount": 0,
        "maxResultCount": 1000,
        "draft": False,
        "trash": False,
        "paxId": pax_id
    }

    response = requests.get(url, headers=headers, params=params, timeout=100)
    response.raise_for_status()
    return response.json()

def get_pax_id_by_email(email):
    """Get PaxId by searching with email address"""
    token_manager = TokenManager()
    
    if ENVIRONMENT == "production":
        url = "https://atlas-api.rickshawnetwork.com/api/crm/pax/search-by-name-or-email"
    else:
        url = "https://staging-atlas-api.rickshawnetwork.com/api/crm/pax/search-by-name-or-email"

    # Get current token
    access_token = token_manager.get_active_token_value()
    if not access_token:
        raise Exception("No active token available")

    headers = {
        "Accept": "text/plain,application/json,text/html,application/xhtml+xml,application/xml,*/*;q=0.9",
        "Authorization": f"Bearer {access_token}"
    }

    # Simple request with just the filter parameter
    response = requests.get(
        f'{url}?filter={email}',
        headers=headers,
        timeout=100
    )

    response.raise_for_status()
    data = response.json()
    logger.info(f"Data: {data}")
    # Return all pax IDs if found
    if data.get('items') and len(data['items']) > 0:
        pax_ids = [item['id'] for item in data['items']]
        logger.info(f"✅ Found {len(pax_ids)} PaxIds for email: {email}")
        
        # If multiple PaxIds found, get mails for each
        if len(pax_ids) > 1:
            logger.info(f"📧 Multiple PaxIds found, fetching mail information...")
            for i, pax_id in enumerate(pax_ids, 1):
                logger.info(f"\n PaxId {i}: {pax_id}")
                try:
                    mails_data = get_mails_for_pax_id(pax_id)
                    logger.info(f"Mail data for PaxId {pax_id}:")
                    logger.info(mails_data)
                except Exception as e:
                    logger.error(f"❌ Error fetching mails for PaxId {pax_id}: {str(e)}")
        
        return pax_ids
    else:
        logger.warning(f"⚠️ No pax found with email: {email}")
        return None

if __name__ == "__main__":
    # Example usage
    pax_ids = get_pax_id_by_email("ingrid.mostert@hotmail.com")
    if pax_ids:
        logger.info(f"Found PaxIds: {pax_ids}")
    else:
        logger.info("No pax found")
