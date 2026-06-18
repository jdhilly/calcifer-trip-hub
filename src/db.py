#!/usr/bin/env python3
"""Trip Hub — Database initialization and migration"""

import sqlite3
import os
import json
import hashlib
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DB_DIR, 'trip-hub.db')
OLD_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'travel-checklist', 'data', 'checklist.db')


def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn):
    conn.executescript("""
        -- Voyages
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            destination TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            type TEXT,
            participants TEXT DEFAULT '[]',
            groups TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        -- Catalogue d'articles (global)
        CREATE TABLE IF NOT EXISTS catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT '',
            default_quantity INTEGER DEFAULT 1,
            unit TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        -- Checklist items (par voyage)
        CREATE TABLE IF NOT EXISTS lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
            catalog_id INTEGER REFERENCES catalog(id),
            category TEXT DEFAULT '',
            label TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            checked INTEGER DEFAULT 0,
            checked_by TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        -- Artifacts NotebookLM
        CREATE TABLE IF NOT EXISTS trip_artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            title TEXT,
            file_path TEXT,
            notebooklm_id TEXT,
            source_hash TEXT,
            status TEXT DEFAULT 'current',
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Journal de bord (par voyage)
        CREATE TABLE IF NOT EXISTS trip_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            content TEXT,
            author TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Métadonnées (version, sync)
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', '1')")
    conn.commit()


def migrate_from_todo():
    """Migrate data from travel-checklist/checklist.db to trip-hub.db"""
    if not os.path.exists(OLD_DB_PATH):
        print("❌ Old DB not found at", OLD_DB_PATH)
        return False

    conn = get_db()
    init_schema(conn)
    old = sqlite3.connect(OLD_DB_PATH)
    old.row_factory = sqlite3.Row

    # 1. Migrate catalog
    print("📦 Migrating catalog...")
    old_cats = old.execute("SELECT * FROM catalog_items ORDER BY id").fetchall()
    for item in old_cats:
        conn.execute(
            "INSERT OR IGNORE INTO catalog (id, name, category, default_quantity, sort_order) VALUES (?, ?, ?, ?, ?)",
            (item['id'], item['label'], item['category'], item['default_quantity'], item['sort_order'])
        )
    print(f"   → {len(old_cats)} items migrated")

    # 2. Migrate lists → trips + list items
    print("📋 Migrating lists...")
    old_lists = old.execute("SELECT * FROM travel_lists ORDER BY id").fetchall()
    for tl in old_lists:
        trip_id = f"legacy-{tl['id']}"
        # Create a trip from the list
        conn.execute(
            "INSERT OR IGNORE INTO trips (id, destination, start_date, end_date) VALUES (?, ?, ?, ?)",
            (trip_id, tl['title'], tl['departure_date'], tl['return_date'])
        )
        # Migrate items
        items = old.execute("SELECT * FROM list_items WHERE list_id = ? ORDER BY id", (tl['id'],)).fetchall()
        for item in items:
            conn.execute(
                "INSERT INTO lists (trip_id, category, label, quantity, checked, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
                (trip_id, item['category'], item['label'], item['quantity'],
                 item['packed_depart'], item['sort_order'])
            )
        print(f"   → {tl['title']}: {len(items)} items")

    print(f"   → {len(old_lists)} lists migrated")

    # 3. Store migration metadata
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                 ('migrated_from_todo', datetime.now().isoformat()))
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                 ('old_db_path', OLD_DB_PATH))

    conn.commit()
    old.close()
    conn.close()
    print("✅ Migration complete!")
    return True


def compute_source_hash(file_paths):
    """Compute SHA256 of concatenated file contents"""
    hasher = hashlib.sha256()
    for path in sorted(file_paths):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                hasher.update(f.read())
    return hasher.hexdigest()


if __name__ == '__main__':
    import sys
    if '--migrate' in sys.argv:
        migrate_from_todo()
    elif '--init' in sys.argv:
        conn = get_db()
        init_schema(conn)
        conn.close()
        print(f"✅ Database initialized at {DB_PATH}")
    else:
        print("Usage: python3 db.py [--init | --migrate]")
