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
- Audio-Generierung kann mehrere Minuten dauern — `--no-wait` fuer Fire-and-Forget nutzen
- Bei Timeout NIEMALS neu generieren — stattdessen `check-status` fuer bestehende Task-ID nutzen
- `poll_status(notebook_id, task_id)` funktioniert auch in neuer Session (listet alle Artefakte)
- `GenerationStatus` hat kein `artifact_id` — stattdessen `task_id` und `is_complete`/`is_failed`
- `download_audio()` braucht kein `artifact_id`, findet das neueste Audio automatisch
- Telegram-Benachrichtigung via @tomsolut_bot bei Audio-Fertigstellung (TELEGRAM_BOT_TOKEN in .env)
- `AudioLength.LONG` für längere Podcasts nutzen
- Multiline XML über SSH-sed ist fragil — besser Feed per scp runterladen, lokal bearbeiten, hochladen
- Telegram Long-Polling braucht erhöhten httpx-Timeout (mind. 60s)
- ffmpeg ist auf dem Server vorhanden, lokal nicht — WAV-Konvertierung auf Server auslagern
- n8n API: Connections verwenden Node-Namen (nicht IDs), Aktivierung via POST .../activate
- n8n: `N8N_RESTRICT_FILE_ACCESS_TO` muss `/var/www/podcast` enthalten fuer Feed-Zugriff
- BlueDot nutzt Telegram-Webhooks mit separatem Bot-Token (`TELEGRAM_BOT_TOKEN_BLUEDOT`) — kein Polling-Konflikt mit NLM-Bot
- NLM-Callback-Daten prefixed mit `nlm_` zur Unterscheidung von anderen Bots
- WICHTIG: n8n-Container hat eigenen `TELEGRAM_BOT_TOKEN` — Webhook muss auf diesen Bot gesetzt werden, nicht auf lokale .env
- n8n Code-Nodes: `this.helpers.httpRequest()` verwenden statt `require('https')` — Task Runner Sandbox blockiert Module
- n8n Code-Nodes: `$getWorkflowStaticData()` statt `this.getWorkflowStaticData()` (v2 Syntax)
- Cloudflare Access: Nur freigegebene Webhook-Pfade erreichbar — NLM nutzt bestehenden BlueDot-Webhook-Pfad
- `/var/www/podcast/` Dateien muessen uid 1000 (node im Container) gehoeren
