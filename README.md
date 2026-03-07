# YouTube2NotebookLM

YouTube-Videos suchen und automatisch an Google NotebookLM senden — als Claude Code Skills.

**Der Clou:** NotebookLM uebernimmt die gesamte Analyse kostenlos (kein Token-Verbrauch in Claude Code).

---

## Kurzanleitung

```
/yt-search "thema" --count 5          # Videos suchen
```
Videos auswaehlen (z.B. "1, 3, 5"), dann:
```
/notebook-lm create --name "Thema" --urls URL1 URL2 URL3
/notebook-lm ask --notebook-id ID --question "Was sind die Kernaussagen?"
/notebook-lm audio --notebook-id ID
```

---

## Einrichtung (einmalig)

```bash
uv pip install yt-dlp
uv pip install notebooklm-py[browser]
uv run playwright install chromium
uv run notebooklm login              # Oeffnet Browser fuer Google-Login
```

---

## Skill 1: `/yt-search`

YouTube durchsuchen mit strukturierten Ergebnissen (Titel, Kanal, Subscribers, Views, Dauer, Datum, URL).

### Beispiele

```
/yt-search "claude code skills"
/yt-search "AI agents" --count 10 --months 3
/yt-search "machine learning" --no-date-filter
```

### Optionen

| Flag | Default | Beschreibung |
|------|---------|-------------|
| `--count N` | 20 | Anzahl Ergebnisse |
| `--months N` | 6 | Nur Videos der letzten N Monate |
| `--no-date-filter` | — | Alle Ergebnisse unabhaengig vom Datum |
| `--json` | — | Maschinenlesbare JSON-Ausgabe |

### Beispiel-Ausgabe

```
────────────────────────────────────────────────────────────
  1. Claude Code - Full Tutorial for Beginners
     Tech With Tim (2.0M subs)  ·  202,048 views (0.10x)  ·  35:48  ·  Feb 27, 2026
     https://youtube.com/watch?v=ntDIxaeo3Wg
────────────────────────────────────────────────────────────
  2. Claude Code Tutorial for Beginners
     Kevin Stratvert (4.2M subs)  ·  446,921 views (0.11x)  ·  14:43  ·  Dec 22, 2025
     https://youtube.com/watch?v=eMZmDH3T2bY
────────────────────────────────────────────────────────────
```

---

## Skill 2: `/notebook-lm`

Notebooks erstellen, YouTube-Videos als Quellen hinzufuegen, Fragen stellen und Audio-Podcasts generieren.

### Befehle

| Befehl | Beschreibung |
|--------|-------------|
| `create --name "Name" --urls URL1 URL2` | Notebook erstellen mit YouTube-URLs |
| `list` | Alle Notebooks anzeigen |
| `sources --notebook-id ID` | Quellen eines Notebooks anzeigen |
| `ask --notebook-id ID --question "Frage"` | Frage an ein Notebook stellen |
| `audio --notebook-id ID` | Audio-Podcast generieren |

### Audio-Optionen

| Flag | Default | Beschreibung |
|------|---------|-------------|
| `--language` | `de` | Sprache des Podcasts |
| `--instructions` | — | Zusaetzliche Anweisungen (z.B. "Fokus auf praktische Tipps") |
| `--output pfad.wav` | — | Audio-Datei lokal speichern |

---

## Typischer Workflow

```
1.  /yt-search "vibe coding" --count 10
    → Ergebnisse mit Nummern anzeigen

2.  "Nimm 1, 3, 7"
    → Claude Code merkt sich die URLs

3.  /notebook-lm create --name "Vibe Coding Research" --urls URL1 URL3 URL7
    → Notebook wird erstellt, Quellen verarbeitet

4.  /notebook-lm ask --notebook-id ID --question "Vergleiche die Ansaetze"
    → NotebookLM analysiert (kostenlos, kein Token-Verbrauch)

5.  /notebook-lm audio --notebook-id ID --output vibe-coding.wav
    → Audio-Podcast wird generiert und heruntergeladen
```

---

## Direkte Nutzung (ohne Claude Code)

```bash
# YouTube-Suche
uv run python scripts/yt_search.py "query" --count 5
uv run python scripts/yt_search.py "query" --json

# NotebookLM
uv run python scripts/nlm_pipeline.py create --name "Test" --urls "https://youtube.com/watch?v=..."
uv run python scripts/nlm_pipeline.py list
uv run python scripts/nlm_pipeline.py sources --notebook-id ID
uv run python scripts/nlm_pipeline.py ask --notebook-id ID --question "Frage"
uv run python scripts/nlm_pipeline.py audio --notebook-id ID --output podcast.wav
```

---

## Projektstruktur

```
YouTube2NotebookLM/
├── .claude/commands/       # Claude Code Skills
│   ├── yt-search.md        #   /yt-search
│   └── notebook-lm.md      #   /notebook-lm
├── scripts/
│   ├── yt_search.py        # YouTube-Suche via yt-dlp (subprocess)
│   └── nlm_pipeline.py     # NotebookLM-Integration (async, notebooklm-py)
├── CLAUDE.md               # Projektregeln fuer Claude Code
├── README.md
└── rules.md                # Erkenntnisse & Issue-Tracking
```

## Troubleshooting

| Problem | Loesung |
|---------|---------|
| `yt-dlp not found` | `uv pip install yt-dlp` |
| `notebooklm` Auth-Fehler | `uv run notebooklm login` im Terminal ausfuehren |
| Browser oeffnet nicht | `uv run playwright install chromium` |
| `python` not found | Immer `uv run python` statt `python` verwenden |
| Audio-Generierung dauert lang | Normal — kann 2-5 Minuten dauern, Timeout ist 10 Min |
