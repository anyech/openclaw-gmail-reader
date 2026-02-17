# OpenClaw Gmail Reader

A Python library for reading and sending emails via Gmail API, designed for OpenClaw integration.

## Features

- **Read emails** from Gmail with priority categorization
- **Send emails** with full Gmail API support
- **OAuth 2.0** authentication (secure, no password storage)
- **Cron-friendly** — run on schedule for daily summaries

## Installation

```bash
git clone https://github.com/anyech/openclaw-gmail-reader.git
cd openclaw-gmail-reader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable **Gmail API**
4. Create OAuth credentials:
   - Application type: **Web application**
   - Add redirect URIs:
     - `http://localhost`
     - `https://developers.google.com/oauthplayground`
5. Download credentials as `credentials/client_secrets.json`

## Initial OAuth Setup

Run the setup script to authorize:

```bash
python setup.py
```

Or use OAuth Playground:
1. Go to [OAuth Playground](https://developers.google.com/oauthplayground)
2. Use your Client ID/Secret
3. Scope: `https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send`
4. Exchange for tokens
5. Save as `credentials/token.json`

## Usage

### Read Emails

```python
from gmail_reader import GmailReader

reader = GmailReader()
emails = reader.fetch_emails(max_results=50)

for email in emails:
    print(f"{email['sender']}: {email['subject']}")
```

### Send Email

```python
from gmail_reader import GmailReader

reader = GmailReader()
reader.send_email(
    to="recipient@example.com",
    subject="Test",
    body="Hello from Gmail Reader!"
)
```

### Use with OpenClaw Cron

Add to your cron job:

```bash
cd /path/to/openclaw-gmail-reader && \
source venv/bin/activate && \
python gmail_reader.py
```

## Configuration

| File | Description |
|------|-------------|
| `credentials/client_secrets.json` | OAuth client credentials |
| `credentials/token.json` | Access/refresh tokens |

Both are in `.gitignore` — never commit to version control.

## Scope Options

| Scope | Permission |
|-------|------------|
| `gmail.readonly` | Read only |
| `gmail.send` | Send only |
| Both | Read + Send |

## File Structure

```
openclaw-gmail-reader/
├── gmail_reader.py     # Main library
├── requirements.txt    # Dependencies
├── setup.py           # OAuth setup helper
├── credentials/       # OAuth files (not committed)
│   ├── client_secrets.json
│   └── token.json
└── .gitignore
```

## License

MIT

## Author

OpenClaw Community