"""
Automation Configuration Demo
============================

This file demonstrates how the automations configured in the frontend
would work in the Python processing code.

Based on the current automations.json configuration:
- Automation 1: "Je reisplan is klaar" (Distribution logic)
- Automation 2: "Boekingsbevestiging" (Base-User logic)
"""

import json
import os

# Sample configuration based on current automations.json
SAMPLE_AUTOMATIONS = {
    "1": {
        "name": "Je reisplan is klaar",
        "crm_label_id": "c919667d-2ecc-b3c5-aeca-3a0dc5054e8f",
        "applicable_destinations": ["93", "111"],  # Vietnam destinations
        "enabled": True,
        "assignment_logic": "distribution",  # ROUND-ROBIN ASSIGNMENT
        "rule1_type": "contains",
        "rule1_value": "je reisplan naar",
        "rule2_type": "contains",
        "rule2_value": "is klaar"
    },
    "2": {
        "name": "Boekingsbevestiging",
        "crm_label_id": "ec18838b-ee41-8a7f-67f8-3a0dc5057e8d",
        "applicable_destinations": ["93", "111"],  # Vietnam destinations
        "enabled": True,
        "assignment_logic": "base_user",  # NAME/EMAIL SEARCH + FALLBACK
        "rule1_type": "contains",
        "rule1_value": "Boekingsbevestiging reis Riksja"
    }
}

# Sample destination configuration
SAMPLE_DESTINATION_CONFIG = {
    "vietnam": {
        "destination_ids": ["93", "111"],
        "users": {
            "charona.van.ingen@riksjatravel.nl": {
                "name": "Charona van Ingen",
                "id": "5e246d96-0dc0-f08a-c874-3a1120e0d81f",
                "email": "charona.van.ingen@riksjatravel.nl"
            },
            "anne_karlijn.bol@riksjatravel.nl": {
                "name": "Anne-Karlijn Bol",
                "id": "ef64fbec-29b0-43e4-9cd0-7c6ad903934c",
                "email": "anne-karlijn.bol@riksjatravel.nl"
            }
        },
        "base_user": "charona.van.ingen@riksjatravel.nl",
        "assigned_users": [
            "charona.van.ingen@riksjatravel.nl",
            "anne_karlijn.bol@riksjatravel.nl"
        ]
    }
}

def demonstrate_automation_matching():
    """Demonstrate how emails match automations"""

    print("🎯 AUTOMATION MATCHING DEMONSTRATION")
    print("=" * 50)

    # Sample emails that would match the automations
    sample_emails = [
        {
            "subject": "Je reisplan naar Vietnam is klaar voor vertrek",
            "destinationId": "93",
            "expected_automation": "1 (Je reisplan is klaar)",
            "assignment_logic": "distribution"
        },
        {
            "subject": "Boekingsbevestiging reis Riksja Vietnam - 2025",
            "destinationId": "93",
            "expected_automation": "2 (Boekingsbevestiging)",
            "assignment_logic": "base_user"
        },
        {
            "subject": "Algemene vraag over reizen",
            "destinationId": "93",
            "expected_automation": "None",
            "assignment_logic": "N/A"
        }
    ]

    for i, email in enumerate(sample_emails, 1):
        print(f"\n📧 Email {i}:")
        print(f"   Subject: {email['subject']}")
        print(f"   Destination: {email['destinationId']}")
        print(f"   Expected Match: {email['expected_automation']}")

        if email['expected_automation'] != "None":
            print(f"   Assignment Logic: {email['assignment_logic']}")

