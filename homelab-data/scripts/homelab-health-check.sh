#!/bin/bash
# homelab-health-check.sh — all-encompassing homelab watcher.
# Checks: container health, web endpoints, VPN tunnel, disk/NAS, qbit + *arr queue health.
# On anomaly: Telegram alert + Hermes diagnosis. Dedups so it won't spam the same issue.
# Scheduled via launchd: com.iamfaulty.homelab-health (every 30 min).

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"
LOG="$HOME/homelab-data/logs/homelab-health.log"
STATE="/tmp/homelab-health.laststate"
mkdir -p "$(dirname "$LOG")"

# --- tunables ---
DISK_CRIT_GB=5            # boot volume free space critical
QBIT_DEAD_MAX=12          # error+missingFiles torrents tolerated
QBIT_STALLED_MAX=25       # stalledDL torrents tolerated
ARR_QUEUE_MAX=80          # per-*arr queue size before "backing up"
ALERT_COOLDOWN_HRS=6      # re-alert same problem set at most this often
HERMES_TIMEOUT=180        # seconds for the diagnosis dispatch
HERMES_PROVIDER=""        # "" = hermes default (Kimi); or e.g. "openrouter-free"
# --- forecast ("brain") tunables ---
DISK_FORECAST_FLOOR_GB=2  # project when free disk will hit this
RAM_FORECAST_FLOOR=8      # project when free RAM % will hit this
FORECAST_HORIZON_DAYS=4   # only warn if breach predicted within this window
RESTART_LOOP_DELTA=3      # +this many restarts between runs = crash-loop
METRICS="$HOME/homelab-data/logs/metrics.csv"
RESTART_STATE="/tmp/homelab-health.restarts"

# --- telegram creds: the live bot container is source of truth (the .env on disk is stale) ---
TELEGRAM_BOT_TOKEN=$(docker exec faulty-telegram-bot sh -c 'echo $TELEGRAM_BOT_TOKEN' 2>/dev/null)
TELEGRAM_CHAT_ID=$(docker exec faulty-telegram-bot sh -c 'echo $TELEGRAM_CHAT_ID' 2>/dev/null)
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  [ -f "$HOME/homelab-data/faulty-orchestrator/.env" ] && source "$HOME/homelab-data/faulty-orchestrator/.env" 2>/dev/null
  [ -f "$HOME/.hermes/.env" ] && source "$HOME/.hermes/.env" 2>/dev/null
fi
RADARR_KEY="ff19e914566d4bfcb494d2e4ebcbba7c"
SONARR_KEY="af0c455b16ab43f9a3e5960f307cc417"
LIDARR_KEY="35e72899e39d4019b79548d66f28bd5e"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') | $*" >> "$LOG"; }
PROBLEMS=()
add() { PROBLEMS+=("$1"); log "PROBLEM: $1"; }
WARNINGS=()
warn() { WARNINGS+=("$1"); log "FORECAST: $1"; }

# ---------- mode flags ----------
AUTOHEAL=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --autoheal) AUTOHEAL=1 ;;
    --dry) DRY=1 ;;
  esac
done

# ---------- 1. containers: unhealthy / restarting / unexpectedly exited ----------
while IFS='|' read -r name status; do
  case "$status" in
    *unhealthy*)  add "container UNHEALTHY: $name ($status)";;
    *Restarting*) add "container RESTART-LOOP: $name ($status)";;
  esac
done < <(docker ps --format '{{.Names}}|{{.Status}}' 2>/dev/null)

# containers that crashed: were running under a restart policy but are now exited/dead.
# ("created" = never-started leftover, not a crash — ignore.)
while IFS='|' read -r name policy state; do
  case "$state" in exited|dead) ;; *) continue;; esac
  case "$policy" in
    always|unless-stopped|on-failure) add "container DOWN: $name (state=$state, policy=$policy)";;
  esac
