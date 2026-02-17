#!/usr/bin/env python3
"""
OpenClaw Gmail Reader
A Python library for reading and sending emails via Gmail API.
"""

import os
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
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
            
            emails.append({
                'id': msg['id'],
                'sender': sender,
                'subject': subject,
                'date': date,
                'snippet': snippet,
                'labels': email_data.get('labelIds', [])
            })
        
        return emails
    
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
        from email.mime.text import MIMEText
        
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


def main():
    """CLI entry point for quick testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenClaw Gmail Reader')
    parser.add_argument('--max', type=int, default=10, help='Max emails to fetch')
    parser.add_argument('--send', type=str, help='Send test email to address')
    args = parser.parse_args()
    
    reader = GmailReader()
    
    if args.send:
        msg_id = reader.send_email(
            to=args.send,
            subject="Test from OpenClaw Gmail Reader",
            body="This is a test email sent via the Gmail API."
        )
        print(f"Email sent! ID: {msg_id}")
    else:
        emails = reader.fetch_emails(max_results=args.max)
        print(f"=== Fetched {len(emails)} emails ===\n")
        
        for email in emails:
            priority = reader.categorize_priority(email)
            print(f"[{priority}] {email['sender'][:30]}")
            print(f"  {email['subject'][:50]}")
            print()


if __name__ == '__main__':
    main()