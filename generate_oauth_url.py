#!/usr/bin/env python3
"""
Generate OAuth authorization URL for Gmail API (VPS/headless environments).

Usage:
    python3 generate_oauth_url.py

Then:
    1. Visit the URL in your browser
    2. Authorize the scopes
    3. Copy the 'code' parameter from the redirect URL
    4. Run: python3 exchange_code.py <code>
"""

import json
from pathlib import Path

# Load client credentials
CREDS_FILE = Path(__file__).parent / 'credentials' / 'client_secrets.json'

with open(CREDS_FILE) as f:
    creds = json.load(f)['web']

client_id = creds['client_id']
redirect_uri = 'https://developers.google.com/oauthplayground'

scopes = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

scope_str = '+'.join(scopes)

url = (
    f'https://accounts.google.com/o/oauth2/v2/auth?'
    f'client_id={client_id}&'
    f'redirect_uri={redirect_uri}&'
    f'response_type=code&'
    f'scope={scope_str}&'
    f'access_type=offline&'
    f'prompt=consent'
)

print("=" * 80)
print("OAUTH AUTHORIZATION URL")
print("=" * 80)
print()
print("Visit this URL in your browser:")
print()
print(url)
print()
print("=" * 80)
print("After authorizing, you'll be redirected to OAuth Playground.")
print("Copy the 'code' parameter from the URL and run:")
print("    python3 exchange_code.py <code>")
print("=" * 80)