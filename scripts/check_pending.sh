#!/bin/bash
# Cronjob-Wrapper: Prueft ausstehende NLM-Generierungen und benachrichtigt via Telegram.
# Beendet sofort wenn keine pending_generations.json existiert oder leer ist.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PENDING_FILE="$PROJECT_DIR/pending_generations.json"
LOG_FILE="$PROJECT_DIR/check_pending.log"

# Nichts zu tun wenn keine Pending-Datei oder leer
if [ ! -f "$PENDING_FILE" ] || [ "$(cat "$PENDING_FILE" 2>/dev/null)" = "[]" ]; then
    exit 0
fi

cd "$PROJECT_DIR"
echo "$(date '+%Y-%m-%d %H:%M:%S') Pruefe ausstehende Generierungen..." >> "$LOG_FILE"
uv run python scripts/nlm_pipeline.py check-status --all >> "$LOG_FILE" 2>&1
