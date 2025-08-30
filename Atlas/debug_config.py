"""
Debug script to test the configuration manager
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

def test_config_manager():
    """Test the config manager functionality"""

    print("\n🔧 TESTING CONFIG MANAGER...")

    # Test getting automations
    try:
        config_data = get_automations()
        print(f"✅ get_automations() works: {len(config_data.get('automations', {}))} automations found")
    except Exception as e:
        print(f"❌ get_automations() failed: {e}")
        return False

    # Test saving automation
    test_automation = {
        "id": "1",
        "name": "Test Automation",
        "enabled": True,
        "assignment_logic": "base_user"
    }

    try:
        result = save_automation(test_automation, "debug_test")
        print(f"✅ save_automation() works: {result}")
        return result.get("success", False)
    except Exception as e:
        print(f"❌ save_automation() failed: {e}")
        return False

if __name__ == "__main__":
    success = test_config_manager()
    if success:
        print("\n✅ CONFIG MANAGER IS WORKING!")
    else:
        print("\n❌ CONFIG MANAGER HAS ISSUES!")
        print("💡 Consider falling back to JSON-based approach temporarily")
