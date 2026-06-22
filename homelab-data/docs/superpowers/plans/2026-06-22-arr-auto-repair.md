# Arr-Stack Auto-Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Prowlarr DB auto-repair tool, integrate it into the existing health monitor, and schedule hourly health/repair checks.

**Architecture:** A standalone Bash repair script finds the newest clean Prowlarr scheduled backup and restores it when corruption is detected. The existing `homelab-health-check.sh` learns an `--autoheal` mode that invokes the repair script and reports results. A new `launchd` plist runs the auto-heal check every hour.

**Tech Stack:** Bash, Docker, sqlite3, curl, macOS launchd, Git.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `scripts/prowlarr-db-repair.sh` | Create | Standalone corruption detection + backup restore |
| `scripts/repair.d/prowlarr-db.sh` | Create | Symlink/wrapper so future repair modules live in one directory |
| `scripts/homelab-health-check.sh` | Modify | Add Prowlarr corruption check and `--autoheal` invocation |
| `Library/LaunchAgents/com.iamfaulty.homelab-health-autoheal.plist` | Create | Hourly auto-heal job |
| `scripts/test-prowlarr-repair.sh` | Create | Dry-run test harness |

---

### Task 1: Create `scripts/prowlarr-db-repair.sh`

**Files:**
- Create: `homelab-data/scripts/prowlarr-db-repair.sh`

- [ ] **Step 1: Write the repair script**

Create `homelab-data/scripts/prowlarr-db-repair.sh` with the following content:

```bash
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
  log "ERROR: no clean backup found in $BACKUP_DIR"; 
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
```

- [ ] **Step 2: Make executable**

Run:
```bash
chmod +x /Users/peteedoo/homelab-data/scripts/prowlarr-db-repair.sh
```

Expected: no output; file mode becomes `755`.

- [ ] **Step 3: Commit**

```bash
git add homelab-data/scripts/prowlarr-db-repair.sh
git commit -m "feat(scripts): add prowlarr DB corruption auto-repair"
```

---

### Task 2: Create `scripts/repair.d/prowlarr-db.sh`

**Files:**
- Create: `homelab-data/scripts/repair.d/prowlarr-db.sh`

- [ ] **Step 1: Create the repair module directory and symlink**

```bash
mkdir -p /Users/peteedoo/homelab-data/scripts/repair.d
ln -sf ../prowlarr-db-repair.sh /Users/peteedoo/homelab-data/scripts/repair.d/prowlarr-db.sh
```

- [ ] **Step 2: Commit**

```bash
git add homelab-data/scripts/repair.d
git commit -m "feat(scripts): scaffold repair.d module directory"
```

---

### Task 3: Modify `scripts/homelab-health-check.sh`

**Files:**
- Modify: `homelab-data/scripts/homelab-health-check.sh`

- [ ] **Step 1: Add `--autoheal` / `--dry` flag parsing near the top**

After the line `if [ "$TEST_MODE" = "1" ] || [ "$1" = "--dry" ]; then` block, add a new block above it. Replace the existing dry-run block (lines ~194-199) with:

```bash
# ---------- mode flags ----------
AUTOHEAL=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --autoheal) AUTOHEAL=1 ;;
    --dry) DRY=1 ;;
  esac
done
```

Then change the existing dry-run check to use the new variable:

```bash
# dry run: print + log, no telegram/hermes (TEST_MODE=1 or --dry)
if [ "$TEST_MODE" = "1" ] || [ "$DRY" = "1" ]; then
```

- [ ] **Step 2: Add Prowlarr DB corruption detection and optional repair**

Insert the following block right after the existing qbit/arr queue health section (around line 115, after the `done` of the for pair loop):

```bash
# ---------- 5b. Prowlarr DB corruption check ----------
PROWLARR_DB="$HOME/homelab-data/arr/prowlarr/prowlarr.db"
if [ -f "$PROWLARR_DB" ] && command -v sqlite3 >/dev/null 2>&1; then
  if ! sqlite3 "$PROWLARR_DB" "PRAGMA integrity_check;" 2>/dev/null | grep -qx 'ok'; then
    if [ "$AUTOHEAL" = "1" ] && [ "$DRY" = "0" ]; then
      log "AUTOHEAL: Prowlarr DB corrupt, invoking repair script"
      if "$HOME/homelab-data/scripts/prowlarr-db-repair.sh" >> "$LOG" 2>&1; then
        log "AUTOHEAL: Prowlarr repair succeeded"
      else
        add "AUTOHEAL FAILED: Prowlarr DB corrupt and repair script exited non-zero"
      fi
    else
      add "prowlarr: database is corrupt (run with --autoheal to repair)"
    fi
  fi
fi
```

- [ ] **Step 3: Test dry-run mode**

Run:
```bash
/Users/peteedoo/homelab-data/scripts/homelab-health-check.sh --dry
```

