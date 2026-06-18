#!/usr/bin/env python3
"""Trip Hub — NotebookLM generation wrapper

Connects to the notebooklm CLI to generate artifacts for a trip.
Usage: python3 notebooklm_generate.py LAURIS slide-deck
       python3 notebooklm_generate.py LAURIS audio
       python3 notebooklm_generate.py LAURIS infographic
       python3 notebooklm_generate.py LAURIS flashcards

Notebook IDs can be partial (matched via notebooklm use).
Artifacts are downloaded to the vault trip folder and recorded in trip-hub.db.
"""

import sys
import os
import json
import subprocess
import time
import re

# Paths
TRIP_HUB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(TRIP_HUB_DIR, 'data', 'trip-hub.db')
VAULT_DIR = os.path.expanduser('~/vault-famille')
ARTIFACTS_DIR = os.path.join(VAULT_DIR, 'Partages', 'Travel')

# Map trip name → notebook id prefix, vault folder
TRIP_MAP = {
    'lauris': {
        'notebook_prefix': 'eca72cd2',
        'folder': 'Lauris-2026',
        'destination': 'Lauris (Luberon) — Juillet 2026',
    },
}

# Map artifact type → CLI subcommand, filename pattern
ARTIFACT_MAP = {
    'slide-deck': {
        'generate_cmd': 'slide-deck',
        'ext': '.pdf',
        'format_flag': '--format detailed',
        'download_ext': 'pdf',
        'prompt': (
            'Guide du séjour à {destination}.\n'
            'Famille : Julien, Justine, Ambre (2.5 ans), Céleste (6 mois).\n'
            'Réunion famille élargie certains jours (8 personnes max).\n'
            'Inclus : présentation, activités adaptées aux tout-petits, météo, '
            'itinéraire jour par jour, bonnes adresses, infos pratiques.\n'
            'Design clair, lisible, adapté à l\'impression.'
        ),
    },
    'audio': {
        'generate_cmd': 'audio',
        'ext': '.mp3',
        'format_flag': '--format deep-dive',
        'download_ext': 'audio',
        'prompt': (
            'Podcast sur le séjour à {destination}.\n'
            'Ambiance détendue, conversation entre amis.\n'
            'Sujets : activités à ne pas manquer, astuces avec enfants en bas âge, '
            'météo, bons plans.'
        ),
    },
    'infographic': {
        'generate_cmd': 'infographic',
        'ext': '.png',
        'format_flag': '--orientation landscape',
        'download_ext': 'infographic',
        'prompt': (
            'Infographie récapitulative du voyage à {destination}.\n'
            'Inclus : météo, top 3 activités, infos clés, compteur de jours.'
        ),
    },
    'flashcards': {
        'generate_cmd': 'flashcards',
        'ext': '.md',
        'format_flag': '',
        'download_ext': 'flashcards',
        'prompt': (
            'Crée un jeu de flashcards sur {destination}.\n'
            'Face A : nom du lieu ou activité.\n'
            'Face B : description, conseils, horaires.\n'
            '15-20 cartes pour apprendre la destination avant le départ.'
        ),
    },
}


def run_notebooklm(args, timeout=300):
    """Run a notebooklm CLI command and return output."""
    cmd = ['notebooklm'] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return '', 'TIMEOUT', -1
    except FileNotFoundError:
        return '', 'notebooklm CLI not found', -1


def select_notebook(trip_key):
    """Select the notebook for a trip."""
    info = TRIP_MAP.get(trip_key.lower())
    if not info:
        print(f"❌ Unknown trip: {trip_key}")
        print(f"   Available: {', '.join(TRIP_MAP.keys())}")
        sys.exit(1)
    
    stdout, stderr, rc = run_notebooklm(['use', info['notebook_prefix']], timeout=10)
    if rc != 0:
        print(f"❌ Failed to select notebook: {stderr}")
        sys.exit(1)
    print(f"📓 Notebook selected: {info['destination']}")
    return info


