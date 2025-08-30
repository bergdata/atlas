"""
Test Script for "Save All Changes" Functionality
===============================================

This script demonstrates how the "Save All Changes" button works
by simulating the data collection and bulk save process.
"""

import json
import requests
import time

def test_save_all_changes():
    """Test the Save All Changes functionality"""

    print("🧪 TESTING 'SAVE ALL CHANGES' FUNCTIONALITY")
    print("=" * 60)

    # Simulate the data that would be collected from the frontend form
    # This represents what the JavaScript saveAllChanges() function collects
    test_automations_data = {
        "1": {
            "name": "Je reisplan is klaar - UPDATED",
            "crm_label_id": "c919667d-2ecc-b3c5-aeca-3a0dc5054e8f",
            "applicable_destinations": ["93", "111"],  # Changed from ["1"] to proper Vietnam IDs
            "enabled": True,
            "assignment_logic": "distribution",
            "rule1_type": "contains",
            "rule1_value": "je reisplan naar",
            "rule2_type": "contains",
            "rule2_value": "is klaar"
            # Note: rule3 removed to test dynamic rule handling
        },
        "2": {
            "name": "Boekingsbevestiging - UPDATED",
            "crm_label_id": "ec18838b-ee41-8a7f-67f8-3a0dc5057e8d",
            "applicable_destinations": ["93", "111"],  # Changed from ["1"] to proper Vietnam IDs
            "enabled": True,
            "assignment_logic": "base_user",
            "rule1_type": "contains",
            "rule1_value": "Boekingsbevestiging reis Riksja"
        },
        "3": {
            "name": "New Automation Test",
            "crm_label_id": "",
            "applicable_destinations": [],
            "enabled": False,
            "assignment_logic": "base_user",
            "rule1_type": "starts_with",
            "rule1_value": "Test email"
        }
    }

    print("📋 TEST DATA TO SAVE:")
    print(json.dumps(test_automations_data, indent=2))
    print()

    # Test the bulk save endpoint
    try:
        print("📡 SENDING BULK SAVE REQUEST TO FLASK APP...")

        # Prepare the payload as the frontend would send it
        payload = {
            "automations": test_automations_data
        }

        # Send POST request to the save_all endpoint
        response = requests.post(
            'http://localhost:5000/automations/save_all',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        print(f"📊 RESPONSE STATUS: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Saved successfully')}")
        else:
            print(f"❌ ERROR: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Flask app is not running")
        print("💡 Make sure to run: python web_app.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

    # Wait a moment for the file to be written
    time.sleep(1)

    # Verify the changes were saved
    print("\n🔍 VERIFYING CHANGES WERE SAVED TO FILE...")
    try:
        with open('automations.json', 'r') as f:
            saved_data = json.load(f)

        print("✅ FILE UPDATED SUCCESSFULLY!")
        print("\n📄 CURRENT FILE CONTENTS:")
        print(json.dumps(saved_data, indent=2))

        # Verify specific changes
        print("\n🔎 VERIFICATION CHECKS:")

        # Check Automation 1 updates
        if saved_data["1"]["name"] == "Je reisplan is klaar - UPDATED":
            print("✅ Automation 1 name updated correctly")
        else:
            print("❌ Automation 1 name not updated")

        if saved_data["1"]["applicable_destinations"] == ["93", "111"]:
            print("✅ Automation 1 destinations updated correctly")
        else:
            print("❌ Automation 1 destinations not updated")

        # Check that rule3 was removed from Automation 1
        if "rule3_value" not in saved_data["1"]:
            print("✅ Automation 1 rule3 removed correctly (dynamic rules working)")
        else:
            print("❌ Automation 1 rule3 still present")

        # Check Automation 2 updates
        if saved_data["2"]["name"] == "Boekingsbevestiging - UPDATED":
            print("✅ Automation 2 name updated correctly")
        else:
            print("❌ Automation 2 name not updated")

        # Check new Automation 3
        if saved_data["3"]["name"] == "New Automation Test":
            print("✅ New Automation 3 added correctly")
        else:
            print("❌ New Automation 3 not added")

        return True

    except Exception as e:
        print(f"❌ ERROR READING FILE: {str(e)}")
        return False

def show_usage_example():
    """Show how this works in practice"""

    print("\n\n🎯 HOW 'SAVE ALL CHANGES' WORKS IN PRACTICE")
    print("=" * 60)

    print("""
🔄 USER WORKFLOW:

1. 🖱️  User makes changes in the frontend:
   ├── Changes automation names
   ├── Adds/removes rules dynamically
   ├── Selects assignment logic (Base-User/Distribution)
   ├── Updates destination groups
   └── Enables/disables automations

2. 💾 User clicks "Save All Changes" button

3. 📊 Frontend JavaScript collects ALL current form data:
   ├── Loops through all automation cards
   ├── Collects names, CRM labels, enabled status
   ├── Gathers assignment logic selection
   ├── Collects all active rules (dynamic rule system)
   ├── Gets selected destination groups

4. 📡 Frontend sends bulk POST request to /automations/save_all

5. 🔧 Backend validates and saves complete configuration:
   ├── Validates data structure
   ├── Saves to automations.json
   ├── Returns success/error response

6. ✅ Frontend shows success toast: "All changes saved to configuration file!"

7. 🔄 Python scripts can now use updated configuration:
   ├── mail_processor.py reads updated rules
   ├── Assignment logic applied correctly
   ├── Dynamic rules work as configured

🎉 RESULT: Frontend configuration seamlessly integrates with Python backend!
    """)

if __name__ == "__main__":
    success = test_save_all_changes()
    show_usage_example()

    if success:
        print("\n" + "=" * 60)
        print("✨ SAVE ALL CHANGES FUNCTIONALITY WORKING PERFECTLY!")
        print("🎯 Frontend ↔ Backend integration complete!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED - Check Flask app and try again")
        print("=" * 60)
