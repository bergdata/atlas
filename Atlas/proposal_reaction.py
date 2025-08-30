import pandas as pd
import re
import logging
import sys
import os
import json
import requests
from token_manager import TokenManager
from crm_mail import fetch_all_mail_data, TokenManager
from Functions.assign_user import extract_riksja_employee, get_user_id
from Functions.mark_email_done import mark_email_as_done
from config import DESTINATION_CONFIGS, get_destination_by_ids


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Proposal-specific configuration - now using destination configs
PROPOSAL_DESTINATION_IDS = ["93", "111"]  #["56", "93", "111", "57", "97", "99", "38", "100", "101", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72"]

def get_all_emails():
    """Retrieve all emails from the CRM with destination IDs"""
    # Use destination IDs from proposal config
    destination_ids = PROPOSAL_DESTINATION_IDS
    
    # Use fetch_all_mail_data instead of make_api_request to get ALL emails
    data_list = fetch_all_mail_data(destination_ids)
    
    df = pd.DataFrame([{k: v for k, v in item.items() if k != 'destination'} for item in data_list])
    
    return df

def filter_proposal_emails(df):
    """Filter emails with the specific subject pattern"""
    # Pattern to match "Re: Je reisplan {Destination_variable} is klaar!"
    pattern = r'^Re:\s*Je\s+reisplan\s+([A-Za-zÀ-ÿ\s]+)\s+is\s+klaar!$'
    
    # Extract the destination name from matching subjects
    extracted = df['subject'].str.extract(pattern, expand=False)
    
    # Filter emails that match the pattern (where extraction is not null)
    filtered_df = df[extracted.notna()].copy()  # Add .copy() to create a new DataFrame
    
    logger.info(f"Found {len(filtered_df)} emails matching the proposal pattern")
    return filtered_df

def get_destination_config_for_email(row):
    """Get the appropriate destination configuration for an email based on its destination IDs"""
    # Extract destination IDs from the email data
    # This assumes the email data contains destination information
    # You may need to adjust this based on your actual data structure
    destination_ids = row.get('destination_ids', [])
    
    if not destination_ids:
        # Fallback to Vietnam config if no destination IDs found
        return DESTINATION_CONFIGS.get("vietnam")
    
    # Find matching destination config
    destination_name, config = get_destination_by_ids(destination_ids)
    if config:
        return config
    
    # Fallback to Vietnam config if no match found
    return DESTINATION_CONFIGS.get("vietnam")

def main():
    """Main function to retrieve proposal emails"""
    logger.info("📬 Starting proposal email analysis...")
    
    try:
        # Get all emails
        logger.info("Retrieving all emails from CRM...")
        all_emails_df = get_all_emails()
        logger.info(f"Retrieved {len(all_emails_df)} total emails")
        
        # Filter emails with proposal pattern
        logger.info("Filtering emails with proposal pattern...")
        proposal_emails_df = filter_proposal_emails(all_emails_df)
        

        if len(proposal_emails_df) == 0:
            logger.warning("No emails found matching the proposal pattern!")
            return
        
        logger.info(f"✅ Found {len(proposal_emails_df)} proposal emails")
        
        # Apply the new employee extraction logic with destination configs
        proposal_emails_df['riksja_employee'] = proposal_emails_df.apply(
            lambda row: extract_riksja_employee(row, get_destination_config_for_email(row)), 
            axis=1
        )
        
        # Add user ID mapping using the new get_user_id function
        proposal_emails_df['user_id'] = proposal_emails_df.apply(
            lambda row: get_user_id(get_destination_config_for_email(row), row['riksja_employee']),
            axis=1
        )

        proposal_emails_df['task_label'] = "proposal-reaction"
        proposal_emails_df['task_label_id'] = "c919667d-2ecc-b3c5-aeca-3a0dc5054e8f"

        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save JSON to output folder
        output_file = os.path.join(output_dir, "proposal_emails.json")
        # Convert DataFrame to list of dictionaries for JSON serialization
        json_data = proposal_emails_df.to_dict('records')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        logger.info(f"\n📁 JSON saved to: {output_file}")
        logger.info(f"📊 Final dataset contains {len(json_data)} records")

        # Create proposal_task_post.json based on the data
#        create_proposal_task_post_json(proposal_emails_df)

    except Exception as e:
        logger.error(f"Error processing proposal emails: {str(e)}")
        raise

