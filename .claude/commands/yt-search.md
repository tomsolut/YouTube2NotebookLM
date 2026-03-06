---
description: "YouTube durchsuchen und strukturierte Video-Ergebnisse anzeigen"
argument-hint: "<query> [--count N] [--months N] [--no-date-filter]"
allowed-tools:
  - Bash
---

Fuehre das YouTube-Such-Skript aus und praesentiere die Ergebnisse.

Kommando: `uv run python scripts/yt_search.py $ARGUMENTS`

Zeige die Ergebnisse dem User in einer uebersichtlichen Darstellung.

Falls der User Videos auswaehlen moechte (z.B. "1, 3, 5" oder "alle"), merke dir die entsprechenden URLs aus den Ergebnissen. Biete anschliessend an, die ausgewaehlten Videos an NotebookLM zu senden (via `/notebook-lm`).
