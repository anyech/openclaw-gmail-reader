#!/usr/bin/env python3
"""
Google Drive File Tree Indexer
Fetches and indexes Drive files for change detection.
"""

import json
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = Path(__file__).parent / 'credentials' / 'token.json'
INDEX_FILE = Path(__file__).parent.parent / 'memory' / 'drive_index.json'

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    return build('drive', 'v3', credentials=creds)

def fetch_all_files(drive, page_size=100):
    """Recursively fetch all files with their paths."""
    files = {}
    
    # First get all folders
    folders = {}
    results = drive.files().list(
        q="mimeType='application/vnd.google-apps.folder'",
        pageSize=1000,
        fields='files(id, name, parents)'
    ).execute()
    
    for f in results.get('files', []):
        folders[f['id']] = {'name': f['name'], 'parents': f.get('parents', [])}
    
    # Now get all files
    results = drive.files().list(
        pageSize=1000,
        fields='files(id, name, mimeType, parents, modifiedTime)'
    ).execute()
    
    for f in results.get('files', []):
        # Build path
        path_parts = []
        parent_ids = f.get('parents', [])
        
        while parent_ids:
            pid = parent_ids[0]
            if pid in folders:
                path_parts.insert(0, folders[pid]['name'])
                parent_ids = folders[pid].get('parents', [])
            else:
                break
        
        if f['name'] == 'root':
            continue
            
        path = '/'.join(path_parts + [f['name']]) if path_parts else f['name']
        
        files[f['id']] = {
            'name': f['name'],
            'path': path,
            'mimeType': f['mimeType'],
            'modifiedTime': f.get('modifiedTime', '')[:10]
        }
    
    return files

def load_previous_index():
    """Load previous index if exists."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return json.load(f)
    return {}

def save_index(files):
    """Save current index."""
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, 'w') as f:
        json.dump({
            'updated': datetime.now().isoformat(),
            'files': files
        }, f, indent=2)

def detect_changes(current_files):
    """Detect new, modified, or deleted files."""
    previous = load_previous_index()
    prev_files = previous.get('files', {})
    
    new_files = []
    modified = []
    
    # Check for new/modified
    for fid, fdata in current_files.items():
        if fid not in prev_files:
            new_files.append(fdata)
        elif fdata['modifiedTime'] > prev_files[fid].get('modifiedTime', ''):
            modified.append(fdata)
    
    # Check for deleted (optional)
    deleted = [f for fid, f in prev_files.items() if fid not in current_files]
    
    return new_files, modified, deleted

def main():
    print("Indexing Google Drive...")
    drive = get_drive_service()
    files = fetch_all_files(drive)
    new_files, modified, deleted = detect_changes(files)
    
    print(f"Total files: {len(files)}")
    print(f"New files: {len(new_files)}")
    print(f"Modified: {len(modified)}")
    
    # Save index
    save_index(files)
    
    if new_files:
        print("\n=== New Files ===")
        for f in new_files[:20]:
            print(f"  {f['path']}")
    
    return new_files, modified

if __name__ == '__main__':
    main()
