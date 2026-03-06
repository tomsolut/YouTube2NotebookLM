# YouTube2NotebookLM

YouTube-Videos suchen und automatisch an Google NotebookLM senden — als Claude Code Skills.

## Was macht dieses Projekt?

1. **`/yt-search`** — YouTube durchsuchen via yt-dlp, strukturierte Ergebnisse mit Titel, Kanal, Views, Dauer und Datum
2. **`/notebook-lm`** — Ausgewaehlte Videos an Google NotebookLM senden fuer Analyse und Audio-Podcasts

Der Clou: NotebookLM uebernimmt die gesamte Analyse kostenlos (kein Token-Verbrauch in Claude Code).

## Installation

### Voraussetzungen

```bash
uv pip install yt-dlp
uv pip install notebooklm-py[browser]
notebooklm login  # Einmalige Browser-Authentifizierung
```

### Nutzung

In Claude Code im Projektverzeichnis:

```
/yt-search "claude code skills" --count 5
```

Videos auswaehlen, dann:

```
/notebook-lm --urls URL1 URL2 --name "Mein Notebook"
```

## Projektstruktur

```
YouTube2NotebookLM/
├── .claude/commands/       # Claude Code Skills
│   ├── yt-search.md
│   └── notebook-lm.md
├── scripts/
│   ├── yt_search.py        # YouTube-Suche
│   └── nlm_pipeline.py     # NotebookLM-Integration
├── CLAUDE.md
├── README.md
└── rules.md
```
