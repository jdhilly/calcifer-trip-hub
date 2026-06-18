# 🧭 Calcifer Trip Hub

Préparation de voyage intelligente — de l'idée de destination jusqu'au retour.

## Stack

| Couche | Technologie |
|--------|-------------|
| Frontend | SvelteKit 2 + Tailwind v4 + TypeScript strict |
| UI Kit | [`@calcifer/ui`](https://github.com/jdhilly/calcifer-ui) (thème dark « feu », composants NavShell, Card, Button…) |
| Backend | Python CLI + SQLite (via `better-sqlite3`) |
| Notifications | Telegram |
| IA | NotebookLM (génération de briefings, podcasts, infographies) |
| Sync | Syncthing + cron |

## Pages

| Route | Fonctionnalité |
|-------|----------------|
| `/` | Dashboard — liste des voyages avec statut (en cours/à venir/terminé) |
| `/catalog` | Catalogue d'articles global (274 articles) |
| `/[id]/` | Détail voyage — barre de progression + navigation vers les sous-pages |
| `/[id]/checklist` | Checklist interactive — compteurs départ, import depuis le catalogue |
| `/[id]/participants` | Participants — âge, rôles, blocs de présence, timeline drag & drop |
| `/[id]/briefing` | Briefing — génération NotebookLM (slide-deck, podcast, infographie, flashcards) |
| `/[id]/journal` | Journal de bord — carnets quotidiens avec dates et auteurs |

## Quick Start

```bash
# Backend
cd ~/apps/trip-hub
python3 src/db.py --init        # Initialiser la base
python3 scripts/migrate_from_todo.py  # Migrer depuis travel-checklist

# Frontend
cd frontend
npm install
npm run build

# Service systemd
systemctl --user start trip-hub
# → http://localhost:6000
```

## Architecture

```
~/apps/trip-hub/
├── src/
│   ├── cli.py          # CLI backend (CRUD, NotebookML generate, sync)
│   └── db.py           # Schéma SQLite + migrations
├── scripts/
│   ├── migrate_from_todo.py     # Migration one-shot TODO → Trip Hub
│   ├── notebooklm_generate.py   # Wrapper génération NotebookLM
│   └── sync_vault_to_trip_hub.py # Sync vault → DB (cron toutes les 6h)
├── frontend/
│   └── src/routes/
│       ├── +page.svelte
│       ├── catalog/
│       └── [id]/
│           ├── checklist/
│           ├── participants/
│           ├── briefing/
│           └── journal/
└── data/
    └── trip-hub.db
```

## NotebookLM

Le script `notebooklm_generate.py` automatise la génération d'artifacts :

```bash
python3 scripts/notebooklm_generate.py lauris slide-deck   # PDF guide visuel
python3 scripts/notebooklm_generate.py lauris audio         # Podcast MP3
python3 scripts/notebooklm_generate.py lauris infographic   # PNG récap
python3 scripts/notebooklm_generate.py lauris flashcards    # Flashcards
```

## Licence

MIT
