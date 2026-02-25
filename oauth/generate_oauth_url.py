#!/usr/bin/env python3
"""
Generate OAuth 2.0 Authorization URL for headless servers.

This script generates an authorization URL that can be copied from a VPS
to a local browser for OAuth authentication with Google APIs.

Usage:
    python3 generate_oauth_url.py

Output:
    Prints a URL to copy/paste into your local browser.

Repository: https://github.com/anyech/openclaw-gmail-reader
"""

import json
import sys
from urllib.parse import urlencode

# Configuration
CLIENT_SECRETS_FILE = 'client_secrets.json'
REDIRECT_URI = 'https://developers.google.com/oauthplayground'

# Scopes to request (customize as needed)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
]


def generate_auth_url():
    """Generate the OAuth authorization URL."""
    
    # Load client credentials
    with open(CLIENT_SECRETS_FILE, 'r') as f:
        creds = json.load(f)
    
    client_id = creds['web']['client_id']
    
    # Build authorization URL parameters
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'access_type': 'offline',  # critical: get refresh token
        'prompt': 'consent',  # critical: always get refresh token
        'scope': ' '.join(SCOPES),
    }
    
    # Generate URL
    base_url = 'https://accounts.google.com/o/oauth2/auth'
    auth_url = f"{base_url}?{urlencode(params)}"
    
    return auth_url


def main():
    print("=" * 70)
    print("OAuth 2.0 Authorization URL Generator (Headless Server)")
    print("=" * 70)
    print()
    
    try:
        auth_url = generate_auth_url()
        
        print("✅ Authorization URL generated successfully!")
        print()
        print("📋 INSTRUCTIONS:")
        print("1. Copy the URL below")
        print("2. Paste it into your LOCAL browser (on your laptop)")
        print("3. Click 'Allow' on Google's consent screen")
        print("4. You'll be redirected to OAuth Playground")
        print("5. Copy the authorization code from OAuth Playground")
        print("6. Run: python3 exchange_code.py <YOUR_CODE>")
        print()
        print("🔗 AUTHORIZATION URL:")
        print("-" * 70)
        print(auth_url)
        print("-" * 70)
        print()
        
    except FileNotFoundError:
        print(f"❌ Error: {CLIENT_SECRETS_FILE} not found!")
        print()
        print("Download this file from Google Cloud Console:")
        print("1. Go to APIs & Services → Credentials")
        print("2. Click download icon next to your OAuth 2.0 Client ID")
        print(f"3. Save as {CLIENT_SECRETS_FILE} in this directory")
        sys.exit(1)
    
    except KeyError as e:
        print(f"❌ Error: Invalid credentials file format - missing {e}")
        print()
        print("Make sure you downloaded a 'Web application' credentials file.")
        sys.exit(1)


if __name__ == '__main__':
    main()
