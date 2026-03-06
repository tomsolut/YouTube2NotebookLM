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

### Nutzung in Claude Code

Dieses Projekt oeffnen und die Skills direkt nutzen:

#### YouTube durchsuchen

```
/yt-search "claude code skills" --count 5
/yt-search "AI agents" --months 3
/yt-search "machine learning" --no-date-filter
```

**Optionen:**
| Flag | Default | Beschreibung |
|------|---------|-------------|
| `--count N` | 20 | Anzahl Ergebnisse |
| `--months N` | 6 | Nur Videos der letzten N Monate |
| `--no-date-filter` | — | Alle Ergebnisse unabhaengig vom Datum |
| `--json` | — | Maschinenlesbare JSON-Ausgabe |

#### NotebookLM Pipeline

```
/notebook-lm create --name "Mein Notebook" --urls URL1 URL2
/notebook-lm list
/notebook-lm ask --notebook-id ID --question "Was sind die Kernaussagen?"
/notebook-lm audio --notebook-id ID --language de --output podcast.wav
```

### Typischer Workflow

1. `/yt-search "thema"` — Videos suchen
2. Videos auswaehlen (z.B. "1, 3, 5")
3. `/notebook-lm create --name "Thema" --urls ...` — Notebook erstellen
4. `/notebook-lm ask --notebook-id ID --question "Zusammenfassung?"` — Analysieren
5. `/notebook-lm audio --notebook-id ID` — Podcast generieren

### Direkte Nutzung (ohne Claude Code)

```bash
# YouTube-Suche
uv run python scripts/yt_search.py "query" --count 5

# NotebookLM
uv run python scripts/nlm_pipeline.py create --name "Test" --urls "https://youtube.com/watch?v=..."
uv run python scripts/nlm_pipeline.py list
uv run python scripts/nlm_pipeline.py ask --notebook-id ID --question "Frage"
uv run python scripts/nlm_pipeline.py audio --notebook-id ID --output podcast.wav
```

## Projektstruktur

```
YouTube2NotebookLM/
├── .claude/commands/       # Claude Code Skills
│   ├── yt-search.md
│   └── notebook-lm.md
├── scripts/
│   ├── yt_search.py        # YouTube-Suche via yt-dlp
│   └── nlm_pipeline.py     # NotebookLM-Integration (async)
├── CLAUDE.md
├── README.md
└── rules.md
```
