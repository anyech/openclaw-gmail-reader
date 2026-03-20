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

from preview_markdown import sanitize_markdown_preview

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Default scopes: Gmail + Calendar + Drive + Sheets (all-in-one)
# This ensures token.json always has all scopes when refreshed
DEFAULT_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
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
    
    def fetch_emails(self, max_results=100, query=None, all_emails=True, include_attachments=False):
        """
        Fetch emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query (optional)
            all_emails: If True, fetch all (read+unread) from last 24h
            include_attachments: If True, extract attachment metadata (adds API calls)
        
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
            # Fetch full message with attachments if requested
            if include_attachments:
                email_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='full'
                ).execute()
            else:
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
            
            # Extract attachment info if requested
            has_attachments = False
            attachment_types = []
            image_attachments = []
            
            if include_attachments and 'parts' in email_data.get('payload', {}):
                for part in email_data['payload']['parts']:
                    if part.get('filename'):
                        has_attachments = True
                        mime_type = part.get('mimeType', '')
                        attachment_types.append(mime_type)
                        
                        # Track image attachments specifically
                        if mime_type.startswith('image/'):
                            attachment_id = part.get('body', {}).get('attachmentId')
                            if attachment_id:
                                image_attachments.append({
                                    'filename': part['filename'],
                                    'mime_type': mime_type,
                                    'attachment_id': attachment_id,
                                    'size': part.get('body', {}).get('size', 0)
                                })
            
            emails.append({
                'id': msg['id'],
                'sender': sender,
                'subject': subject,
                'date': date,
                'snippet': snippet,
                'body': body,
                'labels': email_data.get('labelIds', []),
                'has_attachments': has_attachments,
                'attachment_types': attachment_types,
                'image_attachments': image_attachments
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
    
    def send_email(self, to, subject, body, from_addr=None, reply_to_message_id=None):
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            from_addr: From address (optional, uses authenticated account)
            reply_to_message_id: Gmail message ID to reply to (for threading)
        
        Returns:
            Message ID on success
        """
        service = self.connect()
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        if from_addr:
            message['from'] = from_addr
        
        # Add threading headers if replying to an email
        if reply_to_message_id:
            # In-Reply-To header for email threading
            message['In-Reply-To'] = f'<{reply_to_message_id}@gmail.com>'
            # References header for email threading
            message['References'] = f'<{reply_to_message_id}@gmail.com>'
            # Standard reply subject prefix if not already present
            if not subject.lower().startswith('re:'):
                message['subject'] = f'Re: {subject}'
        
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
    
    def get_attachment(self, message_id, attachment_id):
        """
        Download an email attachment.
        
        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID from message parts
        
        Returns:
            Dictionary with filename, mime_type, and base64-encoded data
        """
        service = self.connect()
        
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_id
        ).execute()
        
        return {
            'filename': attachment.get('filename', 'unknown'),
            'mime_type': attachment.get('mimeType', 'application/octet-stream'),
            'size': attachment.get('size', 0),
            'data': attachment.get('data', '')  # Base64-encoded
        }
    
    def ocr_image_attachment(self, message_id, attachment_id, model='bailian/kimi-k2.5'):
        """
        Perform OCR on an image attachment using vision-capable model.
        
        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID
            model: Vision model to use (default: Kimi K2.5)
        
        Returns:
            OCR result text
        """
        # Get attachment data
        attachment = self.get_attachment(message_id, attachment_id)
        
        if not attachment['data']:
            return "Error: Could not retrieve attachment data"
        
        # For OCR, we'd typically use the image tool or spawn a multimodal subagent
        # This method returns the attachment info for the subagent to process
        return {
            'message_id': message_id,
            'filename': attachment['filename'],
            'mime_type': attachment['mime_type'],
            'size': attachment['size'],
            'base64_data': attachment['data'][:1000] + '...' if len(attachment['data']) > 1000 else attachment['data']
        }
    
    def _sanitize_markdown_preview(self, text):
        """Normalize preview text so generated Markdown stays lint-safe."""
        return sanitize_markdown_preview(text)

    def format_for_analysis(self, emails):
        """Format emails for OpenClaw analysis."""
        if not emails:
            return f"# Gmail Summary ({datetime.now().strftime('%Y-%m-%d %H:%M UTC')})\n\n**No emails in the last 24 hours.**"
        
        output = f"# Gmail Summary ({datetime.now().strftime('%Y-%m-%d %H:%M UTC')})\n\n"
        output += f"**Total emails (last 24h):** {len(emails)}\n\n"
        
        # Track emails with image attachments
        image_attachment_emails = []
        
        for i, email in enumerate(emails, 1):
            output += f"## Email {i}\n"
            output += f"**From:** {email['sender']}\n"
            output += f"**Subject:** {email['subject']}\n"
            output += f"**Date:** {email['date']}\n"
            
            # Check for image attachments
            if email.get('image_attachments'):
                image_attachment_emails.append({
                    'index': i,
                    'subject': email['subject'],
                    'attachments': email['image_attachments']
                })
                output += f"**📎 Attachments:** {len(email['image_attachments'])} image(s)\n"
                for att in email['image_attachments']:
                    output += f"   - `{att['filename']}` ({att['mime_type']}, {att['size']:,} bytes)\n"
                output += f"   → **Reply \"OCR Email {i}\" or \"OCR {email['subject'][:30]}\" to extract text**\n"
            elif email.get('has_attachments'):
                output += f"**📎 Attachments:** Yes ({', '.join(email['attachment_types'][:3])})\n"
            
            preview = self._sanitize_markdown_preview(email.get('body', email.get('snippet', ''))[:200])
            output += f"**Preview:** {preview}...\n\n"
        
        # Add attachment summary section if any found
        if image_attachment_emails:
            output += "---\n\n"
            output += f"## 📸 Emails with Image Attachments ({len(image_attachment_emails)})\n\n"
            output += "**To OCR an attachment, reply with:** `OCR Email <number>` or `OCR <subject>`\n\n"
            for item in image_attachment_emails:
                output += f"{item['index']}. **{item['subject']}**\n"
                for att in item['attachments']:
                    output += f"   - 📎 `{att['filename']}` ({att['size']:,} bytes)\n"
                output += f"   → Reply: `OCR Email {item['index']}`\n\n"
        
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
    parser.add_argument('--attachments', action='store_true', help='Include attachment metadata (adds API calls)')
    parser.add_argument('--ocr', type=str, metavar='MSG_ID:ATT_ID', help='OCR specific attachment (format: message_id:attachment_id)')
    args = parser.parse_args()
    
    reader = GmailReader()
    
    if args.send:
        msg_id = reader.send_email(
            to=args.send,
            subject="Test from OpenClaw Gmail Reader",
            body="This is a test email sent via the Gmail API."
        )
        print(f"Email sent! ID: {msg_id}")
    elif args.ocr:
        # OCR mode
        try:
            msg_id, att_id = args.ocr.split(':')
            print(f"Fetching attachment {att_id} from message {msg_id}...")
            result = reader.ocr_image_attachment(msg_id, att_id)
            print(f"\n{'='*60}")
            print(f"Attachment: {result['filename']}")
            print(f"Type: {result['mime_type']}")
            print(f"Size: {result['size']:,} bytes")
            print(f"\nBase64 preview: {result['base64_data'][:200]}...")
            print(f"\n{'='*60}")
            print("\n📸 To perform OCR, spawn a multimodal subagent with this data:")
            print("   sessions_spawn(mode='run', model='bailian/kimi-k2.5', task='Analyze this image...')")
        except ValueError:
            print("Error: Invalid format. Use --ocr message_id:attachment_id")
    elif args.summary:
        # OpenClaw morning memo mode
        print("Fetching all emails from last 24 hours...")
        emails = reader.fetch_emails(max_results=args.max, include_attachments=args.attachments)
        
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
        emails = reader.fetch_emails(max_results=args.max, include_attachments=args.attachments)
        print(f"=== Fetched {len(emails)} emails ===\n")
        
        # Show attachment summary
        image_emails = [e for e in emails if e.get('image_attachments')]
        if image_emails:
            print(f"📸 Emails with image attachments: {len(image_emails)}\n")
            for email in image_emails:
                print(f"[{email['subject'][:50]}]")
                for att in email['image_attachments']:
                    print(f"  - {att['filename']} ({att['mime_type']}, {att['size']:,} bytes)")
                print()
        
        for email in emails:
            priority = reader.categorize_priority(email)
            print(f"[{priority}] {email['sender'][:30]}")
            print(f"  {email['subject'][:50]}")
            if email.get('image_attachments'):
                print(f"  📎 {len(email['image_attachments'])} image(s)")
            print()


if __name__ == '__main__':
    main()