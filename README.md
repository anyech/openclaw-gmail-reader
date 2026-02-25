# Gmail Reader

Python-based Gmail API integration for OpenClaw.

## Setup

1. OAuth credentials in `credentials/client_secrets.json`
2. Token stored in `credentials/token.json`

## APIs Enabled

- Gmail: Read + Send
- Google Calendar: Read-only
- Google Drive: Read-only
- Google Sheets: Read-only

## OAuth Token Setup (VPS/Headless)

The `gmail_reader.py` uses `flow.run_local_server()` which requires a browser. For VPS environments, use manual OAuth flow with OAuth Playground:

### Step 1: Generate Authorization URL

```bash
cd ~/.openclaw/workspace/gmail-reader
python3 -c "
from urllib.parse import quote
client_id = 'YOUR_CLIENT_ID'  # From client_secrets.json
scopes = 'gmail.readonly gmail.send calendar.readonly drive.readonly spreadsheets.readonly'
scope_url = 'https://www.googleapis.com/auth/' + '+https://www.googleapis.com/auth/'.join(scopes.split())
redirect_uri = 'https://developers.google.com/oauthplayground'

url = f'https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope_url}&access_type=offline&prompt=consent'
print(url)
"
```

### Step 2: Authorize in Browser

1. Visit the generated URL
2. Sign in and authorize all requested scopes
3. You'll be redirected to OAuth Playground with `?code=...` in the URL

### Step 3: Exchange Code for Token

```bash
python3 << 'EOF'
import requests
import json
from pathlib import Path

# Get client credentials
creds_file = Path('credentials/client_secrets.json')
with open(creds_file) as f:
    creds = json.load(f)['web']

# Paste your authorization code here
auth_code = 'YOUR_AUTH_CODE'  # From OAuth Playground redirect URL

# Exchange code for token
response = requests.post('https://oauth2.googleapis.com/token', data={
    'code': auth_code,
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'redirect_uri': 'https://developers.google.com/oauthplayground',
    'grant_type': 'authorization_code'
})

token_data = response.json()
token_data['client_id'] = creds['client_id']
token_data['client_secret'] = creds['client_secret']

# Save token
with open('credentials/token.json', 'w') as f:
    json.dump(token_data, f)

print(f"Token saved with scopes: {token_data.get('scope', 'unknown')}")
EOF
```

## Usage

```bash
source venv/bin/activate
python gmail_reader.py
```

## Scopes

```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/calendar.readonly
https://www.googleapis.com/auth/drive.readonly
https://www.googleapis.com/auth/spreadsheets.readonly
```

## Token Refresh

- **Access tokens** expire in ~1 hour, auto-refreshed by `gmail_reader.py`
- **Refresh tokens** last 6 months of inactivity (app is published to production)
- If refresh token expires, repeat the OAuth flow above

## Security

- `credentials/` directory is `.gitignore`'d
- OAuth tokens not committed
- Client secrets configured for OAuth Playground redirect URI