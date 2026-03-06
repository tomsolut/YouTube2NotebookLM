# Rules & Erkenntnisse

## Issue-Tracking

| Issue | Titel | Status |
|-------|-------|--------|
| #1 | YouTube-Suche Skill | erledigt |
| #2 | NotebookLM-Integration | erledigt |
| #3 | Pipeline-Test & Doku | erledigt |

## Erkenntnisse

- yt-dlp wird als CLI via subprocess aufgerufen (robuster als Python API)
- NotebookLM-Auth via `notebooklm login` (Browser-basiert, einmalig)
- Skills sind projekt-lokal in `.claude/commands/`
- notebooklm-py nutzt async API (`NotebookLMClient.from_storage()` als async context manager)
- Perplexity hat die notebooklm-py API falsch beschrieben — immer gegen echte Doku verifizieren
- `python` existiert nicht auf macOS, immer `uv run python` oder `python3` verwenden
- `sources.add_url()` erkennt YouTube-URLs automatisch und nutzt die richtige Methode
- Audio-Generierung kann mehrere Minuten dauern, `wait_for_completion()` mit timeout=600 nutzen
