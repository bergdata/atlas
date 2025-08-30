import json
import os
import re
from pathlib import Path

def create_destinations_json():
    """Create destinations.json with proper encoding and country extraction"""
    # Read the original destinations data
    with open('output/crm_destinations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Process destinations
    processed_destinations = []

    for item in data['items']:
        name = item['name']

        # Extract country name by removing "Riksja" prefix and handling "Family" prefix
        country = name.replace('Riksja ', '').replace('Riksja Family ', '')

        # Handle special characters properly
        country = country.encode('utf-8').decode('utf-8')

        processed_destinations.append({
            'id': item['id'],
            'name': name,
            'country': country,
            'email': item['emailAddress']
        })

    # Save processed destinations
    with open('destinations.json', 'w', encoding='utf-8') as f:
        json.dump(processed_destinations, f, indent=2, ensure_ascii=False)

    print(f"Created destinations.json with {len(processed_destinations)} destinations")

def create_teams_json():
    """Create teams.json with proper team names"""
    # Read the teams data
    with open('output/crm_teams.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Process teams
    processed_teams = []

    for item in data['items']:
        processed_teams.append({
            'id': item['id'],
            'name': item['name']
        })

    # Save processed teams
    with open('teams.json', 'w', encoding='utf-8') as f:
        json.dump(processed_teams, f, indent=2, ensure_ascii=False)

    print(f"Created teams.json with {len(processed_teams)} teams")

def create_crm_labels_json():
    """Create crm_labels.json with proper label data"""
    # Read the labels data
    with open('output/crm_labels.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Process labels
    processed_labels = []

    for item in data['items']:
        processed_labels.append({
            'id': item['id'],
            'name': item['name'],
            'slug': item['slug']
        })

    # Save processed labels
    with open('crm_labels.json', 'w', encoding='utf-8') as f:
        json.dump(processed_labels, f, indent=2, ensure_ascii=False)

    print(f"Created crm_labels.json with {len(processed_labels)} labels")

def create_destination_groups_json():
    """Create destination_groups.json with proper grouping"""
    # Read destinations
    with open('destinations.json', 'r', encoding='utf-8') as f:
        destinations = json.load(f)

    # Read teams
    with open('teams.json', 'r', encoding='utf-8') as f:
        teams = json.load(f)

    # Create destination groups based on countries
    destination_groups = {}

    # Group destinations by country
    country_groups = {}
    for dest in destinations:
        country = dest['country']
        if country not in country_groups:
            country_groups[country] = []
        country_groups[country].append(dest['id'])

    # Create groups
    group_id = 1
    for country, dest_ids in country_groups.items():
        destination_groups[str(group_id)] = {
            'name': country,
            'destination_ids': dest_ids,
            'employee_ids': []  # Will be populated based on team assignments
        }
        group_id += 1

    # Save destination groups
    with open('destination_groups.json', 'w', encoding='utf-8') as f:
        json.dump(destination_groups, f, indent=2, ensure_ascii=False)

    print(f"Created destination_groups.json with {len(destination_groups)} groups")

if __name__ == "__main__":
    create_destinations_json()
    create_teams_json()
    create_crm_labels_json()
    create_destination_groups_json()
    print("All data files created successfully!")