done < <(docker ps -a --format '{{.Names}}' 2>/dev/null | while read -r n; do
           echo "$n|$(docker inspect "$n" --format '{{.HostConfig.RestartPolicy.Name}}|{{.State.Status}}' 2>/dev/null)"
         done)

# ---------- 2. web endpoints (000 = not serving) ----------
EP=(
  "qbittorrent|http://127.0.0.1:8085"  "radarr|http://127.0.0.1:7878"
  "sonarr|http://127.0.0.1:8989"       "lidarr|http://127.0.0.1:8686"
  "prowlarr|http://127.0.0.1:9696"     "readarr|http://127.0.0.1:8787"
  "mylar3|http://127.0.0.1:8090"       "jellyseerr|http://127.0.0.1:5055"
  "metube|http://127.0.0.1:8081"       "flaresolverr|http://127.0.0.1:8191"
  "bookbounty|http://127.0.0.1:5000"   "huntorr|http://127.0.0.1:5002"
  "slskd|http://127.0.0.1:5030"        "jellyfin|http://127.0.0.1:8096"
  "gitea|http://127.0.0.1:3000"        "portainer|http://127.0.0.1:9000"
  "portfolio|http://127.0.0.1:3001"    "homepage|http://127.0.0.1:3005"
  "dashboard|http://127.0.0.1:3004"    "anythingllm|http://127.0.0.1:3002"
  "daily-brief|http://127.0.0.1:3003"  "planka|http://127.0.0.1:3333"
  "board-dashboard|http://127.0.0.1:3334" "drip-api|http://127.0.0.1:3006"
  "drip-frontend|http://127.0.0.1:3007" "truth-site|http://127.0.0.1:3008"
  "dozzle|http://127.0.0.1:8888"       "duplicati|http://127.0.0.1:8200"
  "beszel|http://127.0.0.1:8089"
)
for e in "${EP[@]}"; do
  nm="${e%%|*}"; url="${e##*|}"
  code=$(curl -s -o /dev/null -m 5 -w "%{http_code}" "$url" 2>/dev/null)
  [ "$code" = "000" ] && add "endpoint DOWN: $nm ($url not responding)"
