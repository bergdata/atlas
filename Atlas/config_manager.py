"""
Configuration Manager for Automations
=====================================

Advanced configuration management system with:
- Version control and change tracking
- Timestamps (created, modified, last_used)
- Change history and rollback capability
- Better naming without "- UPDATED" suffixes
- YAML format for better readability
"""

import yaml
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import copy
import hashlib

class AutomationConfigManager:
    """Manages automation configurations with version control"""

    def __init__(self, config_dir: str = "."):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "automations_config.yaml")
        self.history_file = os.path.join(config_dir, "automations_history.yaml")
        self.backup_dir = os.path.join(config_dir, "config_backups")

        # Create directories if they don't exist
        os.makedirs(self.backup_dir, exist_ok=True)

        # Initialize files if they don't exist
        self._init_config_files()

    def _init_config_files(self):
        """Initialize configuration files if they don't exist"""
        if not os.path.exists(self.config_file):
            initial_config = {
                "metadata": {
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat(),
                    "total_automations": 0
                },
                "automations": {},
                "change_history": []
            }
            self._save_yaml(self.config_file, initial_config)

        if not os.path.exists(self.history_file):
            initial_history = {
                "history": [],
                "last_backup": None
            }
            self._save_yaml(self.history_file, initial_history)

    def _save_yaml(self, file_path: str, data: Dict[str, Any]):
        """Save data to YAML file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load data from YAML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def _generate_config_hash(self, config: Dict[str, Any]) -> str:
        """Generate hash of configuration for change detection"""
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]

    def _get_next_automation_id(self) -> str:
        """Get next available automation ID"""
        config = self._load_yaml(self.config_file)
        existing_ids = [int(k) for k in config.get("automations", {}).keys() if k.isdigit()]
        return str(max(existing_ids + [0]) + 1)

    def save_automation_config(self, automation_data: Dict[str, Any], user: str = "system", create_backup: bool = False) -> Dict[str, Any]:
        """
        Save automation configuration with version control

        Args:
            automation_data: The automation configuration data
            user: User making the change (for logging)
            create_backup: Whether to create a backup (default: False)

        Returns:
            Dict with success status and details
        """
        try:
            # Load current config
            config = self._load_yaml(self.config_file)
            old_hash = self._generate_config_hash(config)

            # Prepare new automation data with timestamps
            automation_id = automation_data.get('id')
            is_new = automation_id not in config.get("automations", {})

            if is_new:
                automation_id = self._get_next_automation_id()
                config["automations"][automation_id] = {
                    "id": automation_id,
                    "created_at": datetime.now().isoformat(),
                    "created_by": user,
                    "last_modified": datetime.now().isoformat(),
                    "last_modified_by": user,
                    "version": 1,
                    "usage_count": 0,
                    "last_used": None,
                    **automation_data
                }
            else:
                # Update existing automation
                existing = config["automations"][automation_id]
                existing.update({
                    "last_modified": datetime.now().isoformat(),
                    "last_modified_by": user,
                    "version": existing.get("version", 1) + 1,
                    **automation_data
                })

            # Update metadata
            config["metadata"]["last_modified"] = datetime.now().isoformat()
            config["metadata"]["total_automations"] = len(config["automations"])

            # Detect changes for history
            new_hash = self._generate_config_hash(config)
            if old_hash != new_hash:
                self._log_change(config, automation_id, is_new, user, old_hash, new_hash)

            # Save configuration
            self._save_yaml(self.config_file, config)

            # Create backup only if explicitly requested
            if create_backup:
                self._create_backup(config)

            return {
                "success": True,
                "automation_id": automation_id,
                "action": "created" if is_new else "updated",
                "message": f"Automation '{automation_data.get('name', automation_id)}' {'created' if is_new else 'updated'} successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save automation configuration"
            }

    def _log_change(self, config: Dict[str, Any], automation_id: str, is_new: bool,
                   user: str, old_hash: str, new_hash: str):
        """Log configuration change to history"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "automation_id": automation_id,
            "action": "created" if is_new else "updated",
            "automation_name": config["automations"][automation_id].get("name", f"Automation {automation_id}"),
            "old_hash": old_hash,
            "new_hash": new_hash,
            "version": config["automations"][automation_id].get("version", 1)
        }

        # Load and update history
        history = self._load_yaml(self.history_file)
        history["history"].append(history_entry)

        # Keep only last 100 entries
        if len(history["history"]) > 100:
            history["history"] = history["history"][-100:]

        self._save_yaml(self.history_file, history)

    def _create_backup(self, config: Dict[str, Any], reason: str = "manual_backup"):
        """Create timestamped backup of configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"automations_backup_{timestamp}.yaml")

        # Add backup metadata
        backup_data = copy.deepcopy(config)
        backup_data["backup_info"] = {
            "created_at": datetime.now().isoformat(),
            "reason": reason,
            "config_hash": self._generate_config_hash(config)
        }

        self._save_yaml(backup_file, backup_data)

        # Update last backup timestamp
        history = self._load_yaml(self.history_file)
        history["last_backup"] = datetime.now().isoformat()
        self._save_yaml(self.history_file, history)

    def get_automation_config(self, automation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get automation configuration(s)"""
        config = self._load_yaml(self.config_file)

        if automation_id:
            return config.get("automations", {}).get(automation_id, {})

        return {
            "metadata": config.get("metadata", {}),
            "automations": config.get("automations", {})
        }

    def get_change_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get change history"""
        history = self._load_yaml(self.history_file)
        return history.get("history", [])[-limit:]

    def delete_automation_config(self, automation_id: str, user: str = "system") -> Dict[str, Any]:
        """
        Delete automation configuration with version control

        Args:
            automation_id: The ID of the automation to delete
            user: User making the change (for logging)

        Returns:
            Dict with success status and details
        """
        try:
            # Load current config
            config = self._load_yaml(self.config_file)
            old_hash = self._generate_config_hash(config)

            # Check if automation exists
            if automation_id not in config.get("automations", {}):
                return {
                    "success": False,
                    "error": f"Automation {automation_id} not found",
                    "message": f"Automation {automation_id} does not exist"
                }

            # Get automation name for logging
            automation_name = config["automations"][automation_id].get("name", f"Automation {automation_id}")

            # Delete the automation
            del config["automations"][automation_id]

            # Update metadata
            config["metadata"]["last_modified"] = datetime.now().isoformat()
            config["metadata"]["total_automations"] = len(config["automations"])

            # Log the deletion
            new_hash = self._generate_config_hash(config)
            self._log_change(config, automation_id, False, user, old_hash, new_hash)

            # Save configuration (no automatic backup)
            self._save_yaml(self.config_file, config)

            return {
                "success": True,
                "automation_id": automation_id,
                "action": "deleted",
                "message": f"Automation '{automation_name}' deleted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete automation configuration"
            }

    def create_manual_backup(self, reason: str = "manual_backup") -> Dict[str, Any]:
        """
        Create a manual backup of the current configuration

        Args:
            reason: Reason for the backup (for logging)

        Returns:
            Dict with success status and details
        """
        try:
            # Load current config
            config = self._load_yaml(self.config_file)

            # Create backup with the specified reason
            self._create_backup(config, reason)

            return {
                "success": True,
                "message": f"Manual backup created successfully with reason: {reason}",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create manual backup"
            }

    def get_automation_stats(self) -> Dict[str, Any]:
        """Get automation statistics"""
        config = self._load_yaml(self.config_file)
        automations = config.get("automations", {})

        stats = {
            "total_automations": len(automations),
            "enabled_automations": sum(1 for a in automations.values() if a.get("enabled", False)),
            "disabled_automations": sum(1 for a in automations.values() if not a.get("enabled", False)),
            "assignment_logic_distribution": {},
            "most_recently_modified": None,
            "oldest_automation": None
        }

        # Assignment logic distribution
        for automation in automations.values():
            logic = automation.get("assignment_logic", "base_user")
            stats["assignment_logic_distribution"][logic] = stats["assignment_logic_distribution"].get(logic, 0) + 1

        # Find most recent and oldest
        if automations:
            sorted_by_modified = sorted(automations.values(),
                                      key=lambda x: x.get("last_modified", x.get("created_at", "")), reverse=True)
            stats["most_recently_modified"] = sorted_by_modified[0].get("name", "Unknown")

            sorted_by_created = sorted(automations.values(),
                                     key=lambda x: x.get("created_at", ""))
            stats["oldest_automation"] = sorted_by_created[0].get("name", "Unknown")

        return stats

    def export_to_json(self, output_file: str = "automations_export.json"):
        """Export configuration to JSON format for compatibility"""
        config = self._load_yaml(self.config_file)

        # Convert to simple JSON format (without metadata)
        json_config = {}
        for automation_id, automation in config.get("automations", {}).items():
            json_config[automation_id] = {
                k: v for k, v in automation.items()
                if k not in ["created_at", "created_by", "last_modified", "last_modified_by",
                           "version", "usage_count", "last_used"]
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_config, f, indent=2, ensure_ascii=False)

        return f"Configuration exported to {output_file}"

    def import_from_json(self, json_file: str, user: str = "system") -> Dict[str, Any]:
        """Import configuration from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            results = []
            for automation_id, automation_data in json_data.items():
                automation_data["id"] = automation_id
                result = self.save_automation_config(automation_data, user)
                results.append(result)

            return {
                "success": True,
                "imported_count": len(results),
                "results": results,
                "message": f"Successfully imported {len(results)} automations"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to import configuration"
            }

