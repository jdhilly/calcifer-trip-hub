#!/usr/bin/env python3
"""Trip Hub CLI — accessed by the SvelteKit frontend via execSync"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from db import get_db, init_schema
import argparse


def cmd_trips(args):
    conn = get_db()
    init_schema(conn)
    rows = conn.execute("SELECT * FROM trips ORDER BY start_date DESC").fetchall()
    return [dict(r) for r in rows]


def cmd_trip_detail(args):
    conn = get_db()
    row = conn.execute("SELECT * FROM trips WHERE id = ?", (args.trip_id,)).fetchone()
    if not row:
        return None
    trip = dict(row)
    trip['items'] = [dict(r) for r in conn.execute(
        "SELECT * FROM lists WHERE trip_id = ? ORDER BY sort_order", (args.trip_id,)
    ).fetchall()]
    trip['artifacts'] = [dict(r) for r in conn.execute(
        "SELECT * FROM trip_artifacts WHERE trip_id = ? ORDER BY created_at DESC", (args.trip_id,)
    ).fetchall()]
    return trip


def cmd_catalog(args):
    conn = get_db()
    rows = conn.execute("SELECT * FROM catalog ORDER BY category, sort_order").fetchall()
    return [dict(r) for r in rows]


def cmd_catalog_update(args):
    conn = get_db()
    item = conn.execute("SELECT * FROM catalog WHERE id = ?", (args.item_id,)).fetchone()
    if not item:
        return {"ok": False, "error": "Catalog item not found"}
    updates = []
    params = []
    if args.name is not None:
        updates.append("name = ?")
        params.append(args.name)
    if args.category is not None:
        updates.append("category = ?")
        params.append(args.category)
    if args.default_quantity is not None:
        updates.append("default_quantity = ?")
        params.append(args.default_quantity)
    if not updates:
        return {"ok": True, "message": "No changes"}
    updates.append("updated_at = datetime('now')")
    params.append(args.item_id)
    conn.execute(f"UPDATE catalog SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    return {"ok": True}


def cmd_catalog_remove(args):
    conn = get_db()
    conn.execute("DELETE FROM catalog WHERE id = ?", (args.item_id,))
    conn.commit()
    return {"ok": True}


def cmd_artifacts(args):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM trip_artifacts WHERE trip_id = ? ORDER BY created_at DESC",
        (args.trip_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def cmd_list_toggle(args):
    """Set a checklist item's checked count"""
    conn = get_db()
    item = conn.execute("SELECT * FROM lists WHERE id = ?", (args.item_id,)).fetchone()
    if not item:
        return {"ok": False, "error": "Item not found"}
    checked = min(args.checked, item['quantity'])
    conn.execute("UPDATE lists SET checked = ?, updated_at = datetime('now') WHERE id = ?",
                 (checked, args.item_id))
    conn.commit()
    return {"ok": True, "checked": checked}


def cmd_list_update(args):
    """Update a checklist item's quantity (and cap checked if needed)"""
    conn = get_db()
    item = conn.execute("SELECT * FROM lists WHERE id = ?", (args.item_id,)).fetchone()
    if not item:
        return {"ok": False, "error": "Item not found"}
    new_qty = args.quantity
    new_checked = min(item['checked'], new_qty)
    conn.execute(
        "UPDATE lists SET quantity = ?, checked = ?, updated_at = datetime('now') WHERE id = ?",
        (new_qty, new_checked, args.item_id)
    )
    conn.commit()
    return {"ok": True, "quantity": new_qty, "checked": new_checked}


def cmd_list_add(args):
    """Add an item to a trip checklist"""
    conn = get_db()
    conn.execute(
        "INSERT INTO lists (trip_id, category, label, quantity, sort_order) VALUES (?, ?, ?, ?, "
        "(SELECT COALESCE(MAX(sort_order), 0) + 1 FROM lists WHERE trip_id = ?))",
        (args.trip_id, args.category, args.label, args.quantity, args.trip_id)
    )
    conn.commit()
    return {"ok": True}


def cmd_list_remove(args):
    """Remove an item from a trip checklist"""
    conn = get_db()
    conn.execute("DELETE FROM lists WHERE id = ?", (args.item_id,))
    conn.commit()
    return {"ok": True}


def cmd_list_import(args):
    """Import multiple catalog items into a trip checklist (items as base64 JSON)"""
    import base64
    raw = base64.b64decode(args.items_b64).decode('utf-8')
    items = json.loads(raw)
    conn = get_db()
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), 0) FROM lists WHERE trip_id = ?",
        (args.trip_id,)
    ).fetchone()[0]
    for item in items:
        max_order += 1
        conn.execute(
            "INSERT INTO lists (trip_id, category, label, quantity, sort_order) VALUES (?, ?, ?, ?, ?)",
            (args.trip_id, item.get('category', ''), item['label'],
             item.get('quantity', 1), max_order)
        )
    conn.commit()
    return {"ok": True, "imported": len(items)}


