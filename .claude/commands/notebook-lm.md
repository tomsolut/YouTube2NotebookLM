---
description: "YouTube-Videos an NotebookLM senden fuer Analyse und Audio-Podcasts"
argument-hint: "[create|list|ask|audio] [Optionen]"
allowed-tools:
  - Bash
---

NotebookLM-Pipeline fuer Analyse und Audio-Podcasts aus YouTube-Videos.

## Workflow

1. Pruefe ob der User bereits URLs aus einer /yt-search Konversation hat
2. Falls nicht, frage nach URLs oder schlage /yt-search vor

## Befehle

Notebook erstellen mit YouTube-URLs:
```
uv run python scripts/nlm_pipeline.py create --name "Notebook Name" --urls URL1 URL2
```

Alle Notebooks auflisten:
```
uv run python scripts/nlm_pipeline.py list
```

Quellen eines Notebooks anzeigen:
```
uv run python scripts/nlm_pipeline.py sources --notebook-id ID
```

Frage an ein Notebook stellen:
```
uv run python scripts/nlm_pipeline.py ask --notebook-id ID --question "Frage"
```

Audio-Podcast generieren:
```
uv run python scripts/nlm_pipeline.py audio --notebook-id ID [--language de] [--instructions "..."] [--output pfad.wav]
```

## Auth-Hinweis

Falls die Authentifizierung fehlschlaegt, den User bitten `notebooklm login` im Terminal auszufuehren.
