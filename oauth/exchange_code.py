#!/usr/bin/env python3
"""
Exchange OAuth 2.0 authorization code for access/refresh tokens.

This script exchanges an authorization code (obtained from OAuth Playground)
for access and refresh tokens that can be used to access Google APIs.

Usage:
    python3 exchange_code.py <AUTHORIZATION_CODE>

Example:
    python3 exchange_code.py 4/0AY0e-g7ZxKqL9vN8mP3rT6sU2wV5xY8zA1bC4dE7fG

Repository: https://github.com/anyech/openclaw-gmail-reader
"""

import json
import sys
import os
import requests
from datetime import datetime

# Configuration
CLIENT_SECRETS_FILE = 'client_secrets.json'
TOKEN_FILE = 'token.json'
REDIRECT_URI = 'https://developers.google.com/oauthplayground'


def exchange_code_for_token(auth_code):
    """Exchange authorization code for access and refresh tokens."""
    
    # Load client credentials
    with open(CLIENT_SECRETS_FILE, 'r') as f:
        creds = json.load(f)
    
    client_id = creds['web']['client_id']
    client_secret = creds['web']['client_secret']
    
    # Token exchange endpoint
    token_uri = 'https://oauth2.googleapis.com/token'
    
    # Prepare request
    data = {
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    
    # Make POST request
    response = requests.post(token_uri, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    
    # Add metadata
    token_data['token_uri'] = token_uri
    token_data['client_id'] = client_id
    token_data['client_secret'] = client_secret
    token_data['scopes'] = token_data.get('scope', '').split(' ')
    token_data['expiry'] = datetime.utcnow().timestamp() + token_data.get('expires_in', 3600)
    token_data['generated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    return token_data


def save_token(token_data, filename=TOKEN_FILE):
    """Save token to JSON file with secure permissions."""
    with open(filename, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    # Set secure permissions (owner read/write only)
    os.chmod(filename, 0o600)


def main():
    print("=" * 70)
    print("OAuth 2.0 Code Exchange (Headless Server)")
    print("=" * 70)
    print()
    
    if len(sys.argv) != 2:
        print("❌ Usage: python3 exchange_code.py <AUTHORIZATION_CODE>")
        print()
        print("Example:")
        print("  python3 exchange_code.py 4/0AY0e-g7ZxKqL9vN8mP3rT6sU2wV5xY8zA1bC4dE7fG")
        print()
        print("Get the authorization code from OAuth Playground after authorizing.")
        sys.exit(1)
    
    auth_code = sys.argv[1]
    
    try:
        print("🔄 Exchanging authorization code for tokens...")
        token_data = exchange_code_for_token(auth_code)
        
        print("✅ Token exchange successful!")
        print()
        print("📦 Token details:")
        print(f"   Access token: {token_data['access_token'][:20]}...")
        print(f"   Refresh token: {token_data['refresh_token'][:20]}...")
        print(f"   Expires in: {token_data['expires_in']} seconds")
        print(f"   Scopes: {len(token_data['scopes'])} permissions granted")
        print()
        
        # Save token
        save_token(token_data)
        print(f"💾 Tokens saved to: {TOKEN_FILE}")
        print(f"   (permissions: 600 - owner read/write only)")
        print()
        
        print("🎉 SUCCESS! Your AI agent can now use Google APIs.")
        print()
        print("📋 NEXT STEPS:")
        print("1. Move token.json to your agent's credentials directory")
        print("2. Configure your agent to use this token file")
        print("3. Test API access (e.g., read emails, check calendar)")
        print()
        print("⚠️  IMPORTANT:")
        print("- Never commit token.json to git (add to .gitignore)")
        print("- Refresh tokens last 6 months for published apps")
        print("- Access tokens expire in 1 hour (auto-refresh with refresh token)")
        print()
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print()
        print("Common causes:")
        print("- Authorization code expired (codes valid for 10 minutes)")
        print("- Code already used (codes are single-use)")
        print("- Client ID/secret mismatch")
        print()
        print("Solution: Generate a new authorization code and try again.")
        sys.exit(1)
    
    except FileNotFoundError:
        print(f"❌ Error: {CLIENT_SECRETS_FILE} not found!")
        print()
        print("Run python3 generate_oauth_url.py first to verify credentials.")
        sys.exit(1)
    
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid credentials file format")
        print()
        print("Make sure client_secrets.json is valid JSON.")
        sys.exit(1)


if __name__ == '__main__':
    main()
