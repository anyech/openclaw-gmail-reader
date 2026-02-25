#!/usr/bin/env python3
"""
Exchange OAuth authorization code for token (VPS/headless environments).

Usage:
    python3 exchange_code.py <authorization_code>

After running this script, the token will be saved to credentials/token.json
"""

import sys
import json
import requests
from pathlib import Path

CREDS_FILE = Path(__file__).parent / 'credentials' / 'client_secrets.json'
TOKEN_FILE = Path(__file__).parent / 'credentials' / 'token.json'

if len(sys.argv) < 2:
    print("Usage: python3 exchange_code.py <authorization_code>")
    print()
    print("Get the authorization code from the OAuth Playground redirect URL.")
    print("Example: https://developers.google.com/oauthplayground/?code=4/0A...&scope=...")
    sys.exit(1)

auth_code = sys.argv[1]

# Load client credentials
with open(CREDS_FILE) as f:
    creds = json.load(f)['web']

# Exchange code for token
response = requests.post('https://oauth2.googleapis.com/token', data={
    'code': auth_code,
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'redirect_uri': 'https://developers.google.com/oauthplayground',
    'grant_type': 'authorization_code'
})

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    sys.exit(1)

token_data = response.json()

# Add client credentials to token (required for refresh)
token_data['client_id'] = creds['client_id']
token_data['client_secret'] = creds['client_secret']

# Save token
TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(TOKEN_FILE, 'w') as f:
    json.dump(token_data, f, indent=2)

print("=" * 80)
print("TOKEN SAVED SUCCESSFULLY")
print("=" * 80)
print()
print(f"Token file: {TOKEN_FILE}")
print(f"Scopes granted: {token_data.get('scope', 'unknown')}")
print(f"Token type: {token_data.get('token_type', 'unknown')}")
print(f"Expires in: {token_data.get('expires_in', 'unknown')} seconds (~1 hour)")
print()
print("The access token will auto-refresh when needed.")
print("Refresh token lasts 6 months of inactivity (app is published to production).")
print("=" * 80)