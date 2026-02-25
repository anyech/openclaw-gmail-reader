#!/usr/bin/env python3
"""
OpenClaw Gmail Reader
A Python library for reading and sending emails via Gmail API.

Usage:
    # As a library
    from gmail_reader import GmailReader
    reader = GmailReader()
    emails = reader.fetch_emails()
    
    # CLI
    python gmail_reader.py --max 20           # Fetch last 20 emails
    python gmail_reader.py --send user@x.com  # Send test email
    python gmail_reader.py --summary          # Generate OpenClaw summary
"""

import os
import json
import base64
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Default scopes: Read + Send
DEFAULT_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

DEFAULT_CREDENTIALS_FILE = Path(__file__).parent / 'credentials' / 'client_secrets.json'
DEFAULT_TOKEN_FILE = Path(__file__).parent / 'credentials' / 'token.json'
DEFAULT_MEMORY_FILE = Path(__file__).parent / '..' / 'memory' / 'gmail-daily.md'


class GmailReader:
    """Gmail API wrapper for OpenClaw."""
    
    def __init__(self, 
                 credentials_file=None, 
                 token_file=None,
                 scopes=None):
        self.credentials_file = credentials_file or DEFAULT_CREDENTIALS_FILE
        self.token_file = token_file or DEFAULT_TOKEN_FILE
        self.scopes = scopes or DEFAULT_SCOPES
        self.service = None
    
    def get_credentials(self):
        """Get or refresh OAuth credentials."""
        creds = None
        
        # Load existing token
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_file), 
                self.scopes
            )
        
        # Refresh or create new
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), 
                    self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for future runs
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def connect(self):
        """Establish connection to Gmail API."""
        if self.service is None:
            creds = self.get_credentials()
            self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def fetch_emails(self, max_results=100, query=None, all_emails=True):
        """
        Fetch emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query (optional)
            all_emails: If True, fetch all (read+unread) from last 24h
        
        Returns:
            List of email dictionaries
        """
        service = self.connect()
        
        # Build query
        if all_emails:
            yesterday = datetime.now() - timedelta(days=1)
            q = query or f'after:{yesterday.strftime("%Y/%m/%d")}'
        else:
            q = query or 'is:unread'
        
        results = service.users().messages().list(
            userId='me',
            q=q,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            email_data = service.users().messages().get(
                userId='me', 
                id=msg['id']
            ).execute()
            
            # Extract headers
            headers = email_data.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get snippet
            snippet = email_data.get('snippet', '')
            
            # Get body (for full content)
            body = self._get_body(email_data)
            
            emails.append({
                'id': msg['id'],
                'sender': sender,
                'subject': subject,
                'date': date,
                'snippet': snippet,
                'body': body,
                'labels': email_data.get('labelIds', [])
            })
        
        return emails
    
    def _get_body(self, email_data):
        """Extract body text from email data."""
        payload = email_data.get('payload', {})
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                        break
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        
        return body[:500] + "..." if len(body) > 500 else body
    
    def categorize_priority(self, email):
        """
        Categorize email priority based on sender/subject keywords.
        
        Returns: 'HIGH', 'MEDIUM', or 'LOW'
        """
        text = (email.get('subject', '') + ' ' + email.get('sender', '')).lower()
        
        high_keywords = ['school', 'medical', 'doctor', 'insurance', 'urgent', 
                        'emergency', 'billing', 'payment due']
        medium_keywords = ['work', 'oracle', 'shipping', 'appointment', 
                          'meeting', 'calendar']
        
        for kw in high_keywords:
            if kw in text:
                return 'HIGH'
        
        for kw in medium_keywords:
            if kw in text:
                return 'MEDIUM'
        
        return 'LOW'
    
    def send_email(self, to, subject, body, from_addr=None):
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            from_addr: From address (optional, uses authenticated account)
        
        Returns:
            Message ID on success
        """
        service = self.connect()
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        if from_addr:
            message['from'] = from_addr
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        result = service.users().messages().send(
            userId='me', 
            body={'raw': raw}
        ).execute()
        
        return result.get('id')
    
    def get_profile(self):
        """Get Gmail profile info."""
        service = self.connect()
        return service.users().getProfile(userId='me').execute()
    
    def format_for_analysis(self, emails):
        """Format emails for OpenClaw analysis."""
        if not emails:
            return f"## Gmail Summary ({datetime.now().strftime('%Y-%m-%d %H:%M UTC')})\n\n**No emails in the last 24 hours.**"
        
        output = f"## Gmail Summary ({datetime.now().strftime('%Y-%m-%d %H:%M UTC')})\n\n"
        output += f"**Total emails (last 24h):** {len(emails)}\n\n"
        
        for i, email in enumerate(emails, 1):
            output += f"### Email {i}\n"
            output += f"**From:** {email['sender']}\n"
            output += f"**Subject:** {email['subject']}\n"
            output += f"**Date:** {email['date']}\n"
            preview = email.get('body', email.get('snippet', ''))[:200]
            output += f"**Preview:** {preview}...\n\n"
        
        return output
    
    def log_emails(self, emails, memory_file=None):
        """Log emails to memory file for OpenClaw."""
        memory_file = memory_file or DEFAULT_MEMORY_FILE
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(memory_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            f.write(f"\n## Gmail Check - {timestamp}\n")
            f.write(f"Emails processed: {len(emails)}\n")
            for email in emails:
                f.write(f"- [{email['date']}] {email['sender']}: {email['subject']}\n")
            f.write("\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='OpenClaw Gmail Reader')
    parser.add_argument('--max', type=int, default=100, help='Max emails to fetch')
    parser.add_argument('--send', type=str, metavar='EMAIL', help='Send test email to address')
    parser.add_argument('--summary', action='store_true', help='Generate OpenClaw summary and log')
    args = parser.parse_args()
    
    reader = GmailReader()
    
    if args.send:
        msg_id = reader.send_email(
            to=args.send,
            subject="Test from OpenClaw Gmail Reader",
            body="This is a test email sent via the Gmail API."
        )
        print(f"Email sent! ID: {msg_id}")
    elif args.summary:
        # OpenClaw morning memo mode
        print("Fetching all emails from last 24 hours...")
        emails = reader.fetch_emails(max_results=args.max)
        
        summary = reader.format_for_analysis(emails)
        reader.log_emails(emails)
        
        # Save summary for OpenClaw to read
        summary_file = Path(__file__).parent / 'latest_summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"\n{'='*60}")
        print(summary)
        print(f"{'='*60}")
        print(f"\nSummary saved to: {summary_file}")
        print(f"Activity logged to: {DEFAULT_MEMORY_FILE}")
    else:
        # Default: fetch and display
        emails = reader.fetch_emails(max_results=args.max)
        print(f"=== Fetched {len(emails)} emails ===\n")
        
        for email in emails:
            priority = reader.categorize_priority(email)
            print(f"[{priority}] {email['sender'][:30]}")
            print(f"  {email['subject'][:50]}")
            print()


if __name__ == '__main__':
    main()