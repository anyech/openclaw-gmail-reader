# OAuth 2.0 Scripts for Headless Servers

These scripts automate OAuth 2.0 authentication for Google APIs on headless servers (VPS) without a browser.

## 📋 Overview

When running applications on a VPS without a browser, the standard OAuth flow fails because it requires opening a browser for Google's consent screen. These scripts use Google's OAuth Playground as a redirect target, allowing you to complete authentication on your local browser while the tokens are stored on the VPS.

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud Project** with APIs enabled
2. **OAuth 2.0 Client ID** (Web application type)
3. **Python 3.8+** installed on your VPS

### Installation

```bash
# Clone the repository
git clone https://github.com/anyech/openclaw-gmail-reader.git
cd openclaw-gmail-reader/oauth

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 1: Configure OAuth Playground Redirect URI

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services → Credentials**
3. Click on your OAuth 2.0 Client ID
4. Under **Authorized redirect URIs**, add:
   ```
   https://developers.google.com/oauthplayground
   ```
5. Click **Save**

### Step 2: Place Client Credentials

Download your OAuth credentials from Google Cloud Console and save as `client_secrets.json` in this directory.

### Step 3: Generate Authorization URL

```bash
python3 generate_oauth_url.py
```

**Output:**
```
======================================================================
OAuth 2.0 Authorization URL Generator (Headless Server)
======================================================================

✅ Authorization URL generated successfully!

📋 INSTRUCTIONS:
1. Copy the URL below
2. Paste it into your LOCAL browser (on your laptop)
3. Click 'Allow' on Google's consent screen
4. You'll be redirected to OAuth Playground
5. Copy the authorization code from OAuth Playground
6. Run: python3 exchange_code.py <YOUR_CODE>

🔗 AUTHORIZATION URL:
----------------------------------------------------------------------
https://accounts.google.com/o/oauth2/auth?client_id=...
----------------------------------------------------------------------
```

### Step 4: Authorize in Local Browser

1. **Copy the URL** from the VPS terminal
2. **Paste into your local browser** (Chrome, Firefox, Safari on your laptop)
3. **Click "Allow"** on Google's consent screen
4. **You'll be redirected** to OAuth Playground

### Step 5: Copy Authorization Code

On the OAuth Playground page, copy the authorization code (the long string after `code=`).

### Step 6: Exchange Code for Tokens

```bash
python3 exchange_code.py 4/0AY0e-g7ZxKqL9vN8mP3rT6sU2wV5xY8zA1bC4dE7fG
```

**Output:**
```
======================================================================
OAuth 2.0 Code Exchange (Headless Server)
======================================================================

🔄 Exchanging authorization code for tokens...
✅ Token exchange successful!

📦 Token details:
   Access token: 23kiD8sF9dK...
   Refresh token: 1//0dZxKqL9vN8...
   Expires in: 3599 seconds
   Scopes: 5 permissions granted

💾 Tokens saved to: token.json
   (permissions: 600 - owner read/write only)

🎉 SUCCESS! Your AI agent can now use Google APIs.
```

## 📁 Files

| File | Purpose |
|------|---------|
| `generate_oauth_url.py` | Generates OAuth authorization URL |
| `exchange_code.py` | Exchanges authorization code for tokens |
| `client_secrets.json` | Your OAuth credentials (download from Google) |
| `token.json` | Generated access/refresh tokens (auto-created) |
| `requirements.txt` | Python dependencies |

## 🔒 Security Best Practices

### File Permissions

The scripts automatically set secure permissions on `token.json`:
```bash
-rw-------  1 user user  1.2K Feb 25 23:48 token.json
```

### Never Commit Sensitive Files

Add these to your `.gitignore`:
```
client_secrets.json
token.json
*.pyc
__pycache__/
venv/
```

### Rotate Credentials

- **Access tokens:** Auto-refresh every hour (handled by your application)
- **Refresh tokens:** Last 6 months for published apps
- **Client secrets:** Rotate every 6-12 months

## 🛠️ Troubleshooting

### "client_secrets.json not found"

Download credentials from Google Cloud Console:
1. Go to **APIs & Services → Credentials**
2. Click download icon next to your OAuth 2.0 Client ID
3. Save as `client_secrets.json` in this directory

### "redirect_uri_mismatch"

Add `https://developers.google.com/oauthplayground` to Authorized redirect URIs in Google Cloud Console.

### "Authorization code expired"

Codes are valid for 10 minutes and single-use. Generate a new URL and re-authorize.

### "App not verified" warning

This is normal for personal projects. Click **Advanced → Go to (unsafe)** to proceed.

## 📚 Related Resources

- [Blog Post: VPS OAuth Survival Guide](https://anyech.github.io/jingxiao-cai-blog/vps-oauth-survival-guide.html)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)

## 📝 License

MIT License - See LICENSE file for details.

---

**Author:** Jingxiao Cai  
**Repository:** https://github.com/anyech/openclaw-gmail-reader  
**Blog:** https://anyech.github.io/jingxiao-cai-blog/
