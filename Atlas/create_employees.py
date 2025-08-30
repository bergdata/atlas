import json
import os

def create_employees_json():
    """Create employees.json from CRM users data"""
    # Read the CRM users data
    with open('output/crm_users.json', 'r', encoding='utf-8') as f:
        crm_data = json.load(f)

    # Process users
    employees = {}

    for item in crm_data.get('items', []):
        user_id = item['id']
        username = item['userName']
        email = item.get('userName', '')  # Using username as email for now
        phone_extension = item.get('phoneNumExtension')
        teams = item.get('teams', '').split(',') if item.get('teams') else []

        employees[user_id] = {
            'username': username,
            'email': email,
            'phone_extension': phone_extension,
            'teams': teams
        }

    # Save employees
    with open('employees.json', 'w', encoding='utf-8') as f:
        json.dump(employees, f, indent=2, ensure_ascii=False)

    print(f"Created employees.json with {len(employees)} employees")

if __name__ == "__main__":
    create_employees_json()
