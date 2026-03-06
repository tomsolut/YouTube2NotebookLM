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
uv run python scripts/nlm_pipeline.py audio --notebook-id ID --output podcast.wav
```

## Dependencies
```bash
uv pip install yt-dlp
uv pip install notebooklm-py[browser]
```

## Workflow
- GitHub-First: Issue → Branch → Implementierung → Merge
- Branch-Konvention: `issue-<Nr>-<titel>`
- Commits: Conventional Commits (Deutsch)