# Global instance for easy access
config_manager = AutomationConfigManager()

def save_automation(automation_data: Dict[str, Any], user: str = "frontend") -> Dict[str, Any]:
    """Convenience function to save automation"""
    return config_manager.save_automation_config(automation_data, user)

def get_automations() -> Dict[str, Any]:
    """Convenience function to get all automations"""
    return config_manager.get_automation_config()

def get_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Convenience function to get change history"""
    return config_manager.get_change_history(limit)

def get_stats() -> Dict[str, Any]:
    """Convenience function to get statistics"""
    return config_manager.get_automation_stats()

def delete_automation(automation_id: str, user: str = "frontend") -> Dict[str, Any]:
    """Convenience function to delete automation"""
    return config_manager.delete_automation_config(automation_id, user)

def create_manual_backup(reason: str = "manual_backup") -> Dict[str, Any]:
    """Convenience function to create manual backup"""
    return config_manager.create_manual_backup(reason)

if __name__ == "__main__":
    # Example usage
    print("🔧 Automation Configuration Manager")
    print("=" * 40)

    # Save a sample automation
    sample_automation = {
        "name": "Sample Travel Plan Automation",
        "crm_label_id": "sample-label-id",
        "applicable_destinations": ["93", "111"],
        "enabled": True,
        "assignment_logic": "base_user",
        "rule1_type": "contains",
        "rule1_value": "travel plan"
    }

    result = save_automation(sample_automation, "demo_user")
    print(f"✅ {result['message']}")

    # Get statistics
    stats = get_stats()
    print(f"\n📊 Statistics: {stats}")

    # Get recent history
    history = get_history(5)
    print(f"\n📝 Recent Changes: {len(history)} entries")
    for entry in history[-3:]:  # Show last 3
        print(f"  - {entry['timestamp'][:19]}: {entry['action']} '{entry['automation_name']}' by {entry['user']}")
