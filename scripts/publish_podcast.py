#!/usr/bin/env python3
"""Publish NotebookLM audio podcasts to RSS feed with Telegram approval."""

import argparse
import asyncio
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Server config
SERVER_HOST = "root@100.77.144.40"
PODCAST_DIR = "/var/www/podcast"
EPISODES_DIR = f"{PODCAST_DIR}/episodes"
FEED_FILE = f"{PODCAST_DIR}/nlm-feed.xml"
BASE_URL = "https://podcast.tomsolut.work"
N8N_WEBHOOK_URL = "http://100.77.144.40:5678/webhook/nlm-podcast-approval"


async def download_audio(notebook_id: str, output_path: str) -> str:
    """Download audio from NotebookLM."""
    from notebooklm import NotebookLMClient

    print(f"Audio herunterladen von Notebook {notebook_id}...")
    client = await NotebookLMClient.from_storage()
    async with client:
        path = await client.artifacts.download_audio(notebook_id, output_path)
        print(f"Heruntergeladen: {path}")
        return path


def upload_and_convert(local_wav: str, remote_filename: str) -> dict:
    """Upload WAV to server and convert to MP3 via ffmpeg."""
    remote_wav = f"/tmp/{remote_filename}.wav"
    remote_mp3 = f"{EPISODES_DIR}/{remote_filename}.mp3"

    print(f"Upload {local_wav} -> {SERVER_HOST}:{remote_wav}")
    subprocess.run(
        ["scp", local_wav, f"{SERVER_HOST}:{remote_wav}"],
        check=True,
    )

    print(f"Konvertiere WAV -> MP3 auf Server...")
    subprocess.run(
        ["ssh", SERVER_HOST, f"ffmpeg -y -i {remote_wav} -codec:a libmp3lame -qscale:a 2 {remote_mp3} && rm {remote_wav}"],
        check=True,
    )

    # Get file size and duration
    result = subprocess.run(
        ["ssh", SERVER_HOST, f"stat -c %s {remote_mp3} && ffprobe -v quiet -show_entries format=duration -of csv=p=0 {remote_mp3}"],
        capture_output=True, text=True, check=True,
    )
    lines = result.stdout.strip().split("\n")
    file_size = int(lines[0])
    duration_secs = float(lines[1])
    minutes = int(duration_secs // 60)
    seconds = int(duration_secs % 60)
    duration_str = f"{minutes}:{seconds:02d}"

    print(f"MP3 erstellt: {remote_mp3} ({file_size} bytes, {duration_str})")
    return {
        "remote_path": remote_mp3,
        "url": f"{BASE_URL}/episodes/{remote_filename}.mp3",
        "file_size": file_size,
        "duration": duration_str,
        "duration_secs": duration_secs,
    }


async def notify_n8n(title: str, mp3_info: dict):
    """Send episode metadata to n8n for Telegram approval."""
    payload = {
        "title": title,
        "mp3_url": mp3_info["url"],
        "mp3_remote_path": mp3_info["remote_path"],
        "file_size": mp3_info["file_size"],
        "duration": mp3_info["duration"],
        "duration_secs": mp3_info["duration_secs"],
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        resp = await client.post(N8N_WEBHOOK_URL, json=payload)
        resp.raise_for_status()
    print("An n8n gesendet. Telegram-Approval laeuft im Hintergrund.")


def init_nlm_feed():
    """Create the NLM RSS feed on the server if it doesn't exist."""
    feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>NotebookLM Summaries</title>
    <link>{BASE_URL}</link>
    <description>Audio-Zusammenfassungen und Deep Dives aus Google NotebookLM. Automatisch generiert aus kuratierten YouTube-Quellen.</description>
    <language>de</language>
    <itunes:author>Tom Bieth</itunes:author>
    <itunes:category text="Technology" />
    <itunes:image href="{BASE_URL}/artwork/nlm-cover.png" />
    <itunes:explicit>false</itunes:explicit>

    <!-- NEUE EPISODEN HIER -->

  </channel>
</rss>"""

    result = subprocess.run(
        ["ssh", SERVER_HOST, f"test -f {FEED_FILE} && echo exists || echo missing"],
        capture_output=True, text=True,
    )

    if "missing" in result.stdout:
        subprocess.run(
            ["ssh", SERVER_HOST, f"cat > {FEED_FILE} << 'FEEDEOF'\n{feed_xml}\nFEEDEOF"],
            check=True,
        )
        print(f"NLM RSS-Feed erstellt: {FEED_FILE}")
    else:
        print(f"NLM RSS-Feed existiert bereits: {FEED_FILE}")


async def publish(notebook_id: str, title: str, output_dir: str = "."):
    """Full pipeline: download → convert → send to n8n for approval."""
    # 1. Ensure feed exists
    init_nlm_feed()

    # 2. Download audio
    safe_name = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"nlm_{safe_name}_{timestamp}"
    local_wav = str(Path(output_dir) / f"{filename}.wav")

    await download_audio(notebook_id, local_wav)

    # 3. Upload and convert to MP3
    mp3_info = upload_and_convert(local_wav, filename)

    # 4. Send to n8n for async Telegram approval
    await notify_n8n(title, mp3_info)

    # Cleanup local WAV
    Path(local_wav).unlink(missing_ok=True)

    print(f"\nFertig! Approval laeuft asynchron via n8n/Telegram.")


async def main():
    parser = argparse.ArgumentParser(description="NotebookLM Podcast Publishing Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    # publish
    pub_parser = subparsers.add_parser("publish", help="Audio herunterladen, konvertieren und mit Telegram-Approval veroeffentlichen")
    pub_parser.add_argument("--notebook-id", required=True, help="NotebookLM Notebook-ID")
    pub_parser.add_argument("--title", required=True, help="Episode-Titel")
    pub_parser.add_argument("--output-dir", default=".", help="Lokales Verzeichnis fuer temporaere Dateien")

    # init
    subparsers.add_parser("init", help="NLM RSS-Feed auf dem Server erstellen")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        init_nlm_feed()
    elif args.command == "publish":
        await publish(args.notebook_id, args.title, args.output_dir)


if __name__ == "__main__":
    asyncio.run(main())
