import json
import re
from bs4 import BeautifulSoup
import html
import unicodedata
from datetime import datetime

# --- Refined separator regex for email replies ---
separator_pattern = re.compile(
    r'(?:(?:On\s+)?([A-Z][a-z]{2}, [A-Z][a-z]{2} \d{1,2}, \d{4}\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\s+(.+?)\s+wrote:|'  # Format: Fri, Jul 4, 2025 5:42 PM [Sender] wrote:
    r'Van:\s*(.+?)\s*Verzonden:\s*(.+?)(?:\s*(?:Aan:|wrote:))|'  # Format: Van: [Sender] Verzonden: [Date]
    r'From:\s*(.+?)\s*Date:\s*(\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{2}:\d{2})|'  # Format: From: [Sender] Date: DD-MM-YYYY HH:MM:SS
    r'==\s*<(.*?@.+?)>\s*wrote:.*?==\s*(?=\n|$))',  # Format: == <email> wrote: == (only if followed by content or end)
    re.IGNORECASE | re.DOTALL | re.MULTILINE
)

def normalize_text(text):
    """Normalize text by replacing special characters while preserving line breaks."""
    text = unicodedata.normalize('NFKC', text).replace('\u202f', ' ').replace('\u00a0', ' ')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text.strip())
    return text

def format_iso_date(iso_date):
    """Convert ISO date (e.g., 2025-07-16T17:39:55) to 'Weekday, Month Day, Year at Hour:Minute AM/PM'."""
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime('%a, %b %d, %Y at %I:%M %p')
    except ValueError:
        return '(unknown date)'

def parse_date(date_str):
    """Parse various date formats to 'Weekday, Month Day, Year at Hour:Minute AM/PM'."""
    try:
        date_str = date_str.strip()
        for fmt in [
            '%A, %B %d, %Y %I:%M:%S %p',  # Wednesday, July 16, 2025 5:39:55 PM
            '%A, %B %d, %Y %I:%M %p',     # Fri, Jul 4, 2025 5:42 PM
            '%d-%m-%Y %H:%M:%S',          # 11-02-2025 12:01:13
            '%A %d %B %Y %H:%M',          # vrijdag 4 juli 2025 11:38
        ]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%a, %b %d, %Y at %I:%M %p')
            except ValueError:
                continue
        return '(unknown date)'
    except:
        return '(unknown date)'

def extract_sender_date_from_line(line, main_email_from, main_email_date_formatted):
    """Extract sender, email, and date from separator line or use main email metadata."""
    line = normalize_text(line)
    m = re.match(
        r'(?:(?:On\s+)?([A-Z][a-z]{2}, [A-Z][a-z]{2} \d{1,2}, \d{4}\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\s+(.+?)\s+wrote:|'  # Format: Fri, Jul 4, 2025 5:42 PM [Sender] wrote:
        r'Van:\s*(.+?)\s*Verzonden:\s*(.+?)(?:\s*(?:Aan:|wrote:))|'  # Format: Van: [Sender] Verzonden: [Date]
        r'From:\s*(.+?)\s*Date:\s*(\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{2}:\d{2})|'  # Format: From: [Sender] Date: DD-MM-YYYY HH:MM:SS
        r'==\s*<(.*?@.+?)>\s*wrote:.*?==)',  # Format: == <email> wrote: ==
        line, re.IGNORECASE
    )
    if m:
        date_part = m.group(1) or m.group(4) or m.group(6) or ''
        sender_part = m.group(2) or m.group(3) or m.group(5) or m.group(7) or ''
        full_date = parse_date(date_part) if date_part else '(unknown date)'
        sender_part = re.sub(r'\n', '', sender_part).strip()
        sender_clean = re.sub(r'\s*<.+?>$', '', sender_part).strip() or sender_part
        email_match = re.search(r'<(.+?)>', sender_part) or (sender_part if '@' in sender_part else None)
        email = email_match.group(1) if email_match and '<' in email_match.group(0) else sender_part if '@' in sender_part else '(unknown email)'
        return sender_clean or '(Unknown sender)', email, full_date
    return main_email_from, main_email_from, main_email_date_formatted

def clean_email_content(text):
    """Clean email content by removing excessive newlines, signatures, and footers."""
    text = normalize_text(text)
    signature_patterns = [
        r'Hartelijke groet[\s\S]*$',
        r'--\s*$',
    ]
    for pattern in signature_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE).strip()
    footer_patterns = [
        r'Riksja[\s\S]*$',
        r't:\s*\+31.*$',
        r'w:\s*(?:www\.riksjatravel\.nl|Vietnamonline\.nl).*$',
        r'a:\s*Pompoenweg.*$',
        r'KvK:.*$',
        r'\[RIK#\d+\]',
        r'\"Logo\"',
    ]
    for pattern in footer_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE).strip()
    return text if text else '(No content after cleaning)'

