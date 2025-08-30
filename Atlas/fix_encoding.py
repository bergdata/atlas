#!/usr/bin/env python3
"""
Script to fix UTF-8 encoding issues in JSON files
"""
import json
import re

def fix_encoding_issues(text):
    """Fix common UTF-8 encoding issues"""
    # Fix double-encoded characters
    fixes = {
        r'\\u00c3\\u00ab': 'ë',  # ë
        r'\\u00c3\\u00a9': 'é',  # é
        r'\\u00c3\\u00a8': 'è',  # è
        r'\\u00c3\\u00a1': 'á',  # á
        r'\\u00c3\\u00b3': 'ó',  # ó
        r'\\u00c3\\u00ba': 'ú',  # ú
        r'\\u00c3\\u00b1': 'ñ',  # ñ
        r'\\u00c3\\u00bc': 'ü',  # ü
        r'\\u00c3\\u00b6': 'ö',  # ö
        r'\\u00c3\\u00a4': 'ä',  # ä
        r'\\u00c3\\u00a7': 'ç',  # ç
        r'\\u00c3\\u00bf': 'ÿ',  # ÿ
        r'\\u00c3\\u00ae': 'î',  # î
        r'\\u00c3\\u00af': 'ï',  # ï
        r'\\u00c3\\u00ad': 'í',  # í
        r'\\u00c3\\u00aa': 'ê',  # ê
        r'\\u00c3\\u00b4': 'ô',  # ô
        r'\\u00c3\\u00bb': 'û',  # û
        r'\\u00c3\\u00a0': 'à',  # à
        r'\\u00c3\\u00a2': 'â',  # â
        r'\\u00c3\\u00a6': 'æ',  # æ
        r'\\u00c3\\u00b8': 'ø',  # ø
        r'\\u00c3\\u00a5': 'å',  # å
        # Also fix single-encoded versions that might appear
        r'Ã«': 'ë',
        r'Ã©': 'é',
        r'Ã¨': 'è',
        r'Ã¡': 'á',
        r'Ã³': 'ó',
        r'Ãº': 'ú',
        r'Ã±': 'ñ',
        r'Ã¼': 'ü',
        r'Ã¶': 'ö',
        r'Ã¤': 'ä',
        r'Ã§': 'ç',
        r'Ã¿': 'ÿ',
        r'Ã®': 'î',
        r'Ã¯': 'ï',
        r'Ã­': 'í',
        r'Ãª': 'ê',
        r'Ã´': 'ô',
        r'Ã»': 'û',
        r'Ã ': 'à',
        r'Ã¢': 'â',
        r'Ã¦': 'æ',
        r'Ã¸': 'ø',
        r'Ã¥': 'å',
    }

    for pattern, replacement in fixes.items():
        text = re.sub(pattern, replacement, text)

    return text

def fix_json_file(filepath):
    """Fix encoding issues in a JSON file"""
    print(f"Fixing encoding in {filepath}...")

    # Read the file as raw text
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Fix encoding issues
    fixed_content = fix_encoding_issues(content)

    # Write back the fixed content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"✅ Fixed encoding in {filepath}")

def main():
    """Main function to fix encoding in all JSON files"""
    import os

    files_to_fix = [
        'crm_labels.json',
        'destinations.json',
        'employees.json',
        'teams.json'
    ]

    for filename in files_to_fix:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            fix_json_file(filepath)
        else:
            print(f"⚠️  File not found: {filename}")

    print("\n🎉 All encoding issues have been fixed!")

if __name__ == '__main__':
    main()
