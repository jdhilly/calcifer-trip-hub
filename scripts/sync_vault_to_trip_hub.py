#!/usr/bin/env python3
"""Trip Hub — Sync vault travel content to Trip Hub DB

This script runs periodically via cron to:
1. Discover new trips in Partages/Travel/* folders
2. Sync journal entries from vault to trip_journal
3. Update catalog from vault references
4. Check for stale NotebookLM sources

Usage: python3 sync_vault_to_trip_hub.py
"""

import os
import sys
import json
import hashlib
import re
from datetime import datetime

TRIP_HUB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(TRIP_HUB_DIR, 'src'))

from db import get_db, init_schema

VAULT_DIR = os.path.expanduser('~/vault-famille')
TRAVEL_DIR = os.path.join(VAULT_DIR, 'Partages', 'Travel')

# Trip key → mapped trip ID in DB
TRIP_MAP = {
    'lauris-2026': 'legacy-1',
}


def discover_trips():
    """Find trip folders in Partages/Travel/"""
    if not os.path.exists(TRAVEL_DIR):
        print(f"⚠️  Travel dir not found: {TRAVEL_DIR}")
        return []
    
    trips = []
    for entry in os.listdir(TRAVEL_DIR):
        folder = os.path.join(TRAVEL_DIR, entry)
        if os.path.isdir(folder) and entry != '__pycache__':
            # Detect by looking for markdown sources or briefing files
            md_files = [f for f in os.listdir(folder) if f.endswith('.md')]
            if md_files or entry in TRIP_MAP:
                trips.append({
                    'key': entry.lower().replace(' ', '-'),
                    'folder': entry,
                    'path': folder,
                    'md_count': len(md_files),
                    'md_files': sorted(md_files),
                })
    return trips


def compute_source_hash(folder):
    """Compute SHA256 of all markdown files in a folder."""
    hasher = hashlib.sha256()
    md_files = sorted([f for f in os.listdir(folder) if f.endswith('.md')])
    for fname in md_files:
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            with open(fpath, 'rb') as f:
                hasher.update(f.read())
    return hasher.hexdigest(), len(md_files)


def check_stale_artifacts(conn, trip_id, source_hash):
    """Mark artifacts as stale if source_hash doesn't match."""
    rows = conn.execute(
        "SELECT id, source_hash, status FROM trip_artifacts WHERE trip_id = ? AND status != 'generating'",
        (trip_id,)
    ).fetchall()
    
    stale_count = 0
    for row in rows:
        stored_hash = row['source_hash'] or ''
        if stored_hash and stored_hash != source_hash:
            conn.execute(
                "UPDATE trip_artifacts SET status = 'stale', updated_at = datetime('now') WHERE id = ?",
                (row['id'],)
            )
            stale_count += 1
    
    return stale_count


def update_artifact_hash(conn, trip_id, source_hash):
    """Update source_hash for current artifacts that don't have one."""
    conn.execute(
        "UPDATE trip_artifacts SET source_hash = ? WHERE trip_id = ? AND source_hash IS NULL AND status = 'current'",
        (source_hash, trip_id)
    )


def main():
    print(f"🔍 Trip Hub Vault Sync — {datetime.now().isoformat()}")
    print(f"   Vault: {VAULT_DIR}")
    print()
    
    conn = get_db()
    init_schema(conn)
    
    trips = discover_trips()
    if not trips:
        print("❌ No trips found in travel directory")
        return
    
    print(f"📂 Found {len(trips)} trip folder(s):")
    for t in trips:
        print(f"   • {t['folder']} ({t['md_count']} sources)")
    
    print()
    
    for t in trips:
        trip_id = TRIP_MAP.get(t['key'], t['key'])
        print(f"  ── {t['folder']} (DB: {trip_id}) ──")
        
        # Compute source hash
        source_hash, md_count = compute_source_hash(t['path'])
        print(f"     📝 Sources: {md_count} → hash: {source_hash[:16]}...")
        
        # Check if trip exists in DB, create if not
        existing = conn.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
        if not existing:
            print(f"     🆕 Creating trip in DB: {t['folder']}")
            conn.execute(
                "INSERT INTO trips (id, destination, created_at) VALUES (?, ?, datetime('now'))",
                (trip_id, t['folder'])
            )
        
        # Check stale artifacts
        stale = check_stale_artifacts(conn, trip_id, source_hash)
        if stale > 0:
            print(f"     ⚠️  {stale} artifact(s) marked stale (sources changed)")
        
        # Update any null source hashes
        update_artifact_hash(conn, trip_id, source_hash)
        
        print()
    
    conn.commit()
    conn.close()
    print("✅ Sync complete!")


if __name__ == '__main__':
    main()