try:
    with open('output/processed_emails.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: 'output/processed_emails.json' not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error: Invalid JSON format in 'output/processed_emails.json'.")
    exit(1)

if not isinstance(data, list) or not data:
    print("Error: JSON data is empty or not a list.")
    exit(1)

# Loop through each email in the JSON data
for email_idx, email_data in enumerate(data, start=1):
    # Extract metadata from JSON
    main_email_from = email_data.get('senderAddress', '(unknown from header)')
    main_email_to = email_data.get('toRecipientsJson', '(unknown to header)')
    main_email_date = email_data.get('createdDateTime', '(unknown date)')
    main_email_subject = email_data.get('subject', '(unknown subject)')

    # Convert main_email_date to desired format
    main_email_date_formatted = format_iso_date(main_email_date) if main_email_date != '(unknown date)' else '(unknown date)'

    # Handle case where toRecipientsJson is a JSON string
    if isinstance(main_email_to, str) and (main_email_to.startswith('[') or main_email_to.startswith('{')):
        try:
            to_recipient = json.loads(main_email_to)
            if isinstance(to_recipient, list):
                main_email_to = ', '.join([r.get('emailAddress', {}).get('address', '(unknown)') for r in to_recipient])
            elif isinstance(to_recipient, dict):
                main_email_to = to_recipient.get('emailAddress', {}).get('address', '(unknown)')
        except json.JSONDecodeError:
            main_email_to = '(invalid toRecipientsJson format)'

    html_body = email_data.get('bodyContent', '')
    if not html_body:
        print(f"Error: No bodyContent found in email #{email_idx}.")
        continue

    # Decode HTML entities and convert HTML to plain text
    html_body = html.unescape(html_body)
    soup = BeautifulSoup(html_body, 'html.parser')
    plain_text_body = soup.get_text(separator='\n', strip=True)
    plain_text_body = normalize_text(plain_text_body)

    # Debug: print full plain text to verify content
    print(f"=== Full plain text email body (Email #{email_idx}) ===")
    print(plain_text_body)
    print("====================================\n")

    # Debug: print lines that might be separators
    print(f"=== Potential separator lines (Email #{email_idx}) ===")
    for line in plain_text_body.split('\n'):
        if 'wrote:' in line or 'Van:' in line or 'From:' in line or '== ' in line:
            print(f">>> {line}")
    print("====================================\n")

    # Find all reply separators
    separator_lines = separator_pattern.findall(plain_text_body)
    print(f"Detected separators ({len(separator_lines)}) for Email #{email_idx}:")
    for s in separator_lines:
        print(f">>> {s}")
    print()

    # Split the conversation into parts by separators
    parts = re.split(separator_pattern, plain_text_body)
    print(f"Parts after split: {parts}")
    parts = [p for p in parts if p is not None and p.strip()]  # Remove None and empty parts
    print(f"Filtered parts: {parts}\n")

    # Process segments
    email_segments = []
    current_segment = []
    for part in parts:
        if not part or part.isspace():
            continue
        if separator_pattern.match(part):
            if current_segment:
                email_segments.append(clean_email_content('\n'.join(current_segment)))
                current_segment = []
        else:
            current_segment.append(part)
    if current_segment:
        email_segments.append(clean_email_content('\n'.join(current_segment)))

    # Print summary info
    print(f"=== Email Conversation Analysis (Email #{email_idx}) ===")
    print(f"Main email subject: {main_email_subject}")
    print(f"Main email date: {main_email_date_formatted}")
    print(f"Main email from: {main_email_from}")
    print(f"Main email to: {main_email_to}")
    print(f"Total emails detected in conversation: {len(email_segments)}\n")

    for idx, email in enumerate(email_segments, start=1):
        first_line = email.split('\n', 1)[0].strip()
        sender, email_address, date = extract_sender_date_from_line(first_line, main_email_from, main_email_date_formatted)
        
        # For snippet, take first 150 chars after the first line, excluding signature
        snippet = email.split('\n', 1)[1].strip() if '\n' in email else email.strip()
        snippet = re.sub(r'\s+', ' ', snippet).strip()[:150] + ('...' if len(snippet) > 150 else '')
        
        print(f"--- Email #{idx} ---")
        print(f"From: {sender}")
        print(f"Email from: {email_address}")
        print(f"Date: {date}")
        print(f"Subject: {main_email_subject}")
        print(f"Snippet: {snippet}")
        print()