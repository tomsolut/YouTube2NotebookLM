#!/usr/bin/env python3
"""NotebookLM pipeline — create notebooks, add YouTube sources, ask questions, generate audio."""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from notebooklm import NotebookLMClient

load_dotenv()

PENDING_FILE = Path(__file__).parent.parent / "pending_generations.json"


async def create_notebook(client, title, urls):
    """Create a notebook and add YouTube URLs as sources."""
    notebook = await client.notebooks.create(title)
    print(f"Notebook erstellt: {notebook.title} (ID: {notebook.id})")

    sources = []
    for url in urls:
        print(f"  Quelle hinzufuegen: {url} ...", end=" ", flush=True)
        source = await client.sources.add_url(notebook.id, url, wait=True, wait_timeout=180)
        print(f"OK ({source.title})")
        sources.append(source)
        time.sleep(1)  # Rate limiting

    print(f"\n{len(sources)} Quelle(n) hinzugefuegt.")
    print(f"Notebook-ID: {notebook.id}")
    return notebook


async def list_notebooks(client):
    """List all notebooks."""
    notebooks = await client.notebooks.list()
    if not notebooks:
        print("Keine Notebooks gefunden.")
        return
    print(f"{len(notebooks)} Notebook(s):\n")
    for nb in notebooks:
        print(f"  {nb.title}")
        print(f"    ID: {nb.id}")
        print()


async def ask_question(client, notebook_id, question):
    """Ask a question to a notebook."""
    print(f"Frage: {question}\n")
    result = await client.chat.ask(notebook_id, question)
    print(f"Antwort:\n{result.answer}")
    if result.references:
        print(f"\nReferenzen: {len(result.references)}")
    return result


def _load_pending() -> list:
    """Load pending generations from JSON file."""
    if PENDING_FILE.exists():
        return json.loads(PENDING_FILE.read_text())
    return []


def _save_pending(entries: list):
    """Save pending generations to JSON file."""
    PENDING_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


def _add_pending(notebook_id: str, task_id: str, description: str = ""):
    """Add a pending generation entry."""
    entries = _load_pending()
    entries.append({
        "notebook_id": notebook_id,
        "task_id": task_id,
        "description": description,
        "started_at": datetime.now().isoformat(),
    })
    _save_pending(entries)


def _remove_pending(task_id: str):
    """Remove a completed/failed generation entry."""
    entries = _load_pending()
    entries = [e for e in entries if e["task_id"] != task_id]
    _save_pending(entries)