def demonstrate_assignment_logic():
    """Demonstrate how assignment logic works"""

    print("\n\n👥 ASSIGNMENT LOGIC DEMONSTRATION")
    print("=" * 50)

    # Distribution Logic Example
    print("\n📊 DISTRIBUTION LOGIC (Automation 1):")
    print("   Users: ['charona.van.ingen@riksjatravel.nl', 'anne_karlijn.bol@riksjatravel.nl']")
    print("   Assignment Pattern:")

    users = ["charona.van.ingen@riksjatravel.nl", "anne_karlijn.bol@riksjatravel.nl"]
    for i in range(6):
        assigned_user = users[i % len(users)]
        print(f"   Email {i+1} → {assigned_user}")

    # Base-User Logic Example
    print("\n🔍 BASE-USER LOGIC (Automation 2):")
    print("   Searches email content for:")
    print("   - Employee names: 'Charona van Ingen', 'Anne-Karlijn Bol'")
    print("   - Employee emails: 'charona.van.ingen@riksjatravel.nl', 'anne_karlijn.bol@riksjatravel.nl'")
    print("   - If no match found → uses base_user: 'charona.van.ingen@riksjatravel.nl'")

    sample_scenarios = [
        {
            "email_content": "Dear Charona van Ingen, your booking is confirmed...",
            "match_type": "name",
            "assigned_to": "charona.van.ingen@riksjatravel.nl"
        },
        {
            "email_content": "Please contact anne-karlijn.bol@riksjatravel.nl for details...",
            "match_type": "email",
            "assigned_to": "anne_karlijn.bol@riksjatravel.nl"
        },
        {
            "email_content": "General inquiry about Vietnam travel...",
            "match_type": "no match",
            "assigned_to": "charona.van.ingen@riksjatravel.nl (base_user)"
        }
    ]

    for scenario in sample_scenarios:
        print(f"\n   Scenario: {scenario['email_content'][:50]}...")
        print(f"   Match Type: {scenario['match_type']}")
        print(f"   Assigned To: {scenario['assigned_to']}")

def demonstrate_rule_matching():
    """Demonstrate how rule matching works"""

    print("\n\n🎯 RULE MATCHING DEMONSTRATION")
    print("=" * 50)

    # Automation 1 Rules
    print("\n📋 Automation 1 Rules:")
    print("   Rule 1: contains 'je reisplan naar'")
    print("   Rule 2: contains 'is klaar'")
    print("   Pattern: [any text...] + je reisplan naar + [any text...] + is klaar + [any text...]")

    automation1_examples = [
        ("✅ MATCH: Je reisplan naar Vietnam is klaar voor vertrek", True),
        ("❌ NO MATCH: Je reisplan naar Vietnam wordt verwerkt", False),
        ("❌ NO MATCH: Vietnam reis is klaar", False),
        ("✅ MATCH: Update: je reisplan naar Thailand is klaar nu", True)
    ]

    for example, matches in automation1_examples:
        print(f"   {example}")

    # Automation 2 Rules
    print("\n📋 Automation 2 Rules:")
    print("   Rule 1: contains 'Boekingsbevestiging reis Riksja'")
    print("   Pattern: [any text...] + Boekingsbevestiging reis Riksja + [any text...]")

    automation2_examples = [
        ("✅ MATCH: Boekingsbevestiging reis Riksja Vietnam 2025", True),
        ("❌ NO MATCH: Boekingsbevestiging andere maatschappij", False),
        ("✅ MATCH: Urgent: Boekingsbevestiging reis Riksja Thailand", True)
    ]

    for example, matches in automation2_examples:
        print(f"   {example}")

def show_processing_flow():
    """Show the complete email processing flow"""

    print("\n\n🔄 COMPLETE PROCESSING FLOW")
    print("=" * 50)

    print("""
📧 EMAIL PROCESSING STEPS:

1. 📥 Retrieve emails from CRM API
2. 📝 Extract last_email and previous_email content
3. 🎯 Check each enabled automation:
   ├── ✅ Check if destination is applicable
   ├── 🎯 Check if subject matches ALL rules
   └── 👥 Apply assignment logic (distribution/base_user)
4. 📊 Generate assignment report
5. 💾 Save processed data to JSON

🎯 AUTOMATION EVALUATION ORDER:

For each email, automations are checked in order (1, 2, 3...):
- First matching automation wins
- Disabled automations are skipped
- If no automation matches → email remains unassigned

📊 ASSIGNMENT TRACKING:

- Distribution: Uses email index for round-robin
- Base-User: Searches content, falls back to base_user
- Results saved in 'riksja_employee' column
    """)

def main():
    """Main demonstration function"""

    print("🚀 AUTOMATION CONFIGURATION DEMO")
    print("=" * 60)
    print("Based on frontend configuration with 2 active automations")
    print()

    # Show current configuration
    print("⚙️  CURRENT CONFIGURATION:")
    print(json.dumps(SAMPLE_AUTOMATIONS, indent=2))
    print()

    # Run demonstrations
    demonstrate_automation_matching()
    demonstrate_assignment_logic()
    demonstrate_rule_matching()
    show_processing_flow()

    print("\n" + "=" * 60)
    print("✨ CONFIGURATION READY FOR PRODUCTION USE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
