import json
import os

def convert_destinations_to_dict():
    """Convert destinations.json from list to dictionary format"""
    # Read current destinations (list format)
    with open('destinations.json', 'r', encoding='utf-8') as f:
        destinations_list = json.load(f)

    # Convert to dictionary format with IDs as keys
    destinations_dict = {}
    for dest in destinations_list:
        dest_id = str(dest['id'])  # Convert ID to string for consistency
        destinations_dict[dest_id] = {
            'name': dest['name'],
            'country': dest['country'],
            'email': dest['email']
        }

    # Save back as dictionary
    with open('destinations.json', 'w', encoding='utf-8') as f:
        json.dump(destinations_dict, f, indent=2, ensure_ascii=False)

    print(f"Converted destinations.json to dictionary format with {len(destinations_dict)} destinations")

def convert_employees_to_dict():
    """Convert employees.json from list to dictionary format if needed"""
    # Read current employees
    with open('employees.json', 'r', encoding='utf-8') as f:
        employees_data = json.load(f)

    # Check if it's already a dictionary
    if isinstance(employees_data, dict):
        print("Employees already in dictionary format")
        return

    # If it's a list, convert to dictionary
    employees_dict = {}
    for emp in employees_data:
        emp_id = str(emp['id'])
        employees_dict[emp_id] = {
            'username': emp['username'],
            'email': emp['email'],
            'phone_extension': emp.get('phone_extension'),
            'teams': emp.get('teams', [])
        }

    # Save back as dictionary
    with open('employees.json', 'w', encoding='utf-8') as f:
        json.dump(employees_dict, f, indent=2, ensure_ascii=False)

    print(f"Converted employees.json to dictionary format with {len(employees_dict)} employees")

if __name__ == "__main__":
    convert_destinations_to_dict()
    convert_employees_to_dict()
    print("Data format conversion completed!")
