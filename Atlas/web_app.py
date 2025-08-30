from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
from config_manager import save_automation, get_automations, get_history, get_stats, delete_automation as delete_automation_config, create_manual_backup

app = Flask(__name__)

# Data storage files
AUTOMATIONS_FILE = 'automations.json'
DESTINATIONS_FILE = 'destinations.json'
EMPLOYEES_FILE = 'employees.json'
DESTINATION_GROUPS_FILE = 'destination_groups.json'
DESTINATION_CONFIGS_FILE = 'destination_configs.json'

# Initialize data files if they don't exist
def init_data_files():
    if not os.path.exists(AUTOMATIONS_FILE):
        default_automations = {
            "1": {
                "name": "Je reisplan xyz is klaar",
                "crm_label_id": "c919667d-2ecc-b3c5-aeca-3a0dc5054e8f",
                "applicable_destinations": ["93", "111"],
                "enabled": True,
                "assignment_logic": "base_user",
                "rule1_type": "starts_with",
                "rule1_value": ""
            },
            "2": {
                "name": "",
                "crm_label_id": "",
                "applicable_destinations": [],
                "enabled": False,
                "assignment_logic": "base_user",
                "rule1_type": "starts_with",
                "rule1_value": ""
            },
            "3": {
                "name": "",
                "crm_label_id": "",
                "applicable_destinations": [],
                "enabled": False,
                "assignment_logic": "base_user",
                "rule1_type": "starts_with",
                "rule1_value": ""
            },
            "4": {
                "name": "",
                "crm_label_id": "",
                "applicable_destinations": [],
                "enabled": False,
                "assignment_logic": "base_user",
                "rule1_type": "starts_with",
                "rule1_value": ""
            },
            "5": {
                "name": "",
                "crm_label_id": "",
                "applicable_destinations": [],
                "enabled": False,
                "assignment_logic": "base_user",
                "rule1_type": "starts_with",
                "rule1_value": ""
            },
            "6": {
                "name": "",
                "crm_label_id": "",
                "applicable_destinations": [],
                "enabled": False,
                "assignment_logic": "base_user",
                "rule1_type": "starts_with",
                "rule1_value": ""
            }
        }
        with open(AUTOMATIONS_FILE, 'w') as f:
            json.dump(default_automations, f, indent=2)

    if not os.path.exists(DESTINATIONS_FILE):
        # Load from existing crm_destinations.json if available
        if os.path.exists('output/crm_destinations.json'):
            with open('output/crm_destinations.json', 'r') as f:
                crm_data = json.load(f)
                destinations = {}
                for item in crm_data.get('items', []):
                    destinations[item['id']] = {
                        'name': item['name'],
                        'email': item.get('emailAddress', ''),
                        'country': extract_country_from_name(item['name'])
                    }
            with open(DESTINATIONS_FILE, 'w') as f:
                json.dump(destinations, f, indent=2)
        else:
            with open(DESTINATIONS_FILE, 'w') as f:
                json.dump({}, f, indent=2)

    if not os.path.exists(EMPLOYEES_FILE):
        # Load from existing crm_users.json if available
        if os.path.exists('output/crm_users.json'):
            with open('output/crm_users.json', 'r') as f:
                crm_data = json.load(f)
                employees = {}
                for item in crm_data.get('items', []):
                    employees[item['id']] = {
                        'username': item['userName'],
                        'email': item.get('userName', ''),
                        'phone_extension': item.get('phoneNumExtension'),
                        'teams': item.get('teams', '').split(',') if item.get('teams') else []
                    }
            with open(EMPLOYEES_FILE, 'w') as f:
                json.dump(employees, f, indent=2)
        else:
            with open(EMPLOYEES_FILE, 'w') as f:
                json.dump({}, f, indent=2)

def extract_country_from_name(name):
    """Extract country name from destination name like 'Riksja Vietnam'"""
    # Fix encoding issues for special characters - handle both UTF-8 and Latin-1 issues
    import re

    # Handle common encoding issues
    name = name.replace('Ã«', 'ë').replace('Ã«', 'ë').replace('Ã¯', 'ï')
    name = name.replace('Ã©', 'é').replace('Ã¨', 'è').replace('Ã¡', 'á')
    name = name.replace('Ã³', 'ó').replace('Ãº', 'ú').replace('Ã±', 'ñ')
    name = name.replace('Ã¼', 'ü').replace('Ã¶', 'ö').replace('Ã¤', 'ä')
    name = name.replace('Ã§', 'ç').replace('Ã¿', 'ÿ')

    # Also handle double-encoded characters
    name = name.replace('ÃƒÂ«', 'ë').replace('ÃƒÂ©', 'é').replace('ÃƒÂ¨', 'è')
    name = name.replace('ÃƒÂ¡', 'á').replace('ÃƒÂ³', 'ó').replace('ÃƒÂº', 'ú')

    if 'Riksja' in name:
        return name.replace('Riksja', '').strip()
    elif 'Rickshaw' in name:
        return name.replace('Rickshaw', '').strip()
    return name

