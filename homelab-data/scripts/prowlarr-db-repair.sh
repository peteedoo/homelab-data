#!/bin/bash
# scripts/prowlarr-db-repair.sh — Detect and repair a corrupted Prowlarr SQLite DB.
# Restores from the newest clean scheduled backup. Safe to run any time.
set -euo pipefail

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

PROWLARR_DIR="$HOME/homelab-data/arr/prowlarr"
DB="$PROWLARR_DIR/prowlarr.db"
BACKUP_DIR="$PROWLARR_DIR/Backups/scheduled"
LOG="$HOME/homelab-data/logs/prowlarr-db-repair.log"
LOCK="/tmp/prowlarr-db-repair.lock"
TS=$(date +%Y%m%d-%H%M%S)

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') | $*" | tee -a "$LOG"; }

cleanup_lock() { rm -f "$LOCK"; }

# --- telegram helper (same pattern as homelab-health-check.sh) ---
tg() {
  local token chat
  token=$(docker exec faulty-telegram-bot sh -c 'echo $TELEGRAM_BOT_TOKEN' 2>/dev/null || true)
  chat=$(docker exec faulty-telegram-bot sh -c 'echo $TELEGRAM_CHAT_ID' 2>/dev/null || true)
  if [ -z "$token" ] || [ -z "$chat" ]; then
    [ -f "$HOME/homelab-data/faulty-orchestrator/.env" ] && source "$HOME/homelab-data/faulty-orchestrator/.env" 2>/dev/null || true
    [ -f "$HOME/.hermes/.env" ] && source "$HOME/.hermes/.env" 2>/dev/null || true
    token="${TELEGRAM_BOT_TOKEN:-}"
    chat="${TELEGRAM_CHAT_ID:-}"
  fi
  [ -n "$token" ] && [ -n "$chat" ] || return 0
  curl -s -X POST "https://api.telegram.org/bot$token/sendMessage" \
    -d "chat_id=$chat" --data-urlencode "text=$1" >/dev/null 2>&1 || true
}

# --- sanity checks ---
if [ ! -f "$DB" ]; then
  log "ERROR: Prowlarr DB not found at $DB"; exit 1
fi
if [ ! -d "$BACKUP_DIR" ]; then
  log "ERROR: Prowlarr backup dir not found at $BACKUP_DIR"; exit 1
fi
if ! command -v sqlite3 >/dev/null 2>&1; then
  log "ERROR: sqlite3 not installed"; exit 1
fi
if ! docker ps >/dev/null 2>&1; then
  log "ERROR: docker not available"; exit 1
fi

# --- single instance ---
if [ -f "$LOCK" ]; then
  pid=$(cat "$LOCK" 2>/dev/null || echo 0)
  if kill -0 "$pid" 2>/dev/null; then
    log "INFO: another repair is already running (pid $pid)"; exit 0
  fi
  rm -f "$LOCK"
fi
echo $$ > "$LOCK"
trap cleanup_lock EXIT

# --- check integrity ---
log "INFO: checking integrity of $DB"
if sqlite3 "$DB" "PRAGMA integrity_check;" 2>/dev/null | grep -qx 'ok'; then
  log "INFO: DB integrity ok, no repair needed"
  exit 0
fi

log "WARN: Prowlarr DB is corrupted; beginning repair"
tg "⚠️ Prowlarr DB corruption detected; auto-repair started."

# --- find newest clean backup ---
CLEAN_BACKUP=""
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"; cleanup_lock' EXIT

for zip in $(ls -t "$BACKUP_DIR"/prowlarr_backup_*.zip 2>/dev/null); do
  [ -f "$zip" ] || continue
  rm -rf "$TMP_DIR"/*
  if unzip -q "$zip" -d "$TMP_DIR" 2>/dev/null && [ -f "$TMP_DIR/prowlarr.db" ]; then
    if sqlite3 "$TMP_DIR/prowlarr.db" "PRAGMA integrity_check;" 2>/dev/null | grep -qx 'ok'; then
      CLEAN_BACKUP="$zip"
      log "INFO: clean backup found: $CLEAN_BACKUP"
      break
    fi
  fi
done

if [ -z "$CLEAN_BACKUP" ]; then
  log "ERROR: no clean backup found in $BACKUP_DIR"
  tg "❌ Prowlarr DB is corrupt and no clean backup was found. Manual intervention required."
  exit 1
fi

# --- stop prowlarr ---
log "INFO: stopping prowlarr container"
docker stop prowlarr >/dev/null 2>&1 || true

# --- backup corrupt DB ---
log "INFO: backing up corrupt DB to prowlarr.db.corrupt.$TS"
cp "$DB" "$PROWLARR_DIR/prowlarr.db.corrupt.$TS"
[ -f "$DB-wal" ] && cp "$DB-wal" "$PROWLARR_DIR/prowlarr.db-wal.corrupt.$TS" 2>/dev/null || true
[ -f "$DB-shm" ] && cp "$DB-shm" "$PROWLARR_DIR/prowlarr.db-shm.corrupt.$TS" 2>/dev/null || true

# --- restore clean DB ---
log "INFO: restoring from $CLEAN_BACKUP"
cp "$TMP_DIR/prowlarr.db" "$DB"
rm -f "$DB-wal" "$DB-shm"

# --- start prowlarr ---
log "INFO: starting prowlarr container"
docker start prowlarr >/dev/null 2>&1 || true

# --- wait for healthy ---
log "INFO: waiting for prowlarr to become healthy"
status=""
for i in $(seq 1 60); do
  status=$(docker inspect --format='{{.State.Health.Status}}' prowlarr 2>/dev/null || echo "")
  if [ "$status" = "healthy" ]; then
    log "INFO: prowlarr is healthy"
    break
  fi
  sleep 2
done
if [ "$status" != "healthy" ]; then
  log "WARN: prowlarr did not report healthy within 2 minutes"
fi

# --- restart *arr apps to clear indexer backoff caches ---
for app in radarr sonarr lidarr; do
  if docker ps --format '{{.Names}}' | grep -qx "$app"; then
    log "INFO: restarting $app to clear indexer backoff cache"
    docker restart "$app" >/dev/null 2>&1 || true
  fi
done

log "INFO: repair complete (restored from $CLEAN_BACKUP)"
tg "✅ Prowlarr DB repaired using $(basename "$CLEAN_BACKUP"). radarr/sonarr/lidarr restarted."
exit 0
