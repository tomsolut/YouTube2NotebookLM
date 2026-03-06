# Rules & Erkenntnisse

## Issue-Tracking

| Issue | Titel | Status |
|-------|-------|--------|
| #1 | YouTube-Suche Skill | offen |
| #2 | NotebookLM-Integration | geplant |
| #3 | Pipeline-Test & Doku | geplant |

## Erkenntnisse

- yt-dlp wird als CLI via subprocess aufgerufen (robuster als Python API)
- NotebookLM-Auth via `notebooklm login` (Browser-basiert, einmalig)
- Skills sind projekt-lokal in `.claude/commands/`
