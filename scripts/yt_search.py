#!/usr/bin/env python3
"""YouTube search via yt-dlp with structured output and views/subs ratio."""

import io
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

# Force UTF-8 output to handle emoji in video titles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def parse_args(argv):
    """Parse query, --count N, --months N, --json, --no-date-filter from argv."""
    args = argv[1:]
    count = 20
    months = 6
    output_json = False
    query_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            try:
                count = int(args[i + 1])
            except ValueError:
                print(f"Error: --count requires an integer, got '{args[i + 1]}'", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--months" and i + 1 < len(args):
            try:
                months = int(args[i + 1])
            except ValueError:
                print(f"Error: --months requires an integer, got '{args[i + 1]}'", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--no-date-filter":
            months = 0
            i += 1
        elif args[i] == "--json":
            output_json = True
            i += 1
        else:
            query_parts.append(args[i])
            i += 1
    query = " ".join(query_parts)
    if not query:
        print("Usage: yt_search.py <query> [--count N] [--months N] [--no-date-filter] [--json]", file=sys.stderr)
        print("Example: yt_search.py claude code tutorial --count 5 --months 3", file=sys.stderr)
        sys.exit(1)
    return query, count, months, output_json


def format_subscribers(n):
    """Format subscriber count as human-readable (e.g., 45.2K, 1.2M)."""
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_views(n):
    """Format view count with commas."""
    if n is None:
        return "N/A"
    return f"{n:,}"


def format_duration(info):
    """Extract human-readable duration from yt-dlp info."""
    if info.get("duration_string"):
        return info["duration_string"]
    dur = info.get("duration")
    if dur is None:
        return "N/A"
    dur = int(dur)
    hours, remainder = divmod(dur, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_date(raw):
    """Convert YYYYMMDD to human-readable date (e.g., Jan 10, 2026)."""
    if not raw or len(raw) != 8:
        return "N/A"
    try:
        dt = datetime.strptime(raw, "%Y%m%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def get_cutoff_date(months):
    """Get the cutoff date as YYYYMMDD string, N months ago from today."""
    if months <= 0:
        return None
    cutoff = datetime.now() - timedelta(days=months * 30)
    return cutoff.strftime("%Y%m%d")


def extract_video_data(info):
    """Extract structured video data from yt-dlp info dict."""
    video_id = info.get("id", "")
    views = info.get("view_count")
    subs = info.get("channel_follower_count")

    if subs and views and subs > 0:
        ratio = round(views / subs, 2)
    else:
        ratio = None

    return {
        "title": info.get("title", "Unknown Title"),
        "channel": info.get("channel", info.get("uploader", "Unknown")),
        "subscribers": subs,
        "views": views,
        "views_subs_ratio": ratio,
        "duration": format_duration(info),
        "date": format_date(info.get("upload_date", "")),
        "upload_date_raw": info.get("upload_date", ""),
        "url": f"https://youtube.com/watch?v={video_id}" if video_id else "N/A",
    }


def print_text_results(videos_data):
    """Print results as formatted text."""
    divider = "\u2500" * 60

    for i, v in enumerate(videos_data, 1):
        subs_str = format_subscribers(v["subscribers"])
        views_str = format_views(v["views"])
        ratio_str = f"{v['views_subs_ratio']:.2f}x" if v["views_subs_ratio"] else "N/A"
        meta = f"{v['channel']} ({subs_str} subs)  \u00b7  {views_str} views ({ratio_str})  \u00b7  {v['duration']}  \u00b7  {v['date']}"

        print(divider)
        print(f" {i:>2}. {v['title']}")
        print(f"     {meta}")
        print(f"     {v['url']}")

    print(divider)


def main():
    query, count, months, output_json = parse_args(sys.argv)

    if not shutil.which("yt-dlp"):
        print("Error: yt-dlp not found on PATH. Install with: uv pip install yt-dlp", file=sys.stderr)
        sys.exit(1)

    # Fetch extra results to account for date filtering
    fetch_count = count * 2 if months > 0 else count
    search_query = f"ytsearch{fetch_count}:{query}"
    cmd = [
        "yt-dlp",
        search_query,
        "--dump-json",
        "--no-download",
        "--no-warnings",
        "--quiet",
    ]

    date_label = f", last {months} months" if months > 0 else ""
    print(f"Searching YouTube for: \"{query}\" (top {count} results{date_label})...\n", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print("Error: Search timed out after 120 seconds.", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0 and not result.stdout.strip():
        print(f"Error: yt-dlp failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            videos.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not videos:
        print("No results found.", file=sys.stderr)
        sys.exit(0)

    # Apply date filter
    cutoff = get_cutoff_date(months)
    if cutoff:
        filtered = [v for v in videos if (v.get("upload_date") or "00000000") >= cutoff]
        skipped = len(videos) - len(filtered)
        videos = filtered
        if skipped > 0:
            print(f"(Filtered out {skipped} video(s) older than {months} months)\n", file=sys.stderr)

    if not videos:
        print(f"No results found within the last {months} months.", file=sys.stderr)
        sys.exit(0)

    # Limit to requested count
    videos = videos[:count]

    # Extract structured data
    videos_data = [extract_video_data(v) for v in videos]

    if output_json:
        print(json.dumps(videos_data, ensure_ascii=False, indent=2))
    else:
        print_text_results(videos_data)


if __name__ == "__main__":
    main()