def cmd_journal_entries(args):
    """Get journal entries for a trip"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM trip_journal WHERE trip_id = ? ORDER BY date DESC, created_at DESC",
        (args.trip_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def cmd_journal_add(args):
    """Add a journal entry"""
    conn = get_db()
    conn.execute(
        "INSERT INTO trip_journal (trip_id, date, content, author) VALUES (?, ?, ?, ?)",
        (args.trip_id, args.date, args.content, args.author)
    )
    conn.commit()
    return {"ok": True}


def cmd_journal_delete(args):
    """Delete a journal entry"""
    conn = get_db()
    conn.execute("DELETE FROM trip_journal WHERE id = ?", (args.entry_id,))
    conn.commit()
    return {"ok": True}


def cmd_participants_update(args):
    """Update participants JSON for a trip"""
    conn = get_db()
    conn.execute("UPDATE trips SET participants = ?, updated_at = datetime('now') WHERE id = ?",
                 (args.json_data, args.trip_id))
    conn.commit()
    return {"ok": True}


def cmd_connectivity(args):
    """Check if cloud services are reachable"""
    import urllib.request
    try:
        urllib.request.urlopen('https://www.google.com', timeout=3)
        return {"online": True}
    except Exception:
        return {"online": False}


def cmd_notebooklm_generate(args):
    """Generate a NotebookLM artifact for a trip"""
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', 'notebooklm_generate.py')
    if not os.path.exists(script):
        return {"ok": False, "error": "notebooklm_generate.py not found"}
    import subprocess
    try:
        result = subprocess.run(
            ['python3', script, args.trip_key, args.artifact_type, '--verbose'],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode == 0:
            # Extract the file path from output
            lines = result.stdout.strip().split('\n')
            file_path = None
            for line in lines:
                if line.startswith('🎉 Done!'):
                    file_path = line.split(' at ')[-1] if ' at ' in line else None
            return {"ok": True, "output": result.stdout, "file_path": file_path}
        else:
            return {"ok": False, "error": result.stderr[:500], "output": result.stdout[:500]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Generation timed out after 10 minutes"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', help='Path to DB (unused, uses default)')
    sub = parser.add_subparsers()

    p = sub.add_parser('trips')
    p.set_defaults(func=cmd_trips)

    p = sub.add_parser('trip')
    p.add_argument('trip_id')
    p.set_defaults(func=cmd_trip_detail)

    p = sub.add_parser('catalog')
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser('catalog-update')
    p.add_argument('item_id', type=int)
    p.add_argument('--name', default=None)
    p.add_argument('--category', default=None)
    p.add_argument('--default-quantity', type=int, default=None)
    p.set_defaults(func=cmd_catalog_update)

    p = sub.add_parser('catalog-remove')
    p.add_argument('item_id', type=int)
    p.set_defaults(func=cmd_catalog_remove)

    p = sub.add_parser('artifacts')
    p.add_argument('trip_id')
    p.set_defaults(func=cmd_artifacts)

    p = sub.add_parser('list-toggle')
    p.add_argument('item_id', type=int)
    p.add_argument('--checked', type=int, default=0)
    p.set_defaults(func=cmd_list_toggle)

    p = sub.add_parser('list-update')
    p.add_argument('item_id', type=int)
    p.add_argument('--quantity', type=int, required=True)
    p.set_defaults(func=cmd_list_update)

    p = sub.add_parser('list-add')
    p.add_argument('trip_id')
    p.add_argument('--label', required=True)
    p.add_argument('--category', default='')
    p.add_argument('--quantity', type=int, default=1)
    p.set_defaults(func=cmd_list_add)

    p = sub.add_parser('list-remove')
    p.add_argument('item_id', type=int)
    p.set_defaults(func=cmd_list_remove)

    p = sub.add_parser('list-import')
    p.add_argument('trip_id')
    p.add_argument('items_b64')
    p.set_defaults(func=cmd_list_import)

    p = sub.add_parser('journal')
    p.add_argument('trip_id')
    p.set_defaults(func=cmd_journal_entries)

    p = sub.add_parser('journal-add')
    p.add_argument('trip_id')
    p.add_argument('--date', required=True)
    p.add_argument('--content', required=True)
    p.add_argument('--author', default='')
    p.set_defaults(func=cmd_journal_add)

    p = sub.add_parser('journal-delete')
    p.add_argument('entry_id', type=int)
    p.set_defaults(func=cmd_journal_delete)

    p = sub.add_parser('participants-update')
    p.add_argument('trip_id')
    p.add_argument('json_data')
    p.set_defaults(func=cmd_participants_update)

    p = sub.add_parser('connectivity')
    p.set_defaults(func=cmd_connectivity)

    p = sub.add_parser('notebooklm-generate')
    p.add_argument('trip_key')
    p.add_argument('artifact_type')
    p.set_defaults(func=cmd_notebooklm_generate)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        result = args.func(args)
        print(json.dumps(result, default=str))
    else:
        parser.print_help()
