import pandas as pd
import sys
import logging
import json
import os
from bs4 import BeautifulSoup
from crm_mail import make_api_request, TokenManager
from config import ENVIRONMENT
from Functions.assign_user import extract_riksja_employee, get_user_id


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_crm_mail_data():
    """Get CRM mail data using the existing crm_mail functionality"""
    token_manager = TokenManager()
    
    # Make API request with automatic token refresh
    data = token_manager.api_request_with_token_refresh(make_api_request)
    
    data_list = data['items']
    df = pd.DataFrame([{k: v for k, v in item.items() if k != 'destination'} for item in data_list])
    
    return df

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

def load_automations():
    """Load automations data from automations.json"""
    try:
        automations_file = os.path.join(os.path.dirname(__file__), 'automations.json')
        with open(automations_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading automations: {e}")
        return {}

def load_destination_configs():
    """Load destination configurations"""
    try:
        configs_file = os.path.join(os.path.dirname(__file__), 'destination_configs.json')
        with open(configs_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading destination configs: {e}")
        return {}

def check_automation_rules(subject, automation):
    """Check if email subject matches automation rules"""
    if not subject:
        return False

    subject_lower = subject.lower()

    # First validate rule consistency (no duplicate starts_with or ends_with)
    if not validate_automation_rules(automation):
        logger.warning(f"⚠️  Automation has invalid rule configuration (duplicate rule types)")
        return False

    # Check rule 1
    rule1_value = automation.get('rule1_value', '').strip()
    if rule1_value:
        rule1_type = automation.get('rule1_type', 'contains')
        if not check_single_rule(subject_lower, rule1_value.lower(), rule1_type):
            return False

    # Check rule 2
    rule2_value = automation.get('rule2_value', '').strip()
    if rule2_value:
        rule2_type = automation.get('rule2_type', 'contains')
        if not check_single_rule(subject_lower, rule2_value.lower(), rule2_type):
            return False

    # Check rule 3
    rule3_value = automation.get('rule3_value', '').strip()
    if rule3_value:
        rule3_type = automation.get('rule3_type', 'contains')
        if not check_single_rule(subject_lower, rule3_value.lower(), rule3_type):
            return False

    return True

def validate_automation_rules(automation):
    """Validate that automation rules don't have duplicate types"""
    rule_types = []

    # Collect all rule types that have values
    for i in range(1, 4):
        rule_value = automation.get(f'rule{i}_value', '').strip()
        if rule_value:
            rule_type = automation.get(f'rule{i}_type', 'contains')
            rule_types.append(rule_type)

    # Check for duplicates of starts_with and ends_with
    starts_with_count = rule_types.count('starts_with')
    ends_with_count = rule_types.count('ends_with')

    if starts_with_count > 1:
        logger.warning(f"❌ Multiple 'starts_with' rules found: {starts_with_count}")
        return False

    if ends_with_count > 1:
        logger.warning(f"❌ Multiple 'ends_with' rules found: {ends_with_count}")
        return False

    return True

def check_single_rule(subject, rule_value, rule_type):
    """Check if subject matches a single rule"""
    if rule_type == 'starts_with':
        return subject.startswith(rule_value)
    elif rule_type == 'ends_with':
        return subject.endswith(rule_value)
    elif rule_type == 'contains':
        return rule_value in subject
    return False

def assign_user_distribution(destination_config, email_index):
    """Assign user using distribution (round-robin) logic"""
    users = destination_config.get('users', {})
    if not users:
        return destination_config.get('base_user')

    # Get list of user keys
    user_keys = list(users.keys())

    # Use email index for round-robin assignment
    assigned_user = user_keys[email_index % len(user_keys)]

    logger.info(f"📊 Distribution assignment: Email {email_index} → {assigned_user}")
    return assigned_user

def assign_user_base_logic(row, destination_config):
    """Assign user using base-user logic (search for names/emails)"""
    return extract_riksja_employee(row, destination_config)

def extract_riksja_employee(row, destination_config=None):
    """Extract Riksja employee name from email content using destination configuration"""
    if not destination_config:
        # Fallback to Vietnam config if no destination specified
        from config import DESTINATION_CONFIGS
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

def categorize_and_order_emails(email_df):
    """Categorize emails by destinationId and order them"""
    logger.info("📊 Categorizing and ordering emails by destinationId...")
    
    # Get unique destinationIds and sort them
    unique_destinations = sorted(email_df['destinationId'].unique())
    
    # Create a mapping from destinationId to category (1, 2, 3, 4, 5...)
    destination_to_category = {dest_id: i+1 for i, dest_id in enumerate(unique_destinations)}
    
    # Add category column based on destinationId
    email_df['category'] = email_df['destinationId'].apply(lambda x: destination_to_category.get(x, len(unique_destinations) + 1))
    
    # Sort by destinationId and then by receivedDateTime
    email_df_sorted = email_df.sort_values(['destinationId', 'receivedDateTime'], ascending=[True, True])
    
    # Display categorization results
    logger.info("\n📋 Email Categorization Results:")
    category_counts = email_df_sorted['category'].value_counts().sort_index()
    for category, count in category_counts.items():
        logger.info(f"Category {category}: {count} emails")
    
    # Display destination breakdown
    logger.info("\n🏛️ Destination Breakdown:")
    destination_counts = email_df_sorted['destinationId'].value_counts().sort_index()
    for dest_id, count in destination_counts.items():
        category = destination_to_category.get(dest_id, "Unknown")
        logger.info(f"Destination ID {dest_id} (Category {category}): {count} emails")
    
    return email_df_sorted

def process_emails_with_automations():
    """Process emails using automations logic"""
    logger.info("🎯 Starting email processing with automations...")

    try:
        # Load configuration data
        automations = load_automations()
        destination_configs = load_destination_configs()

        # Get CRM mail data
        email_df = get_crm_mail_data()
        logger.info(f"Retrieved {len(email_df)} emails from CRM")

        # Apply email extraction
        logger.info("Extracting last and previous emails...")
        email_df[['last_email', 'previous_email']] = email_df.apply(
            lambda row: pd.Series(extract_last_and_previous_email(row)), axis=1
        )

        # Process emails with automations
        logger.info("🎯 Processing emails with automations...")
        email_assignments = []

        for idx, row in email_df.iterrows():
            subject = row.get('subject', '')
            destination_id = str(row.get('destinationId', ''))

            assigned_user = None
            matched_automation = None

            # Check each enabled automation
            for automation_id, automation in automations.items():
                if not automation.get('enabled', False):
                    continue

                # Check if destination is applicable
                applicable_destinations = automation.get('applicable_destinations', [])
                if destination_id not in applicable_destinations:
                    continue

                # Check if email matches automation rules
                if check_automation_rules(subject, automation):
                    matched_automation = automation
                    logger.info(f"✅ Email {idx} matches automation '{automation.get('name', automation_id)}'")

                    # Find destination config for this destination
                    destination_config = None
                    for config_name, config in destination_configs.items():
                        if destination_id in config.get('destination_ids', []):
                            destination_config = config
                            break

                    if not destination_config:
                        logger.warning(f"⚠️  No destination config found for destination {destination_id}")
                        continue

                    # Apply assignment logic
                    assignment_logic = automation.get('assignment_logic', 'base_user')

                    if assignment_logic == 'distribution':
                        assigned_user = assign_user_distribution(destination_config, idx)
                    else:  # base_user
                        assigned_user = assign_user_base_logic(row, destination_config)

                    break  # Use first matching automation

            if assigned_user:
                email_assignments.append(assigned_user)
                logger.info(f"👤 Email {idx} assigned to: {assigned_user}")
            else:
                email_assignments.append(None)
                logger.info(f"❓ Email {idx} not assigned by any automation")

        # Add assignments to dataframe
        email_df['riksja_employee'] = email_assignments

        # Display results
        logger.info("\n📊 Email Assignment Results:")
        logger.info(f"Total emails processed: {len(email_df)}")

        # Count assignments
        assignments = email_df['riksja_employee'].value_counts()
        logger.info("\nEmployee assignments:")
        for employee, count in assignments.items():
            if pd.isna(employee):
                logger.info(f"Unassigned: {count}")
            else:
                logger.info(f"{employee}: {count}")

        # Show unassigned emails
        unassigned = email_df[email_df['riksja_employee'].isna()]
        if len(unassigned) > 0:
            logger.info(f"\n⚠️  {len(unassigned)} emails could not be assigned by automations")
            logger.info("Unassigned emails:")
            for idx, row in unassigned.head(5).iterrows():
                logger.info(f"  - Subject: {row.get('subject', 'N/A')}")
                logger.info(f"    From: {row.get('from', 'N/A')}")

        # Save processed data
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = os.path.join(output_dir, "processed_emails_automations.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(email_df.to_dict('records'), f, indent=4, ensure_ascii=False)
        logger.info(f"\n📁 Processed data saved to: {output_file}")

        return email_df

    except Exception as e:
        logger.error(f"Error processing emails: {str(e)}")
        raise

def process_emails():
    """Main function to process emails and assign them to users"""
    logger.info("📬 Starting email processing...")

    try:
        # Get CRM mail data
        email_df = get_crm_mail_data()
        logger.info(f"Retrieved {len(email_df)} emails from CRM")

        # Apply email extraction
        logger.info("Extracting last and previous emails...")
        email_df[['last_email', 'previous_email']] = email_df.apply(
            lambda row: pd.Series(extract_last_and_previous_email(row)), axis=1
        )

        # Add riksja_employee column
        logger.info("Assigning emails to Riksja employees...")
        email_df['riksja_employee'] = email_df.apply(extract_riksja_employee, axis=1)

        # Display results
        logger.info("\n📊 Email Assignment Results:")
        logger.info(f"Total emails processed: {len(email_df)}")

        # Count assignments
        assignments = email_df['riksja_employee'].value_counts()
        logger.info("\nEmployee assignments:")
        for employee, count in assignments.items():
            if pd.isna(employee):
                logger.info(f"Unassigned: {count}")
            else:
                logger.info(f"{employee}: {count}")

        # Show unassigned emails
        unassigned = email_df[email_df['riksja_employee'].isna()]
        if len(unassigned) > 0:
            logger.info(f"\n⚠️  {len(unassigned)} emails could not be assigned to any employee")
            logger.info("Unassigned emails:")
            for idx, row in unassigned.head(5).iterrows():
                logger.info(f"  - Subject: {row.get('subject', 'N/A')}")
                logger.info(f"    From: {row.get('from', 'N/A')}")

        # Save processed data
        import os
        import json
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = os.path.join(output_dir, "processed_emails.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(email_df.to_dict('records'), f, indent=4, ensure_ascii=False)
        logger.info(f"\n📁 Processed data saved to: {output_file}")

        return email_df

    except Exception as e:
        logger.error(f"Error processing emails: {str(e)}")
        raise

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        # If token provided as command line argument
        access_token = sys.argv[1].strip()
        token_manager = TokenManager()
        token_manager.add_token(access_token)
    
    # Process emails
    processed_df = process_emails()
    
    # Display sample of processed data
    logger.info("\n📋 Sample of processed emails:")
    
    # Define desired columns and check which ones exist
    desired_cols = ['subject', 'from', 'riksja_employee', 'last_email']
    available_cols = [col for col in desired_cols if col in processed_df.columns]
    
    if available_cols:
        logger.info(processed_df[available_cols].head())
    else:
        logger.info("No sample columns available. Available columns:")
        logger.info(list(processed_df.columns))

if __name__ == "__main__":
    main()