done
# Caddy edge (public path)
code=$(curl -s -o /dev/null -m 5 -w "%{http_code}" -H "Host: iamfaulty.com" http://127.0.0.1:80 2>/dev/null)
[ "$code" = "000" ] && add "edge DOWN: Caddy not serving on :80"

# ---------- 3. VPN tunnel ----------
vpn_ip=$(docker exec gluetun wget -qO- -T 8 https://ipinfo.io/ip 2>/dev/null)
if ! echo "$vpn_ip" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
  add "VPN DOWN: gluetun cannot reach internet (no public IP)"
fi

# ---------- 4. disk + NAS ----------
avail_gb=$(df -g / 2>/dev/null | awk 'NR==2{print $4}')
[ -n "$avail_gb" ] && [ "$avail_gb" -lt "$DISK_CRIT_GB" ] && add "DISK CRITICAL: only ${avail_gb}GB free on /"
mount | grep -q "on /Volumes/homelab " || add "NAS NOT MOUNTED: /Volumes/homelab missing"

# ---------- 5. qbit + *arr queue health ----------
qj=$(docker exec qbittorrent sh -c 'curl -s "http://localhost:8080/api/v2/torrents/info"' 2>/dev/null)
if [ -n "$qj" ]; then
  dead=$(echo "$qj" | tr '{' '\n' | grep -cE '"state":"(error|missingFiles)"')
  stalled=$(echo "$qj" | tr '{' '\n' | grep -cE '"state":"stalledDL"')
  [ "$dead" -gt "$QBIT_DEAD_MAX" ] && add "qbit: $dead error/missingFiles torrents (decluttarr may be stuck)"
  [ "$stalled" -gt "$QBIT_STALLED_MAX" ] && add "qbit: $stalled stalled downloads"
fi
for pair in "Radarr|7878|$RADARR_KEY|v3" "Sonarr|8989|$SONARR_KEY|v3" "Lidarr|8686|$LIDARR_KEY|v1"; do
  IFS='|' read -r nm port key api <<< "$pair"
  n=$(curl -s -m 8 "http://127.0.0.1:$port/api/$api/queue?pageSize=1" -H "X-Api-Key: $key" 2>/dev/null \
        | grep -oE '"totalRecords":[0-9]+' | head -1 | grep -oE '[0-9]+')
  [ -n "$n" ] && [ "$n" -gt "$ARR_QUEUE_MAX" ] && add "$nm queue backing up: $n items"
done

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

# ---------- 6. crash-loop detector + restart tally ----------
total_restarts=0
new_rstate=""
while IFS='|' read -r name rc; do
  [ -z "$name" ] && continue
  [ -z "$rc" ] && rc=0
  total_restarts=$((total_restarts + rc))
  new_rstate+="$name $rc"$'\n'
  prev=$(grep -E "^$name " "$RESTART_STATE" 2>/dev/null | awk '{print $2}')
  if [ -n "$prev" ] && [ "$rc" -ge $((prev + RESTART_LOOP_DELTA)) ]; then
    add "container CRASH-LOOP: $name +$((rc - prev)) restarts since last check (total $rc)"
  fi
done < <(docker ps -a --format '{{.Names}}' 2>/dev/null | while read -r n; do
           echo "$n|$(docker inspect "$n" --format '{{.RestartCount}}' 2>/dev/null)"
         done)
printf '%s' "$new_rstate" > "$RESTART_STATE"

# ---------- 7. metric history + forecast (the "brain") ----------
ram_free_pct=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{gsub(/[ %]/,"",$2); print $2}')
[ -f "$METRICS" ] || echo "epoch,disk_gb,ram_free_pct,restarts,qbit_dead,qbit_stalled" > "$METRICS"
echo "$(date +%s),${avail_gb:-0},${ram_free_pct:-0},${total_restarts:-0},${dead:-0},${stalled:-0}" >> "$METRICS"

FC=$(python3 - "$METRICS" "$DISK_FORECAST_FLOOR_GB" "$FORECAST_HORIZON_DAYS" "$RAM_FORECAST_FLOOR" <<'PY'
import sys, csv
path, floor_gb, horizon_d, ram_floor = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
rows = []
with open(path) as f:
    for r in csv.DictReader(f):
        try: rows.append((float(r['epoch']), float(r['disk_gb']), float(r['ram_free_pct'])))
        except Exception: pass
if not rows: sys.exit(0)
now = rows[-1][0]
win = [r for r in rows if now - r[0] <= 24*3600]   # trailing 24h
def lsq(pairs):                                    # least squares; x in days relative to now
    n = len(pairs)
    if n < 6: return None                          # need history to forecast
    xs = [(t - now)/86400.0 for t, _ in pairs]
    ys = [v for _, v in pairs]
    mx = sum(xs)/n; my = sum(ys)/n
    den = sum((x-mx)**2 for x in xs)
    if den == 0: return None
    m = sum((xs[i]-mx)*(ys[i]-my) for i in range(n))/den   # per day
    b = my - m*mx                                          # value at now
    return m, b
out = []
d = lsq([(t, dg) for t, dg, _ in win])
if d:
    m, b = d
    if m < -0.05:                                  # losing meaningful disk/day
        days = (b - floor_gb)/(-m)
        if 0 < days <= horizon_d:
            out.append(f"DISK filling: ~{b:.1f}GB free, losing {-m:.1f}GB/day -> hits {floor_gb:.0f}GB in ~{days:.1f} days")
rr = lsq([(t, rp) for t, _, rp in win])
if rr:
    m, b = rr
    if m < -0.5:
        days = (b - ram_floor)/(-m)
        if 0 < days <= horizon_d:
            out.append(f"RAM trending down: ~{b:.0f}% free, -{-m:.1f}%/day -> under {ram_floor:.0f}% in ~{days:.1f} days")
print("\n".join(out))
PY
)
while IFS= read -r line; do [ -n "$line" ] && warn "$line"; done <<< "$FC"

# ---------- verdict ----------
TOTAL=$(( ${#PROBLEMS[@]} + ${#WARNINGS[@]} ))
if [ "$TOTAL" -eq 0 ]; then
  log "OK | all checks passed"
  echo "" > "$STATE"
  exit 0
fi

P_TXT=""; [ ${#PROBLEMS[@]} -gt 0 ] && P_TXT=$(printf '• %s\n' "${PROBLEMS[@]}")
W_TXT=""; [ ${#WARNINGS[@]} -gt 0 ] && W_TXT=$(printf '• %s\n' "${WARNINGS[@]}")
log "SUMMARY | ${#PROBLEMS[@]} problem(s), ${#WARNINGS[@]} forecast(s)"

# dry run: print + log, no telegram/hermes (TEST_MODE=1 or --dry)
if [ "$TEST_MODE" = "1" ] || [ "$DRY" = "1" ]; then
  echo "[DRY] problems=${#PROBLEMS[@]} forecasts=${#WARNINGS[@]}"
  [ -n "$P_TXT" ] && { echo "NOW:"; echo "$P_TXT"; }
  [ -n "$W_TXT" ] && { echo "COMING:"; echo "$W_TXT"; }
  exit 1
fi

# dedup: same problem+forecast set within cooldown -> log only, no re-alert
sig=$(printf '%s\n' "${PROBLEMS[@]}" "${WARNINGS[@]}" | sort | md5 2>/dev/null || echo "$P_TXT$W_TXT" | md5)
now=$(date +%s)
if [ -f "$STATE" ]; then
  read -r last_sig last_ts < "$STATE" 2>/dev/null
  if [ "$sig" = "$last_sig" ] && [ $(( now - ${last_ts:-0} )) -lt $(( ALERT_COOLDOWN_HRS*3600 )) ]; then
    log "deduped | same set within ${ALERT_COOLDOWN_HRS}h, no re-alert"
    exit 0
  fi
fi
echo "$sig $now" > "$STATE"

tg() {
  [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ] || { log "telegram creds missing"; return; }
  curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
    -d "chat_id=$TELEGRAM_CHAT_ID" --data-urlencode "text=$1" >/dev/null 2>&1
}

MSG="🏠 Homelab health"
[ ${#PROBLEMS[@]} -gt 0 ] && MSG="$MSG — ${#PROBLEMS[@]} issue(s) now"
[ ${#WARNINGS[@]} -gt 0 ] && MSG="$MSG — ${#WARNINGS[@]} forecast(s)"
[ -n "$P_TXT" ] && MSG="$MSG"$'\n\n⚠️ NOW:\n'"$P_TXT"
[ -n "$W_TXT" ] && MSG="$MSG"$'\n🔮 COMING:\n'"$W_TXT"
tg "$MSG"

# ---------- Hermes diagnosis (only for active problems; forecasts are advisory) ----------
if [ ${#PROBLEMS[@]} -gt 0 ]; then
  PROMPT="You are diagnosing the iamfaulty homelab (Mac mini, OrbStack Docker, arr-stack behind gluetun VPN). The health monitor flagged these active problems:
$P_TXT
${W_TXT:+Trend forecasts (context):
$W_TXT}
Read ~/homelab-data/STACK.md first. Inspect the relevant containers/logs. Give a concise root-cause and the exact fix command(s) for each issue. Do not make changes — diagnose only."
  PROV=""; [ -n "$HERMES_PROVIDER" ] && PROV="--provider $HERMES_PROVIDER"
  DIAG=$(timeout "$HERMES_TIMEOUT" hermes -z "$PROMPT" $PROV --yolo 2>&1)
  [ -z "$DIAG" ] && DIAG="(Hermes returned nothing or timed out after ${HERMES_TIMEOUT}s)"
  log "HERMES DIAGNOSIS: $DIAG"
  tg "🔎 Hermes diagnosis:
$(echo "$DIAG" | tail -c 3500)"
fi

exit 1
