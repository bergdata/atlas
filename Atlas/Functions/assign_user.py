import pandas as pd
from bs4 import BeautifulSoup
import logging
from config import DESTINATION_CONFIGS

# Configure logging
logger = logging.getLogger(__name__)

def extract_last_and_previous_email(row):
    """Extract the last email and previous email from the email content"""
    content = row['bodyContent']
    content_type = row['bodyContentType']
    
    if content_type.lower() == 'html':
        # Parse HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract the last email (top-level content, outside blockquotes)
        last_email = []
        for element in soup.find_all(recursive=False):
            if element.name != 'blockquote':
                last_email.append(element.get_text(strip=True))
        last_email_text = ' '.join(last_email).strip()
        
        # Extract the previous email (first blockquote)
        previous_email = soup.find('blockquote')
        previous_email_text = previous_email.get_text(strip=True) if previous_email else ''
        
        return {'last_email': last_email_text, 'previous_email': previous_email_text}
    else:
        # For Text content, use the entire bodyContent as last_email, no previous email
        return {'last_email': content.strip(), 'previous_email': ''}

def extract_riksja_employee(row, destination_config=None):
    """Extract Riksja employee name from email body content using destination configuration"""
    if not destination_config:
        # Fallback to Vietnam config if no destination specified
        destination_config = DESTINATION_CONFIGS["vietnam"]
    
    # Extract last and previous emails
    email_data = extract_last_and_previous_email(row)
    last_email = email_data.get('last_email', '')
    previous_email = email_data.get('previous_email', '')
    body_content = row.get('bodyContent', '')
    
    logger.info(f"🔍 Searching for employee in email content:")
    logger.info(f"   - Last email length: {len(last_email)} chars")
    logger.info(f"   - Previous email length: {len(previous_email)} chars") 
    logger.info(f"   - Body content length: {len(body_content)} chars")
    
    # Search through all content fields
    search_fields = [
        ('last_email', last_email),
        ('previous_email', previous_email), 
        ('body_content', body_content)
    ]
    
    for field_name, field in search_fields:
        if not field:
            logger.debug(f"   ⏭️  Skipping empty field: {field_name}")
            continue
            
        field_lower = field.lower()
        logger.debug(f"   🔎 Searching in {field_name} (first 100 chars: '{field[:100]}...')")
        
        # Check each user's email and name in the config
        users = destination_config.get("users", {})
        for user_key, user_info in users.items():
            # Check email address
            user_email = user_info.get("email", "").lower()
            if user_email and user_email in field_lower:
                logger.info(f"✅ Found employee '{user_key}' by email '{user_email}' in field '{field_name}'")
                return user_key
            
            # Check employee name
            user_name = user_info.get("name", "").lower()
            if user_name and user_name in field_lower:
                logger.info(f"✅ Found employee '{user_key}' by name '{user_name}' in field '{field_name}'")
                return user_key
    
    # If no employee found, return the base user
    base_user = destination_config.get("base_user")
    logger.warning(f"⚠️  No employee found in any field, using base user: {base_user}")
    return base_user

def get_user_id(destination_config, user_key):
    """Get user ID from destination config"""
    users = destination_config.get("users", {})
    user_info = users.get(user_key, {})
    return user_info.get("id")
