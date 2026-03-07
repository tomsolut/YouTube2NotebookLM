#!/usr/bin/env python3
"""NotebookLM pipeline — create notebooks, add YouTube sources, ask questions, generate audio."""

import argparse
import asyncio
import json
import sys
import time

from notebooklm import NotebookLMClient


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


async def generate_audio(client, notebook_id, language="de", instructions=None,
                         audio_length=None, output_path=None):
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

    print(f"Generation gestartet (Task-ID: {status.task_id})")
    print("Warte auf Fertigstellung...")

    result = await client.artifacts.wait_for_completion(
        notebook_id,
        status.task_id,
        timeout=600,
    )

    if result.is_complete:
        print(f"Audio fertig! (Task-ID: {status.task_id})")
        if output_path:
            path = await client.artifacts.download_audio(notebook_id, output_path)
            print(f"Heruntergeladen: {path}")
    elif result.is_failed:
        print(f"Fehler: {result.error}")
    else:
        print(f"Status: {result.status}")

    return result


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
            )


if __name__ == "__main__":
    asyncio.run(main())
