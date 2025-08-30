"""
Configuration Manager Demo
==========================

Demonstrates the new advanced configuration management system with:
- Version control and change tracking
- Timestamps (created, modified, last_used)
- Better naming without "- UPDATED" suffixes
- YAML format for better readability
- Change history and rollback capability
"""

import json
from datetime import datetime
from config_manager import save_automation, get_automations, get_history, get_stats
from config_manager import config_manager

def demonstrate_config_manager():
    """Demonstrate the new configuration management system"""

    print("🔧 ADVANCED CONFIGURATION MANAGER DEMO")
    print("=" * 60)

    # Show current configuration
    print("\n📋 CURRENT CONFIGURATION:")
    current_config = get_automations()
    print(f"Total automations: {len(current_config.get('automations', {}))}")
    print(f"Last modified: {current_config.get('metadata', {}).get('last_modified', 'Never')}")

    # Demonstrate saving a new automation
    print("\n\n🆕 CREATING NEW AUTOMATION:")
    new_automation = {
        "name": "Hotel Booking Confirmations",
        "crm_label_id": "hotel-booking-label",
        "applicable_destinations": ["93", "111"],
        "enabled": True,
        "assignment_logic": "distribution",
        "rule1_type": "contains",
        "rule1_value": "hotel booking confirmed",
        "rule2_type": "contains",
        "rule2_value": "reference number"
    }

    result = save_automation(new_automation, "demo_user")
    print(f"✅ Result: {result['message']}")
    print(f"   Automation ID: {result['automation_id']}")
    print(f"   Action: {result['action']}")

    # Demonstrate updating an existing automation
    print("\n\n📝 UPDATING EXISTING AUTOMATION:")
    updated_automation = {
        "id": "1",  # Update automation 1
        "name": "Travel Plan Ready Notifications",  # Better name without "- UPDATED"
        "enabled": True,
        "assignment_logic": "base_user",
        "rule1_type": "contains",
        "rule1_value": "je reisplan naar",
        "rule2_type": "contains",
        "rule2_value": "is volledig klaar"
    }

    result = save_automation(updated_automation, "demo_user")
    print(f"✅ Result: {result['message']}")
    print(f"   Action: {result['action']}")

    # Show change history
    print("\n\n📜 CHANGE HISTORY:")
    history = get_history(10)
    for i, entry in enumerate(history[-5:], 1):  # Show last 5 entries
        print(f"{i}. {entry['timestamp'][:19]} | {entry['action']} | '{entry['automation_name']}' | by {entry['user']}")

    # Show statistics
    print("\n\n📊 CONFIGURATION STATISTICS:")
    stats = get_stats()
    print(f"Total Automations: {stats['total_automations']}")
    print(f"Enabled: {stats['enabled_automations']}")
    print(f"Disabled: {stats['disabled_automations']}")
    print(f"Assignment Logic Distribution: {stats['assignment_logic_distribution']}")
    print(f"Most Recently Modified: {stats['most_recently_modified']}")
    print(f"Oldest Automation: {stats['oldest_automation']}")

    # Show YAML configuration structure
    print("\n\n📄 YAML CONFIGURATION STRUCTURE:")
    print("Files created:")
    print("├── automations_config.yaml (main configuration)")
    print("├── automations_history.yaml (change history)")
    print("└── config_backups/ (automatic backups)")

    # Demonstrate export to JSON for compatibility
    print("\n\n🔄 EXPORT TO JSON (for compatibility):")
    export_result = config_manager.export_to_json("automations_export.json")
    print(f"✅ {export_result}")

    # Show the improved configuration
    print("\n\n🎯 FINAL CONFIGURATION OVERVIEW:")
    final_config = get_automations()
    automations = final_config.get("automations", {})

    for automation_id, automation in automations.items():
        status = "✅ ENABLED" if automation.get("enabled", False) else "❌ DISABLED"
        logic = automation.get("assignment_logic", "base_user")
        version = automation.get("version", 1)
        modified = automation.get("last_modified", "Never")[:19]

        print(f"Automation {automation_id}: '{automation.get('name', 'Unnamed')}'")
        print(f"  Status: {status} | Logic: {logic} | Version: {version}")
        print(f"  Last Modified: {modified}")
        print()

def show_file_structure():
    """Show the new file structure"""

    print("\n\n📁 NEW FILE STRUCTURE:")
    print("""
Atlas/
├── automations_config.yaml      # Main configuration (YAML format)
├── automations_history.yaml     # Change history and metadata
├── config_backups/              # Automatic timestamped backups
│   ├── automations_backup_20231201_143022.yaml
│   ├── automations_backup_20231201_150055.yaml
│   └── ...
├── automations.json             # Legacy JSON (for compatibility)
└── web_app.py                   # Updated to use config manager
    """)

def show_benefits():
    """Show the benefits of the new system"""

    print("\n\n🎉 BENEFITS OF NEW CONFIGURATION SYSTEM:")
    print("""
✅ NO MORE "- UPDATED" SUFFIXES
   - Clean, professional naming
   - Automatic version tracking
   - Better change management

✅ COMPLETE VERSION CONTROL
   - Every change tracked with timestamp
   - User attribution for changes
   - Hash-based change detection
   - Automatic backups

✅ RICH METADATA
   - Created/Modified timestamps
   - Version numbers
   - Usage statistics
   - Change history

✅ BETTER FILE FORMAT
   - YAML for human readability
   - Comments support
   - Better structure
   - JSON export for compatibility

✅ CHANGE TRACKING
   - Who made changes and when
   - What was changed
   - Rollback capability
   - Audit trail

✅ AUTOMATIC BACKUPS
   - Timestamped backups
   - Configurable retention
   - Easy recovery
    """)

def demonstrate_yaml_vs_json():
    """Show the difference between YAML and JSON formats"""

    print("\n\n🔍 YAML vs JSON COMPARISON:")
    print("""
📄 JSON Format (old):
{
  "1": {
    "name": "Je reisplan is klaar - UPDATED",
    "enabled": true,
    "assignment_logic": "base_user"
  }
}

📄 YAML Format (new):
automations:
  "1":
    id: "1"
    name: "Travel Plan Ready Notifications"  # Clean name
    enabled: true
    assignment_logic: base_user
    created_at: "2023-12-01T14:30:22.123456"
    created_by: "demo_user"
    last_modified: "2023-12-01T15:00:55.654321"
    last_modified_by: "demo_user"
    version: 3
    usage_count: 0
    last_used: null

metadata:
  version: "1.0.0"
  created_at: "2023-12-01T14:30:22.123456"
  last_modified: "2023-12-01T15:00:55.654321"
  total_automations: 3

change_history:
  - timestamp: "2023-12-01T14:30:22.123456"
    user: "demo_user"
    automation_id: "1"
    action: "updated"
    automation_name: "Travel Plan Ready Notifications"
    old_hash: "abc123"
    new_hash: "def456"
    version: 3
    """)

if __name__ == "__main__":
    demonstrate_config_manager()
    show_file_structure()
    show_benefits()
    demonstrate_yaml_vs_json()

    print("\n" + "=" * 60)
    print("✨ CONFIGURATION MANAGEMENT SYSTEM READY!")
    print("🎯 Your automations now have professional version control!")
    print("=" * 60)