def load_automations():
    try:
        with open(AUTOMATIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading automations: {e}")
        return {}

def save_automations(automations):
    try:
        with open(AUTOMATIONS_FILE, 'w') as f:
            json.dump(automations, f, indent=2)
    except Exception as e:
        print(f"Error saving automations: {e}")

def load_destinations():
    try:
        with open(DESTINATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading destinations: {e}")
        return {}

def load_employees():
    try:
        with open(EMPLOYEES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading employees: {e}")
        return {}

def load_destination_groups():
    try:
        if os.path.exists(DESTINATION_GROUPS_FILE):
            with open(DESTINATION_GROUPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading destination groups: {e}")
    return {}

def save_destination_groups(groups):
    try:
        with open(DESTINATION_GROUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving destination groups: {e}")

def load_destination_configs():
    try:
        if os.path.exists(DESTINATION_CONFIGS_FILE):
            with open(DESTINATION_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading destination configs: {e}")
    return {}

def save_destination_configs(configs):
    try:
        with open(DESTINATION_CONFIGS_FILE, 'w') as f:
            json.dump(configs, f, indent=2)
    except Exception as e:
        print(f"Error saving destination configs: {e}")

def load_teams():
    """Load teams data from teams.json"""
    try:
        teams_file = os.path.join(os.path.dirname(__file__), 'teams.json')
        if os.path.exists(teams_file):
            with open(teams_file, 'r', encoding='utf-8') as f:
                teams_data = json.load(f)
                teams = {}
                for item in teams_data:
                    teams[item['id']] = {
                        'name': item['name'],
                        'id': item['id']
                    }
                return teams
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading teams: {e}")
    return {}

@app.route('/')
def index():
    return redirect(url_for('automations'))

@app.route('/automations')
def automations():
    # Use direct JSON loading instead of config manager
    automations_data = load_automations()

    destination_groups_data = load_destination_groups()

    # Load CRM labels
    crm_labels_file = os.path.join(os.path.dirname(__file__), 'crm_labels.json')
    crm_labels = []
    try:
        if os.path.exists(crm_labels_file):
            with open(crm_labels_file, 'r', encoding='utf-8') as f:
                crm_labels = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading CRM labels: {e}")
        crm_labels = []

    # Get scrollTo parameter for viewport adjustment
    scroll_to = request.args.get('scrollTo')

    return render_template('automations.html',
                         automations=automations_data,
                         destination_groups=destination_groups_data,
                         crm_labels=crm_labels,
                         scroll_to=scroll_to)

@app.route('/automations/update', methods=['POST'])
def update_automation():
    """Update individual automation field using direct JSON"""
    data = request.get_json()
    automation_id = data.get('id')
    field = data.get('field')
    value = data.get('value')

    # Load automations directly from JSON
    automations = load_automations()

    if automation_id in automations:
        # Update the field
        if field == 'applicable_destinations':
            automations[automation_id][field] = value if isinstance(value, list) else []
        else:
            automations[automation_id][field] = value

        # Save directly to JSON
        try:
            save_automations(automations)
            return jsonify({'success': True})
        except Exception as e:
            print(f"JSON save failed: {e}")
            return jsonify({'success': False, 'error': f'Save failed: {str(e)}'})

    return jsonify({'success': False, 'error': 'Automation not found'})

@app.route('/automations/create', methods=['POST'])
def create_automation():
    """Create a new automation using direct JSON"""
    try:
        data = request.get_json()
        automation_id = data.get('id')
        automation_data = data.get('automation', {})

        if not automation_id or not automation_data:
            return jsonify({'success': False, 'error': 'Automation ID and data are required'})

        # Load current automations
        automations = load_automations()

        # Check if automation already exists
        if automation_id in automations:
            return jsonify({'success': False, 'error': f'Automation {automation_id} already exists'})

        # Add the new automation
        automations[automation_id] = automation_data

        # Save directly to JSON
        try:
            save_automations(automations)
            return jsonify({
                'success': True,
                'message': f'Automation {automation_id} created successfully',
                'automation_id': automation_id
            })
        except Exception as e:
            print(f"JSON save failed: {e}")
            return jsonify({'success': False, 'error': f'Save failed: {str(e)}'})

    except Exception as e:
        print(f"Error creating automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/automations/save_all', methods=['POST'])
def save_all_automations():
    """Save all automations data from the frontend form using direct JSON"""
    try:
        data = request.get_json()
        automations_data = data.get('automations', {})

        if not automations_data:
            return jsonify({'success': False, 'error': 'No automation data provided'})

        # Validate the data structure
        for automation_id, automation in automations_data.items():
            if not isinstance(automation, dict):
                return jsonify({'success': False, 'error': f'Invalid data for automation {automation_id}'})

        # Save directly to JSON
        try:
            save_automations(automations_data)
            return jsonify({
                'success': True,
                'message': f'Successfully saved {len(automations_data)} automations',
                'saved_count': len(automations_data),
                'errors': []
            })
        except Exception as e:
            print(f"JSON save failed: {e}")
            return jsonify({'success': False, 'error': f'Save failed: {str(e)}'})

    except Exception as e:
        print(f"Error saving all automations: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/automations/delete/<automation_id>', methods=['DELETE'])
def delete_automation(automation_id):
    """Delete an automation using direct JSON and renumber remaining automations"""
    try:
        # Ensure automation_id is a string
        automation_id = str(automation_id)

        print(f"Attempting to delete automation {automation_id}")

        # Load automations directly from JSON
        automations = load_automations()

        if automation_id not in automations:
            print(f"Automation {automation_id} not found in JSON file")
            return jsonify({'success': False, 'error': f'Automation {automation_id} not found'})

        # Get automation name for response
        automation_name = automations[automation_id].get("name", f"Automation {automation_id}")

        # Delete from JSON
        del automations[automation_id]

        # Renumber remaining automations
        if automations:
            # Sort remaining automation IDs numerically
            sorted_ids = sorted(automations.keys(), key=int)

            # Create new automations dict with sequential numbering
            renumbered_automations = {}
            for new_id, old_id in enumerate(sorted_ids, 1):
                new_id_str = str(new_id)
                renumbered_automations[new_id_str] = automations[old_id]

            automations = renumbered_automations

        # Save directly to JSON
        try:
            save_automations(automations)
            print(f"JSON delete and renumber successful for automation {automation_id}")
            return jsonify({
                'success': True,
                'message': f'Automation "{automation_name}" deleted successfully',
                'automation_id': automation_id
            })
        except Exception as e:
            print(f"JSON save failed: {e}")
            return jsonify({'success': False, 'error': f'Save failed: {str(e)}'})

    except Exception as e:
        print(f"Error deleting automation: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/destinations')
def destinations():
    destinations_data = load_destinations()
    return render_template('destinations.html', destinations=destinations_data)

@app.route('/destinations/update', methods=['POST'])
def update_destination():
    data = request.get_json()
    destination_id = data.get('id')
    field = data.get('field')
    value = data.get('value')

    destinations = load_destinations()
    if destination_id in destinations:
        destinations[destination_id][field] = value
        with open(DESTINATIONS_FILE, 'w') as f:
            json.dump(destinations, f, indent=2)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Destination not found'})

@app.route('/employees')
def employees():
    employees_data = load_employees()
    teams_data = load_teams()
    return render_template('employees.html', employees=employees_data, teams=teams_data)

@app.route('/employees/update', methods=['POST'])
def update_employee():
    data = request.get_json()
    employee_id = data.get('id')
    field = data.get('field')
    value = data.get('value')

    employees = load_employees()
    if employee_id in employees:
        employees[employee_id][field] = value
        with open(EMPLOYEES_FILE, 'w') as f:
            json.dump(employees, f, indent=2)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Employee not found'})

@app.route('/api/destinations')
def api_destinations():
    return jsonify(load_destinations())

@app.route('/api/employees')
def api_employees():
    return jsonify(load_employees())

@app.route('/destination-groups')
def destination_groups():
    groups_data = load_destination_groups()
    destinations_data = load_destinations()
    employees_data = load_employees()
    return render_template('destination_groups.html',
                         groups=groups_data,
                         destinations=destinations_data,
                         employees=employees_data)

@app.route('/destination-groups/create', methods=['POST'])
def create_destination_group():
    data = request.get_json()
    group_name = data.get('name')
    destination_ids = data.get('destination_ids', [])
    employee_ids = data.get('employee_ids', [])

    if not group_name:
        return jsonify({'success': False, 'error': 'Group name is required'})

    groups = load_destination_groups()
    destinations = load_destinations()
    employees = load_employees()

    # Create the group
    group_id = str(len(groups) + 1)
    groups[group_id] = {
        'name': group_name,
        'destination_ids': destination_ids,
        'employee_ids': employee_ids,
        'created_at': datetime.now().isoformat()
    }

    save_destination_groups(groups)

    # Auto-generate destination config
    generate_destination_config(group_name, destination_ids, employee_ids)

    return jsonify({'success': True, 'group_id': group_id})

@app.route('/destination-groups/update', methods=['POST'])
def update_destination_group():
    data = request.get_json()
    group_id = data.get('id')
    field = data.get('field')
    value = data.get('value')

    groups = load_destination_groups()
    if group_id in groups:
        groups[group_id][field] = value
        save_destination_groups(groups)

        # Regenerate config if destinations or employees changed
        if field in ['destination_ids', 'employee_ids']:
            generate_destination_config(groups[group_id]['name'],
                                      groups[group_id]['destination_ids'],
                                      groups[group_id]['employee_ids'])

        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Group not found'})

@app.route('/destination-groups/delete/<group_id>', methods=['DELETE'])
def delete_destination_group(group_id):
    groups = load_destination_groups()
    configs = load_destination_configs()

    if group_id in groups:
        group_name = groups[group_id]['name']
        del groups[group_id]

        # Remove from configs too
        if group_name in configs:
            del configs[group_name]

        save_destination_groups(groups)
        save_destination_configs(configs)

        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Group not found'})

def generate_destination_config(group_name, destination_ids, employee_ids):
    """Generate destination config in the format expected by the existing system"""
    configs = load_destination_configs()
    employees = load_employees()
    destinations = load_destinations()

    # Create users dictionary
    users = {}
    assigned_emails = []

    for emp_id in employee_ids:
        if emp_id in employees:
            emp = employees[emp_id]
            username_key = emp['username'].lower().replace(' ', '_').replace('-', '_')
            users[username_key] = {
                'name': emp['username'],
                'id': emp_id,
                'email': emp['email']
            }
            assigned_emails.append(emp['email'])

    # Determine base user (first in the list)
    base_user = list(users.keys())[0] if users else None

    # Create the config
    config_name = group_name.lower().replace(' ', '_')
    configs[config_name] = {
        'destination_ids': destination_ids,
        'users': users,
        'base_user': base_user,
        'assigned_users': assigned_emails
    }

    save_destination_configs(configs)

@app.route('/destination-configs')
def destination_configs():
    configs_data = load_destination_configs()
    return render_template('destination_configs.html', configs=configs_data)

@app.route('/api/destination-groups')
def api_destination_groups():
    return jsonify(load_destination_groups())

@app.route('/api/destination-configs')
def api_destination_configs():
    return jsonify(load_destination_configs())

@app.route('/crm-labels')
def crm_labels():
    # Load CRM labels from crm_labels.json
    crm_labels_file = os.path.join(os.path.dirname(__file__), 'crm_labels.json')
    labels = []

    try:
        if os.path.exists(crm_labels_file):
            with open(crm_labels_file, 'r', encoding='utf-8') as f:
                labels = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading CRM labels: {e}")
        labels = []

    return render_template('crm_labels.html', labels=labels)

@app.route('/crm-labels/update-status', methods=['POST'])
def update_crm_label_status():
    data = request.get_json()
    label_id = data.get('id')
    is_active = data.get('active', True)

    crm_labels_file = os.path.join(os.path.dirname(__file__), 'crm_labels.json')

    try:
        # Load current labels
        with open(crm_labels_file, 'r', encoding='utf-8') as f:
            labels = json.load(f)

        # Update the specific label's active status
        for label in labels:
            if label['id'] == label_id:
                label['active'] = is_active
                break

        # Save updated labels
        with open(crm_labels_file, 'w', encoding='utf-8') as f:
            json.dump(labels, f, indent=2, ensure_ascii=False)

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error updating CRM label status: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_data_files()
    app.run(debug=True, host='0.0.0.0', port=5000)