async def _send_telegram(message: str):
    """Send a Telegram notification via @tomsolut_bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("WARNUNG: TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID nicht gesetzt — keine Benachrichtigung.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as http:
        resp = await http.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        })
        resp.raise_for_status()
    print("Telegram-Benachrichtigung gesendet.")


async def generate_audio(client, notebook_id, language="de", instructions=None,
                         audio_length=None, output_path=None, no_wait=False):
    """Generate audio overview for a notebook."""
    from notebooklm import AudioLength

    print("Audio-Podcast wird generiert (kann einige Minuten dauern)...")

    # AudioLength: SHORT, DEFAULT, LONG
    length = None
    if audio_length:
        length = getattr(AudioLength, audio_length.upper(), None)

    status = await client.artifacts.generate_audio(
        notebook_id,
        language=language,
        instructions=instructions,
        audio_length=length,
    )

    task_id = status.task_id
    print(f"Generation gestartet (Task-ID: {task_id})")

    desc = instructions[:80] if instructions else "Audio"
    _add_pending(notebook_id, task_id, desc)

    if no_wait:
        print(f"\nFire-and-Forget: Task-ID gespeichert in {PENDING_FILE}")
        print(f"Status pruefen mit: uv run python scripts/nlm_pipeline.py check-status --notebook-id {notebook_id} --task-id {task_id}")
        return status

    print("Warte auf Fertigstellung...")

    result = await client.artifacts.wait_for_completion(
        notebook_id,
        task_id,
        timeout=1200,
    )

    if result.is_complete:
        print(f"Audio fertig! (Task-ID: {task_id})")
        _remove_pending(task_id)
        await _send_telegram(f"🎙 *Audio fertig!*\nTask: `{task_id}`\nNotebook: `{notebook_id}`")
        if output_path:
            path = await client.artifacts.download_audio(notebook_id, output_path)
            print(f"Heruntergeladen: {path}")
    elif result.is_failed:
        print(f"Fehler: {result.error}")
        _remove_pending(task_id)
        await _send_telegram(f"❌ *Audio-Generierung fehlgeschlagen*\nTask: `{task_id}`\nFehler: {result.error}")
    else:
        print(f"Status: {result.status} (Task laeuft noch)")

    return result


async def check_status(client, notebook_id, task_id, download_path=None):
    """Check status of a running audio generation and notify via Telegram."""
    print(f"Pruefe Status fuer Task {task_id}...")

    result = await client.artifacts.poll_status(notebook_id, task_id)

    if result.is_complete:
        print(f"Audio fertig! (Task-ID: {task_id})")
        _remove_pending(task_id)
        await _send_telegram(f"🎙 *Audio fertig!*\nTask: `{task_id}`\nNotebook: `{notebook_id}`")
        if download_path:
            path = await client.artifacts.download_audio(notebook_id, download_path)
            print(f"Heruntergeladen: {path}")
    elif result.is_failed:
        print(f"Fehler: {result.error}")
        _remove_pending(task_id)
        await _send_telegram(f"❌ *Audio-Generierung fehlgeschlagen*\nTask: `{task_id}`")
    else:
        print(f"Status: Noch in Bearbeitung (Task-ID: {task_id})")

    return result


async def check_all_pending(client):
    """Check all pending generations and notify on completion."""
    entries = _load_pending()
    if not entries:
        print("Keine ausstehenden Generierungen.")
        return

    print(f"{len(entries)} ausstehende Generierung(en):\n")
    for entry in list(entries):
        print(f"  Task: {entry['task_id']}")
        print(f"  Notebook: {entry['notebook_id']}")
        print(f"  Gestartet: {entry['started_at']}")
        print(f"  Beschreibung: {entry.get('description', '-')}")
        await check_status(client, entry["notebook_id"], entry["task_id"])
        print()


async def download_audio_only(client, notebook_id, output_path):
    """Download audio from a notebook without starting a new generation."""
    print(f"Lade Audio herunter von Notebook {notebook_id}...")
    path = await client.artifacts.download_audio(notebook_id, output_path)
    print(f"Heruntergeladen: {path}")
    return path


async def list_sources(client, notebook_id):
    """List sources in a notebook."""
    sources = await client.sources.list(notebook_id)
    if not sources:
        print("Keine Quellen gefunden.")
        return
    print(f"{len(sources)} Quelle(n):\n")
    for s in sources:
        print(f"  {s.title}")
        print(f"    ID: {s.id} | Status: {s.status}")
        print()


async def main():
    parser = argparse.ArgumentParser(description="NotebookLM Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Verfuegbare Befehle")

    # create
    create_parser = subparsers.add_parser("create", help="Notebook erstellen mit YouTube-URLs")
    create_parser.add_argument("--name", required=True, help="Notebook-Titel")
    create_parser.add_argument("--urls", nargs="+", required=True, help="YouTube-URLs")

    # list
    subparsers.add_parser("list", help="Alle Notebooks auflisten")

    # sources
    sources_parser = subparsers.add_parser("sources", help="Quellen eines Notebooks auflisten")
    sources_parser.add_argument("--notebook-id", required=True, help="Notebook-ID")

    # ask
    ask_parser = subparsers.add_parser("ask", help="Frage an ein Notebook stellen")
    ask_parser.add_argument("--notebook-id", required=True, help="Notebook-ID")
    ask_parser.add_argument("--question", required=True, help="Die Frage")

    # audio
    audio_parser = subparsers.add_parser("audio", help="Audio-Podcast generieren")
    audio_parser.add_argument("--notebook-id", required=True, help="Notebook-ID")
    audio_parser.add_argument("--language", default="de", help="Sprache (default: de)")
    audio_parser.add_argument("--instructions", help="Zusaetzliche Anweisungen fuer den Podcast")
    audio_parser.add_argument("--length", choices=["short", "default", "long"], help="Podcast-Laenge")
    audio_parser.add_argument("--output", help="Ausgabepfad fuer die Audio-Datei")
    audio_parser.add_argument("--no-wait", action="store_true", help="Fire-and-Forget: Generierung starten ohne zu warten")

    # check-status
    cs_parser = subparsers.add_parser("check-status", help="Status einer laufenden Audio-Generierung pruefen")
    cs_parser.add_argument("--notebook-id", help="Notebook-ID (optional wenn nur eine pending)")
    cs_parser.add_argument("--task-id", help="Task-ID (optional wenn nur eine pending)")
    cs_parser.add_argument("--all", action="store_true", help="Alle ausstehenden Generierungen pruefen")
    cs_parser.add_argument("--output", help="Audio herunterladen wenn fertig")

    # download
    dl_parser = subparsers.add_parser("download", help="Fertiges Audio herunterladen (ohne neue Generierung)")
    dl_parser.add_argument("--notebook-id", required=True, help="Notebook-ID")
    dl_parser.add_argument("--output", required=True, help="Ausgabepfad fuer die Audio-Datei")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = await NotebookLMClient.from_storage()
    async with client:
        if args.command == "create":
            notebook = await create_notebook(client, args.name, args.urls)
            # Output notebook ID as JSON for pipeline usage
            print(json.dumps({"notebook_id": notebook.id, "title": notebook.title}))

        elif args.command == "list":
            await list_notebooks(client)

        elif args.command == "sources":
            await list_sources(client, args.notebook_id)

        elif args.command == "ask":
            await ask_question(client, args.notebook_id, args.question)

        elif args.command == "audio":
            await generate_audio(
                client,
                args.notebook_id,
                language=args.language,
                instructions=args.instructions,
                audio_length=args.length,
                output_path=args.output,
                no_wait=args.no_wait,
            )

        elif args.command == "check-status":
            if args.all:
                await check_all_pending(client)
            else:
                notebook_id = args.notebook_id
                task_id = args.task_id
                # Auto-detect from pending if not specified
                if not notebook_id or not task_id:
                    entries = _load_pending()
                    if len(entries) == 1:
                        notebook_id = notebook_id or entries[0]["notebook_id"]
                        task_id = task_id or entries[0]["task_id"]
                    elif len(entries) == 0:
                        print("Keine ausstehenden Generierungen.")
                        sys.exit(0)
                    else:
                        print(f"{len(entries)} ausstehende Generierungen — bitte --notebook-id und --task-id angeben oder --all nutzen.")
                        for e in entries:
                            print(f"  Task: {e['task_id']} | Notebook: {e['notebook_id']} | {e.get('description', '-')}")
                        sys.exit(1)
                await check_status(client, notebook_id, task_id, download_path=args.output)

        elif args.command == "download":
            await download_audio_only(client, args.notebook_id, args.output)


if __name__ == "__main__":
    asyncio.run(main())
