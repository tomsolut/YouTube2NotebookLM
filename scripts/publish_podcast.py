#!/usr/bin/env python3
"""Publish NotebookLM audio podcasts to RSS feed with Telegram approval."""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from email.utils import formatdate
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

# Server config
SERVER_HOST = "root@100.77.144.40"
PODCAST_DIR = "/var/www/podcast"
EPISODES_DIR = f"{PODCAST_DIR}/episodes"
FEED_FILE = f"{PODCAST_DIR}/nlm-feed.xml"
BASE_URL = "https://podcast.tomsolut.work"


def load_env():
    """Load .env file from project root."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print(f"FEHLER: {env_path} nicht gefunden.")
        print("Erstelle .env mit TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID")
        sys.exit(1)
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def telegram_token():
    return os.environ["TELEGRAM_BOT_TOKEN"]


def telegram_chat_id():
    return os.environ["TELEGRAM_CHAT_ID"]


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


async def send_telegram_approval(title: str, mp3_info: dict) -> bool:
    """Send Telegram message with inline approve/reject buttons. Wait for response."""
    token = telegram_token()
    chat_id = telegram_chat_id()
    api = f"https://api.telegram.org/bot{token}"

    message = (
        f"🎙 <b>Neuer NotebookLM-Podcast</b>\n\n"
        f"<b>{title}</b>\n"
        f"Dauer: {mp3_info['duration']}\n"
        f"URL: {mp3_info['url']}\n\n"
        f"In RSS-Feed veröffentlichen?"
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Veröffentlichen", "callback_data": "approve"},
            {"text": "❌ Ablehnen", "callback_data": "reject"},
        ]]
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        # Send message with buttons
        resp = await client.post(f"{api}/sendMessage", json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
        })
        resp.raise_for_status()
        msg_data = resp.json()
        message_id = msg_data["result"]["message_id"]

        print("Telegram-Nachricht gesendet. Warte auf Antwort...")

        # Poll for callback
        last_update_id = 0
        timeout = 3600  # 1 hour
        start = time.time()

        while time.time() - start < timeout:
            resp = await client.get(f"{api}/getUpdates", params={
                "offset": last_update_id + 1,
                "timeout": 30,
                "allowed_updates": json.dumps(["callback_query"]),
            })
            resp.raise_for_status()
            updates = resp.json().get("result", [])

            for update in updates:
                last_update_id = update["update_id"]
                cb = update.get("callback_query")
                if cb and cb["message"]["message_id"] == message_id:
                    approved = cb["data"] == "approve"
                    # Answer callback
                    await client.post(f"{api}/answerCallbackQuery", json={
                        "callback_query_id": cb["id"],
                        "text": "Veröffentlicht!" if approved else "Abgelehnt.",
                    })
                    # Update message
                    status = "✅ Veröffentlicht" if approved else "❌ Abgelehnt"
                    await client.post(f"{api}/editMessageText", json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": f"{message}\n\n<b>Status: {status}</b>",
                        "parse_mode": "HTML",
                    })
                    return approved

        print("Timeout: Keine Antwort innerhalb 1 Stunde.")
        return False


def update_rss_feed(title: str, mp3_info: dict, episode_num: int | None = None):
    """Add episode to the NLM RSS feed on the server."""
    import tempfile

    now = formatdate(timeval=time.time(), localtime=False, usegmt=True)
    safe_title = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    guid = f"nlm_{safe_title}_{int(time.time())}"

    # Download feed
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
        tmp_path = tmp.name
    subprocess.run(["scp", f"{SERVER_HOST}:{FEED_FILE}", tmp_path], check=True)
    feed_content = Path(tmp_path).read_text()

    if episode_num is None:
        episode_num = feed_content.count("<item>") + 1

    new_item = (
        f"    <item>\n"
        f"      <title>{title}</title>\n"
        f"      <description>NotebookLM Audio Summary</description>\n"
        f"      <enclosure url=\"{mp3_info['url']}\"\n"
        f"        length=\"{mp3_info['file_size']}\" type=\"audio/mpeg\" />\n"
        f"      <pubDate>{now}</pubDate>\n"
        f"      <itunes:duration>{mp3_info['duration']}</itunes:duration>\n"
        f"      <itunes:episode>{episode_num}</itunes:episode>\n"
        f"      <guid isPermaLink=\"false\">{guid}</guid>\n"
        f"    </item>\n"
    )

    # Insert after marker
    marker = "<!-- NEUE EPISODEN HIER -->"
    feed_content = feed_content.replace(marker, f"{marker}\n{new_item}")
    Path(tmp_path).write_text(feed_content)

    # Upload back
    subprocess.run(["scp", tmp_path, f"{SERVER_HOST}:{FEED_FILE}"], check=True)
    Path(tmp_path).unlink()

    print(f"RSS-Feed aktualisiert: Episode {episode_num} - {title}")


def cleanup_episode(mp3_info: dict):
    """Remove rejected episode from server."""
    subprocess.run(
        ["ssh", SERVER_HOST, f"rm -f {mp3_info['remote_path']}"],
        check=True,
    )
    print(f"Aufgeräumt: {mp3_info['remote_path']}")


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
    <itunes:image href="{BASE_URL}/artwork/nlm-cover.jpg" />
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
    """Full pipeline: download → convert → telegram → approve → publish."""
    load_env()

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

    # 4. Send Telegram approval
    approved = await send_telegram_approval(title, mp3_info)

    if approved:
        # 5. Update RSS feed
        update_rss_feed(title, mp3_info)
        print(f"\nVeröffentlicht! Feed: {BASE_URL}/nlm-feed.xml")
    else:
        # 6. Cleanup
        cleanup_episode(mp3_info)
        print("\nAbgelehnt. Dateien aufgeräumt.")

    # Cleanup local WAV
    Path(local_wav).unlink(missing_ok=True)

    return approved


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
        load_env()
        init_nlm_feed()
    elif args.command == "publish":
        await publish(args.notebook_id, args.title, args.output_dir)


if __name__ == "__main__":
    asyncio.run(main())
