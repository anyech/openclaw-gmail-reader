# OpenClaw Gmail Reader

Python-based Gmail API integration for OpenClaw. Supports Gmail, Calendar, Drive, and Sheets APIs.

## Setup

1. Create OAuth credentials in Google Cloud Console
2. Download as `credentials/client_secrets.json`
3. Run OAuth flow to generate `credentials/token.json`

## Available Scripts

| Script | Purpose |
|--------|---------|
| `gmail_reader.py` | Fetch emails from last 24h, format for AI analysis |
| `calendar_events.py` | Fetch upcoming calendar events |
| `drive_indexer.py` | Index Drive files for change detection |
| `manual_oauth.py` | Complete OAuth flow for VPS/headless environments |
| `generate_oauth_url.py` | Generate OAuth authorization URL |
| `exchange_code.py` | Exchange authorization code for token |
| `setup.py` | Browser-based OAuth setup (local machine only) |

## APIs Enabled

| API | Scope |
|-----|-------|
| Gmail | Read + Send |
| Google Calendar | Read-only |
| Google Drive | Read-only |
| Google Sheets | Read-only |

## OAuth Token Setup (VPS/Headless)

For VPS environments without a browser, use the manual OAuth flow with OAuth Playground:

### Quick Setup

```bash
cd ~/.openclaw/workspace/gmail-reader

# Step 1: Generate authorization URL
python3 manual_oauth.py

# Step 2: Visit URL in browser, authorize, get redirected to OAuth Playground

# Step 3: Copy the 'code' parameter from URL and exchange for token
python3 manual_oauth.py "YOUR_CODE_HERE"
```

### Alternative: Step-by-Step

```bash
# Generate URL
python3 generate_oauth_url.py

# Exchange code after authorization
python3 exchange_code.py "YOUR_CODE_HERE"
```

## Usage

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Fetch emails
python gmail_reader.py

# Fetch calendar events
python calendar_events.py

# Index Drive files
python drive_indexer.py
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

- **Access tokens** expire in ~1 hour, auto-refreshed by scripts
- **Refresh tokens** last 6 months of inactivity (if app is published to production)
- If refresh token expires, repeat the OAuth flow

## Security

- `credentials/` directory is `.gitignore`'d
- OAuth tokens not committed
- Client secrets configured for OAuth Playground redirect URI

## Requirements

```bash
pip install -r requirements.txt
```

See `requirements.txt` for dependencies:
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`