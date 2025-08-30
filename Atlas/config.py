import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment setting
ENVIRONMENT = os.getenv('ENVIRONMENT', 'staging')

# Atlas API Credentials
ATLAS_USERNAME = os.getenv('ATLAS_USERNAME')
ATLAS_PASSWORD = os.getenv('ATLAS_PASSWORD')

# API URLs
STAGING_AUTH_URL = os.getenv('STAGING_AUTH_URL', 'https://staging-atlas-auth.rickshawnetwork.com')
STAGING_API_URL = os.getenv('STAGING_API_URL', 'https://staging-atlas-api.rickshawnetwork.com')
STAGING_REDIRECT_URI = os.getenv('STAGING_REDIRECT_URI', 'https://staging-atlas.rickshawnetwork.com')

PRODUCTION_AUTH_URL = os.getenv('PRODUCTION_AUTH_URL', 'https://atlas-auth.rickshawnetwork.com')
PRODUCTION_API_URL = os.getenv('PRODUCTION_API_URL', 'https://atlas-api.rickshawnetwork.com')
PRODUCTION_REDIRECT_URI = os.getenv('PRODUCTION_REDIRECT_URI', 'https://atlas.rickshawnetwork.com')

# Client Configuration
CLIENT_ID = os.getenv('CLIENT_ID', 'Atlas_App')

# Destination IDs
DESTINATION_IDS = os.getenv('DESTINATION_IDS', '111,93').split(',')

# Entities in Riksja
# Wij filteren nu enkel alleen nog op ID 1, Nederland
# Dit is de default entity die we gebruiken voor API
# 1. Riksja     - Nederland
# 2. Rickshaw   - Engeland 
# 3. erlebe     - Duitsland
ENTITY_ID = os.getenv('ENTITY_ID', '1')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Destination-specific employee assignments
DESTINATION_CONFIGS = {
    "vietnam": {
        "destination_ids": ["93", "111"],
        "users": {
            "charona": {
                "name": "Charona",
                "id": "5e246d96-0dc0-f08a-c874-3a1120e0d81f",
                "email": "charona.van.ingen@riksjatravel.nl"
            },
            "anne_karlijn": {
                "name": "Anne-Karlijn", 
                "id": "ef64fbec-29b0-43e4-9cd0-7c6ad903934c",
                "email": "anne-karlijn.bol@riksjatravel.nl",
                "dt_startdate": "2025-08-01"
            }
        },
        "base_user": "charona",  # Default user for unassigned emails
        "assigned_users": ["charona.van.ingen@riksjatravel.nl", "anne-karlijn.bol@riksjatravel.nl"]
    }
    # Add more destinations here as needed:
}

def get_destination_config(destination_name):
    """Get configuration for a specific destination"""
    return DESTINATION_CONFIGS.get(destination_name.lower())

def get_destination_by_ids(destination_ids):
    """Find destination configuration by destination IDs"""
    for dest_name, config in DESTINATION_CONFIGS.items():
        if set(destination_ids) == set(config["destination_ids"]):
            return dest_name, config
    return None, None 

