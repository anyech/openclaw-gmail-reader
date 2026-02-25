#!/usr/bin/env python3
"""
Google Calendar Event Fetcher
Fetches upcoming calendar events.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = Path(__file__).parent / 'credentials' / 'token.json'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    """Build the Calendar service."""
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    return build('calendar', 'v3', credentials=creds)

def fetch_events(days_ahead=7, max_results=20):
    """Fetch upcoming events from primary calendar."""
    service = get_calendar_service()
    
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def format_events_json(events):
    """Format events as JSON for easy parsing."""
    if not events:
        return json.dumps({"events": []}, indent=2)
    
    output = []
    for event in events:
        start = event.get('start', {})
        end = event.get('end', {})
        
        # Get start time
        if 'dateTime' in start:
            start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            start_str = start_time.strftime('%b %d, %H:%M')
        else:
            start_str = event.get('start', {}).get('date', 'All Day')
        
        output.append({
            'start': start_str,
            'title': event.get('summary', 'Untitled Event'),
            'link': event.get('htmlLink', '')
        })
    
    return json.dumps({"events": output}, indent=2)

if __name__ == '__main__':
    print("Fetching upcoming calendar events...")
    events = fetch_events()
    print(format_events_json(events))
