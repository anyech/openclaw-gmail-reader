#!/usr/bin/env python3
"""
Setup script to help configure OAuth credentials.
Run this to generate initial token.json
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def main():
    print("=== OpenClaw Gmail Reader Setup ===\n")
    
    creds_file = Path(__file__).parent / 'credentials' / 'client_secrets.json'
    
    if not creds_file.exists():
        print("ERROR: credentials/client_secrets.json not found!")
        print("\n1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Web application)")
        print("3. Download as client_secrets.json")
        print("4. Place in credentials/ directory")
        return
    
    print("Starting OAuth flow...")
    print("A browser window will open for authentication.")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        str(creds_file),
        SCOPES
    )
    
    creds = flow.run_local_server(port=0)
    
    # Save token
    token_file = Path(__file__).parent / 'credentials' / 'token.json'
    token_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(token_file, 'w') as f:
        f.write(creds.to_json())
    
    print(f"\n✅ Success! Token saved to {token_file}")
    print("\nYou can now use gmail_reader.py")

if __name__ == '__main__':
    main()