"""
Migrate existing JSON automations to YAML config manager
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from config_manager import config_manager
    print("✅ Config manager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import config manager: {e}")
    sys.exit(1)

def migrate_automations():
    """Migrate existing automations.json to YAML format"""

    json_file = "automations.json"

    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found")
        return False

    print(f"📁 Found {json_file}, migrating to YAML format...")

    # Import from JSON
    result = config_manager.import_from_json(json_file, "migration_system")

    if result["success"]:
        print(f"✅ Migration successful!")
        print(f"   Imported {result['imported_count']} automations")

        # Show the results
        for i, res in enumerate(result["results"], 1):
            if res["success"]:
                print(f"   {i}. ✅ {res['message']}")
            else:
                print(f"   {i}. ❌ {res.get('error', 'Unknown error')}")

        return True
    else:
        print(f"❌ Migration failed: {result.get('error', 'Unknown error')}")
        return False

def verify_migration():
    """Verify that migration worked correctly"""

    print("\n🔍 VERIFYING MIGRATION...")

    # Get automations from config manager
    config_data = config_manager.get_automation_config()
    automations = config_data.get("automations", {})

    print(f"Found {len(automations)} automations in YAML config")

    # Compare with original JSON
    try:
        import json
        with open("automations.json", "r") as f:
            original_data = json.load(f)

        print(f"Original JSON had {len(original_data)} automations")

        # Check if all automations were migrated
        migrated_ids = set(automations.keys())
        original_ids = set(original_data.keys())

        if migrated_ids == original_ids:
            print("✅ All automation IDs migrated successfully")
            return True
        else:
            missing = original_ids - migrated_ids
            extra = migrated_ids - original_ids
            if missing:
                print(f"❌ Missing automations: {missing}")
            if extra:
                print(f"⚠️  Extra automations: {extra}")
            return False

    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

if __name__ == "__main__":
    print("🔄 AUTOMATION MIGRATION: JSON → YAML")
    print("=" * 40)

    success = migrate_automations()
    if success:
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        print("💡 Your automations are now using the advanced YAML config system")
    else:
        print("\n❌ Migration failed!")
        print("💡 Consider using the fallback JSON approach temporarily")
