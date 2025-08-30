"""
Test script to debug the update automation issue
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

def test_update_enabled():
    """Test updating just the enabled field"""

    print("\n🔧 TESTING UPDATE ENABLED FIELD...")

    # Get current automations
    config_data = get_automations()
    automations = config_data.get("automations", {})
    print(f"Found {len(automations)} automations")

    if "1" in automations:
        automation_1 = automations["1"]
        print(f"Automation 1 current state: enabled={automation_1.get('enabled', 'N/A')}")

        # Try to update just the enabled field
        updated_automation = automation_1.copy()
        updated_automation["enabled"] = True  # Try to enable it
        updated_automation["id"] = "1"  # Make sure ID is included

        print(f"Attempting to save with enabled=True...")

        try:
            result = save_automation(updated_automation, "test_update")
            print(f"✅ Save result: {result}")

            if result.get("success"):
                print("✅ Update successful!")
                return True
            else:
                print(f"❌ Update failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Exception during save: {e}")
            return False
    else:
        print("❌ Automation 1 not found")
        return False

if __name__ == "__main__":
    success = test_update_enabled()
    if success:
        print("\n✅ UPDATE ENABLED FIELD WORKS!")
    else:
        print("\n❌ UPDATE ENABLED FIELD HAS ISSUES!")
        print("💡 This might be the source of the frontend error")