def create_proposal_task_post_json(proposal_emails_df):
    """Create proposal_task_post.json based on the proposal emails data"""
    from datetime import datetime, timedelta, timezone
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate task posts for each proposal email
    task_posts = []
    
    for index, row in proposal_emails_df.iterrows():
        # Calculate deadline date (7 days from now) - using UTC
        deadline_date = datetime.now(timezone.utc) + timedelta(days=9)
        
        # Create task post structure
        task_post = {
            "priority": 0,
            "deadlineDate": deadline_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "assignedUserIds": row.get('user_id', ""),
            "travelPlanId": "",
            "labelId": row.get('task_label_id', ""),
            "paxId": row.get("contactPaxId", ""),
            "phoneCallId": "",
            "emailId": row.get('id', ""),
            "entityId": 1,
            "destinationId": row.get("destinationId", ""),
            "subject": f"Proposal Reaction - {row.get('contactFullName', '')}",
            "body": row.get("bodyPreview", ""),
            "visibleFromDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
           # "dashboardTile": 0 # not sure if this is needed
        }

        task_posts.append(task_post)

        task_post_2 = {
            "priority": 2,  # Adjusted to match POST request
            "deadlineDate": deadline_date.strftime("%Y-%m-%dT00:00:00Z"),  # Set to 00:00:00Z
            "visibleFromDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", #From now
            "assignedUserIds": [row.get('user_id', "")],
            "paxId": row.get("contactPaxId", ""),
            "phoneCallId": None,  # Changed to null
            "labelId": row.get("task_label_id", ""),
            "entityId": 1,
            "destinationId": row.get("destinationId", ""),
            "subject": f"Proposal reaction -TEST1234567890 {row.get('contactFullName', '')}",  # Adjusted case to match POST
            "body": "",  # Set to empty string to match POST
            "emailId": row.get("id", ""),
            "travelPlan": "",  # Added to match POST
            "travelPlanId": None,  # Changed to null
            # "dashboardTile": 0,  # Not needed in POST request (already commented)
            # "done": False,  # Not needed in POST request
            # "attachments": None,  # Not needed in POST request
            # "isDeleted": False,  # Not needed in POST request
            # "deleterId": None,  # Not needed in POST request
            # "deletionTime": None,  # Not needed in POST request
            # "lastModificationTime": None,  # Not needed in POST request
            # "lastModifierId": None  # Not needed in POST request
        }        
        task_posts.append(task_post_2)

        # Send POST request with task_post_2 as payload
        try:
            # Send POST request
            url = "https://staging-atlas-api.rickshawnetwork.com/api/crm/task"
            
            # Get headers from TokenManager
            token_manager = TokenManager()

            # Get current token (without incrementing usage)
            access_token = token_manager.get_active_token_value()
            if not access_token:
                raise Exception("No active token available")

            headers = {
                "Accept": "application/json,text/html,application/xhtml+xml,application/xml,text/*;q=0.9, image/*;q=0.8, */*;q=0.7",
                "Authorization": f"Bearer {access_token}"
            }
            
            payload = task_post_2
            
            #response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                # Print response details
                logger.info(f"Status Code: {response.status_code}")
                logger.info(f"Response Headers: {response.headers}")
                logger.info(f"Response Content: {response.text}")
                
                # Save complete response to JSON file
                response_data = {
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                    "response_content": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
                
                # Save to post_task_output.json
                output_file = os.path.join(output_dir, "post_task_output.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"\n📁 Complete response saved to: {output_file}")

                # Mark email as done after successful task creation
                email_id = row.get("id", "")
                if email_id:
                    logger.info(f"📧 Marking email {email_id} as done...")
                    mark_email_as_done(email_id)
                else:
                    logger.warning("⚠️ No email ID found to mark as done")
                
            else:
                logger.error(f"Failed to create task post for {row.get('contactFullName', '')}")
            
        except Exception as e:
            logger.error(f"Error sending POST request: {str(e)}")

    
    # Save to file
    output_file = os.path.join(output_dir, "proposal_task_post.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(task_posts, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n📁 Proposal task post JSON saved to: {output_file}")
    logger.info(f"📊 Created {len(task_posts)} task posts")

if __name__ == "__main__":
    main()
