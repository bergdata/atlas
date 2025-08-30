"""
Clean up automation names by removing "- UPDATED" suffixes
"""

import json
import os

def clean_automation_names():
    """Remove '- UPDATED' suffixes from automation names"""

    json_file = "automations.json"

    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found")
        return False

    print(f"📁 Found {json_file}, cleaning up names...")

    # Load current data
    try:
        with open(json_file, 'r') as f:
            automations = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {json_file}: {e}")
        return False

    # Clean up names
    cleaned_count = 0
    for automation_id, automation in automations.items():
        original_name = automation.get('name', '')
        print(f"🔍 Checking: '{original_name}'")

        # Check for various "- UPDATED" patterns
        clean_name = original_name
        updated_patterns = [' - UPDATED', '- UPDATED', ' -UPDATED', '-UPDATED']

        for pattern in updated_patterns:
            if clean_name.endswith(pattern):
                clean_name = clean_name.replace(pattern, '').strip()
                print(f"   Found pattern: '{pattern}'")
                break

        if clean_name != original_name:
            automation['name'] = clean_name
            cleaned_count += 1
            print(f"✅ Cleaned: '{original_name}' → '{clean_name}'")
        else:
            print(f"   No pattern found for: '{original_name}'")

    if cleaned_count == 0:
        print("ℹ️  No names needed cleaning")
        return True

    # Save cleaned data
    try:
        with open(json_file, 'w') as f:
            json.dump(automations, f, indent=2, ensure_ascii=False)
        print(f"✅ Successfully cleaned {cleaned_count} automation names")
        return True
    except Exception as e:
        print(f"❌ Error saving cleaned data: {e}")
        return False

if __name__ == "__main__":
    print("🧹 CLEANING AUTOMATION NAMES")
    print("=" * 30)

    success = clean_automation_names()
    if success:
        print("\n🎉 Names cleaned successfully!")
        print("💡 Your automations will now show clean names without '- UPDATED' suffixes")
    else:
        print("\n❌ Failed to clean names")
