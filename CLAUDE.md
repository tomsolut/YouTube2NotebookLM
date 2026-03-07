# YouTube2NotebookLM — Projektregeln

## Projektbeschreibung
Zwei Claude Code Skills als Pipeline:
1. `/yt-search` — YouTube durchsuchen via yt-dlp
2. `/notebook-lm` — Videos an Google NotebookLM senden

## Technologie
- Python-Skripte (kein Package, kein pyproject.toml)
- yt-dlp (CLI via subprocess)
- notebooklm-py (Python API)
- Skills sind projekt-lokal in `.claude/commands/`

## Befehle
```bash
# YouTube-Suche
uv run python scripts/yt_search.py "query" --count 5
uv run python scripts/yt_search.py "query" --json

# NotebookLM
uv run python scripts/nlm_pipeline.py create --name "Name" --urls URL1 URL2
uv run python scripts/nlm_pipeline.py list
uv run python scripts/nlm_pipeline.py ask --notebook-id ID --question "Frage"
uv run python scripts/nlm_pipeline.py audio --notebook-id ID --length long --output podcast.wav

# Podcast Publishing (Download → MP3 → Telegram-Approval → RSS)
uv run python scripts/publish_podcast.py init
uv run python scripts/publish_podcast.py publish --notebook-id ID --title "Titel"
```

## Dependencies
```bash
uv pip install yt-dlp
uv pip install notebooklm-py[browser]
uv pip install httpx
```

## Server & Infrastruktur
- Podcast-Server: `root@100.77.144.40` (Tailscale SSH)
- Podcast-URL: `https://podcast.tomsolut.work`
- NLM RSS-Feed: `https://podcast.tomsolut.work/nlm-feed.xml`
- Bestehender Feed: `feed.xml` (Tom's Weekly Briefings — nicht anfassen)
- Telegram-Bot für Approval: Config in `.env`

## Workflow
- GitHub-First: Issue → Branch → Implementierung → Merge
- Branch-Konvention: `issue-<Nr>-<titel>`
- Commits: Conventional Commits (Deutsch)
