"""
Test if config manager is actually saving data
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from config_manager import save_automation, get_automations
    print("✅ Config manager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import config manager: {e}")
    sys.exit(1)

def test_save_and_retrieve():
    """Test saving and retrieving data"""

    print("\n💾 TESTING SAVE AND RETRIEVE...")

    # Create test automation
    test_automation = {
        "id": "999",
        "name": "Test Migration Automation",
        "enabled": True,
        "assignment_logic": "base_user",
        "rule1_type": "contains",
        "rule1_value": "test migration"
    }

    print("Saving test automation...")
    result = save_automation(test_automation, "test_user")
    print(f"Save result: {result}")

    if result.get("success"):
        print("✅ Save successful, now retrieving...")

        # Retrieve all automations
        config_data = get_automations()
        automations = config_data.get("automations", {})

        print(f"Retrieved {len(automations)} automations")

        # Check if our test automation is there
        if "999" in automations:
            retrieved = automations["999"]
            print(f"✅ Found test automation: {retrieved.get('name')}")
            print(f"   Enabled: {retrieved.get('enabled')}")
            print(f"   Assignment Logic: {retrieved.get('assignment_logic')}")
            return True
        else:
            print("❌ Test automation not found in retrieved data")
            print(f"Available IDs: {list(automations.keys())}")
            return False
    else:
        print(f"❌ Save failed: {result.get('error')}")
        return False

def check_yaml_files():
    """Check if YAML files exist and have content"""

    print("\n📁 CHECKING YAML FILES...")

    files_to_check = [
        "automations_config.yaml",
        "automations_history.yaml"
    ]

    for filename in files_to_check:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename}: {size} bytes")

            # Show first few lines
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()[:5]
                    print(f"   First 5 lines: {lines}")
            except Exception as e:
                print(f"   Error reading: {e}")
        else:
            print(f"❌ {filename}: File not found")

if __name__ == "__main__":
    success = test_save_and_retrieve()
    check_yaml_files()

    if success:
        print("\n✅ CONFIG MANAGER IS WORKING!")
    else:
        print("\n❌ CONFIG MANAGER HAS ISSUES!")
        print("💡 The data is not being saved or retrieved correctly")