def generate_artifact(trip_info, artifact_type, verbose=False):
    """Generate an artifact via NotebookLM."""
    info = ARTIFACT_MAP.get(artifact_type)
    if not info:
        print(f"❌ Unknown artifact type: {artifact_type}")
        print(f"   Available: {', '.join(ARTIFACT_MAP.keys())}")
        sys.exit(1)

    dest = trip_info['destination']
    prompt = info['prompt'].format(destination=dest)

    print(f"🎯 Generating {artifact_type}...")
    print(f"   Prompt: {prompt[:80]}...")
    
    # Build the generate command
    gen_args = ['generate', info['generate_cmd'], '--language', 'fr', '--wait', prompt]
    if info['format_flag']:
        gen_args = ['generate', info['generate_cmd']] + info['format_flag'].split() + ['--language', 'fr', '--wait', prompt]

    if verbose:
        print(f"   Running: notebooklm {' '.join(gen_args)}")

    stdout, stderr, rc = run_notebooklm(gen_args, timeout=600)
    
    if rc != 0:
        print(f"❌ Generation failed: {stderr[:500]}")
        print(f"   stdout: {stdout[:500]}")
        return None

    # Parse artifact ID from output
    # Look for patterns like "Artifact <id> created" or ID in the output
    artifact_id = None
    id_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', stdout)
    if id_match:
        artifact_id = id_match.group(1)
    
    if not artifact_id:
        print(f"⚠️  Could not extract artifact ID from output")
        print(f"   stdout: {stdout[:300]}")
        return None

    print(f"✅ Generated! Artifact ID: {artifact_id}")
    return artifact_id


def download_artifact(trip_info, artifact_type, artifact_id):
    """Download a generated artifact."""
    info = ARTIFACT_MAP.get(artifact_type)
    folder = trip_info['folder']
    trip_dir = os.path.join(ARTIFACTS_DIR, folder)
    os.makedirs(trip_dir, exist_ok=True)

    # Build filename
    base_name = f"{artifact_type}-{trip_info['folder'].lower()}"
    file_path = os.path.join(trip_dir, base_name + info['ext'])

    print(f"💾 Downloading to {file_path}...")
    
    download_args = ['download', info['download_ext'], file_path]
    stdout, stderr, rc = run_notebooklm(download_args, timeout=120)

    if rc != 0:
        print(f"❌ Download failed: {stderr[:300]}")
        return None

    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ Downloaded: {file_path} ({size / 1024:.1f} KB)")
        return file_path
    else:
        print(f"⚠️  File not found after download: {file_path}")
        return None


def record_artifact(trip_id, artifact_type, title, file_path, notebooklm_id):
    """Record artifact in trip-hub.db."""
    import sqlite3
    
    if not os.path.exists(DB_PATH):
        print(f"⚠️  DB not found at {DB_PATH}, skipping record")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO trip_artifacts (trip_id, type, title, file_path, notebooklm_id, status)
        VALUES (?, ?, ?, ?, ?, 'current')
    """, (trip_id, artifact_type, title, file_path, notebooklm_id))
    conn.commit()
    conn.close()
    print(f"📝 Recorded in trip_artifacts (trip_id={trip_id})")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 notebooklm_generate.py <trip_key> <artifact_type> [--verbose]")
        print("")
        print("  trip_key:      lauris")
        print("  artifact_type: slide-deck, audio, infographic, flashcards")
        sys.exit(1)

    trip_key = sys.argv[1]
    artifact_type = sys.argv[2]
    verbose = '--verbose' in sys.argv

    # Select notebook
    trip_info = select_notebook(trip_key)

    # Generate
    artifact_id = generate_artifact(trip_info, artifact_type, verbose)
    if not artifact_id:
        sys.exit(1)

    # Download
    file_path = download_artifact(trip_info, artifact_type, artifact_id)
    if not file_path:
        sys.exit(1)

    # Record in DB
    trip_db_id = f"lauris-2026"  # Will match our trip ID convention
    record_artifact(
        trip_id=trip_db_id,
        artifact_type=artifact_type,
        title=f"{artifact_type.capitalize()} — {trip_info['destination']}",
        file_path=file_path,
        notebooklm_id=artifact_id,
    )

    print(f"\n🎉 Done! {artifact_type} ready at {file_path}")


if __name__ == '__main__':
    main()
