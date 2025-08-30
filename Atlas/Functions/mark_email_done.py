import requests
import logging
from token_manager import TokenManager
from config import ENVIRONMENT

# Configure logging
logger = logging.getLogger(__name__)

def mark_email_as_done(email_id, environment=None):
    """Mark an email as done using the API for staging or production"""
    try:
        # Use provided environment or default from config
        if environment is None:
            environment = ENVIRONMENT
            
        # Get headers from TokenManager
        token_manager = TokenManager()
        access_token = token_manager.get_active_token_value()
        if not access_token:
            raise Exception("No active token available")

        headers = {
            "Accept": "application/json,text/html,application/xhtml+xml,application/xml,text/*;q=0.9, image/*;q=0.8, */*;q=0.7",
            "Authorization": f"Bearer {access_token}"
        }

        # API endpoint to mark email as done - use environment-specific URL
        if environment == "production":
            base_url = "https://atlas-api.rickshawnetwork.com"
        else:
            base_url = "https://staging-atlas-api.rickshawnetwork.com"
            
        url = f"{base_url}/api/crm/mail/{email_id}/mark-done"
        
        params = {
            'value': 'true',
        }

        response = requests.post(url, params=params, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully marked email {email_id} as done in {environment}")
            return True
        else:
            logger.error(f"❌ Failed to mark email {email_id} as done in {environment}. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error marking email {email_id} as done in {environment}: {str(e)}")
        return False

def mark_multiple_emails_as_done(email_ids, environment=None):
    """Mark multiple emails as done using the API"""
    if not email_ids:
        logger.warning("No email IDs provided to mark as done")
        return []
    
    results = []
    for email_id in email_ids:
        success = mark_email_as_done(email_id, environment)
        results.append({
            'email_id': email_id,
            'success': success,
            'environment': environment or ENVIRONMENT
        })
    
    successful_count = sum(1 for result in results if result['success'])
    logger.info(f"�� Marked {successful_count}/{len(email_ids)} emails as done in {environment or ENVIRONMENT}")
    
    return results 