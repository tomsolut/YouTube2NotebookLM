# Rules & Erkenntnisse

## Issue-Tracking

| Issue | Titel | Status |
|-------|-------|--------|
| #1 | YouTube-Suche Skill | erledigt |
| #2 | NotebookLM-Integration | erledigt |
| #3 | Pipeline-Test & Doku | erledigt |
| #4 | Podcast-Publishing mit Telegram-Approval | erledigt |
| #6 | Telegram-Approval von Polling auf n8n-Webhook | erledigt |

## Erkenntnisse

- yt-dlp wird als CLI via subprocess aufgerufen (robuster als Python API)
- NotebookLM-Auth via `notebooklm login` (Browser-basiert, einmalig)
- Skills sind projekt-lokal in `.claude/commands/`
- notebooklm-py nutzt async API (`NotebookLMClient.from_storage()` als async context manager)
- Perplexity hat die notebooklm-py API falsch beschrieben — immer gegen echte Doku verifizieren
- `python` existiert nicht auf macOS, immer `uv run python` oder `python3` verwenden
- `sources.add_url()` erkennt YouTube-URLs automatisch und nutzt die richtige Methode
- Audio-Generierung kann mehrere Minuten dauern, `wait_for_completion()` mit timeout=600 nutzen
- `GenerationStatus` hat kein `artifact_id` — stattdessen `task_id` und `is_complete`/`is_failed`
- `download_audio()` braucht kein `artifact_id`, findet das neueste Audio automatisch
- `AudioLength.LONG` für längere Podcasts nutzen
- Multiline XML über SSH-sed ist fragil — besser Feed per scp runterladen, lokal bearbeiten, hochladen
- Telegram Long-Polling braucht erhöhten httpx-Timeout (mind. 60s)
- ffmpeg ist auf dem Server vorhanden, lokal nicht — WAV-Konvertierung auf Server auslagern
- n8n API: Connections verwenden Node-Namen (nicht IDs), Aktivierung via POST .../activate
- n8n: `N8N_RESTRICT_FILE_ACCESS_TO` muss `/var/www/podcast` enthalten fuer Feed-Zugriff
- BlueDot nutzt Telegram-Webhooks mit separatem Bot-Token (`TELEGRAM_BOT_TOKEN_BLUEDOT`) — kein Polling-Konflikt mit NLM-Bot
- NLM-Callback-Daten prefixed mit `nlm_` zur Unterscheidung von anderen Bots