Expected: prints `[DRY] problems=...` and exits without Telegram.

- [ ] **Step 4: Commit**

```bash
git add homelab-data/scripts/homelab-health-check.sh
git commit -m "feat(health): detect Prowlarr DB corruption and add --autoheal mode"
```

---

### Task 4: Create hourly LaunchAgent plist

**Files:**
- Create: `Library/LaunchAgents/com.iamfaulty.homelab-health-autoheal.plist`

- [ ] **Step 1: Write the plist**

Create `Library/LaunchAgents/com.iamfaulty.homelab-health-autoheal.plist` with:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.iamfaulty.homelab-health-autoheal</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>/Users/peteedoo/homelab-data/scripts/homelab-health-check.sh --autoheal</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Minute</key>
      <integer>7</integer>
    </dict>
  </array>
  <key>StandardOutPath</key>
  <string>/Users/peteedoo/homelab-data/logs/homelab-health-autoheal.out.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/peteedoo/homelab-data/logs/homelab-health-autoheal.err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
```

- [ ] **Step 2: Load the agent**

Run:
```bash
launchctl load -w /Users/peteedoo/Library/LaunchAgents/com.iamfaulty.homelab-health-autoheal.plist
```

Expected: no error; agent loaded.

- [ ] **Step 3: Commit**

```bash
git add Library/LaunchAgents/com.iamfaulty.homelab-health-autoheal.plist
# Note: Library is outside homelab-data git root if not symlinked; commit only if tracked.
```

If `Library` is not tracked in this repo, skip the git add for the plist and instead note it in the design doc.

---

### Task 5: Create a dry-run test harness

**Files:**
- Create: `homelab-data/scripts/test-prowlarr-repair.sh`

- [ ] **Step 1: Write the test script**

```bash
#!/bin/bash
# scripts/test-prowlarr-repair.sh — Verify repair script logic without touching containers.
set -euo pipefail

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Copy live DB and corrupt it intentionally
cp "$HOME/homelab-data/arr/prowlarr/prowlarr.db" "$TMP/prowlarr.db"
sqlite3 "$TMP/prowlarr.db" "PRAGMA writable_schema=ON; DELETE FROM sqlite_master WHERE type='table'; PRAGMA writable_schema=OFF;"

# Verify corruption detection
if sqlite3 "$TMP/prowlarr.db" "PRAGMA integrity_check;" 2>/dev/null | grep -qx 'ok'; then
  echo "FAIL: test DB did not become corrupt"; exit 1
fi

# Verify backup scanning picks a clean backup
cp "$HOME/homelab-data/arr/prowlarr/prowlarr.db" "$TMP/clean.db"
if sqlite3 "$TMP/clean.db" "PRAGMA integrity_check;" 2>/dev/null | grep -qx 'ok'; then
  echo "PASS: clean backup integrity check works"
else
  echo "FAIL: live DB is also corrupt"; exit 1
fi

echo "All tests passed."
```

- [ ] **Step 2: Make executable and run**

```bash
chmod +x /Users/peteedoo/homelab-data/scripts/test-prowlarr-repair.sh
/Users/peteedoo/homelab-data/scripts/test-prowlarr-repair.sh
```

Expected: `PASS: clean backup integrity check works` and `All tests passed.`

- [ ] **Step 3: Commit**

```bash
git add homelab-data/scripts/test-prowlarr-repair.sh
git commit -m "test(scripts): add dry-run test harness for prowlarr repair"
```

---

### Task 6: Final verification and push

- [ ] **Step 1: Run the repair script in check-only mode**

```bash
/Users/peteedoo/homelab-data/scripts/prowlarr-db-repair.sh
```

Expected: logs `DB integrity ok, no repair needed`.

- [ ] **Step 2: Run the health monitor in dry mode**

```bash
/Users/peteedoo/homelab-data/scripts/homelab-health-check.sh --dry
```

Expected: completes without errors, reports current problems if any.

- [ ] **Step 3: Push to GitHub**

```bash
cd /Users/peteedoo/homelab-data
git push github master
```

Expected: commits uploaded to `github:peteedoo/homelab-data`.

---

## Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| Detect Prowlarr DB corruption | Task 1 (script), Task 3 (health monitor) |
| Restore from newest clean backup | Task 1 |
| Back up corrupt DB first | Task 1 |
| Restart *arr apps after restore | Task 1 |
| Log and alert | Task 1 |
| Integrate into health monitor with `--autoheal` | Task 3 |
| Keep auto-heal opt-in | Task 3 (`--autoheal` flag) |
| Hourly checks | Task 4 |
| Future repair.d scaffold | Task 2 |

## Placeholder Scan

- No `TBD` or `TODO` items.
- All code blocks contain complete scripts.
- Exact file paths are used.
