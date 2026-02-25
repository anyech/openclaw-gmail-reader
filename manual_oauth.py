#!/usr/bin/env python3
"""
Manual OAuth flow for Gmail API on VPS (no browser).
Uses OAuth Playground as redirect URI.

Usage:
  python3 manual_oauth.py                    # Generate auth URL
  python3 manual_oauth.py "CODE_OR_URL"      # Exchange code for token
"""

import sys
import json
from pathlib import Path
from google_auth_oauthlib.flow import Flow

# All 5 scopes for Google Workspace integration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
]

CREDENTIALS_FILE = Path(__file__).parent / 'credentials' / 'client_secrets.json'
TOKEN_FILE = Path(__file__).parent / 'credentials' / 'token.json'

def main():
    # Load client secrets
    with open(CREDENTIALS_FILE, 'r') as f:
        client_secrets = json.load(f)
    
    # Use OAuth Playground as redirect URI (configured in Google Cloud Console)
    redirect_uri = 'https://developers.google.com/oauthplayground'
    
    # Create flow
    flow = Flow.from_client_config(
        client_secrets,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Check if code was provided as argument
    if len(sys.argv) < 2:
        print("=" * 70)
        print("MANUAL OAUTH FLOW FOR GMAIL API - Step 1")
        print("=" * 70)
        print()
        print("Open this URL in your browser:")
        print()
        print(auth_url)
        print()
        print("After authorizing, you'll be redirected to OAuth Playground.")
        print("Copy the 'code' parameter from the URL and run:")
        print()
        print(f'  python3 manual_oauth.py "YOUR_CODE_HERE"')
        print()
        print("Or paste the full redirect URL:")
        print()
        print(f'  python3 manual_oauth.py "https://developers.google.com/oauthplayground/?code=..."')
        sys.exit(0)
    
    # Get code from argument
    redirect_response = sys.argv[1]
    
    # Extract code if full URL was provided
    if redirect_response.startswith('http'):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(redirect_response)
        params = parse_qs(parsed.query)
        if 'code' in params:
            code = params['code'][0]
        else:
            print("ERROR: No 'code' parameter found in URL")
            sys.exit(1)
    else:
        code = redirect_response
    
    print("Exchanging authorization code for tokens...")
    
    # Exchange code for tokens
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save token
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print()
        print("=" * 70)
        print("SUCCESS! Token saved to:", TOKEN_FILE)
        print("=" * 70)
        print()
        print("Scopes granted:")
        for scope in credentials.scopes:
            print(f"  - {scope}")
        print()
        print("You can now use the Gmail API!")
        
    except Exception as e:
        print(f"ERROR: Failed to exchange code: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()