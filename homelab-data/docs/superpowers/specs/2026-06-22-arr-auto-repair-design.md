# Arr-Stack Auto-Repair Design

**Date:** 2026-06-22  
**Author:** Kimi Code / Petee  
**Status:** Approved for implementation

## 1. Context

On 2026-06-22 qBittorrent appeared to stop downloading. Investigation showed qBit itself was healthy (connected, port-forwarded, seeding 279 torrents) but had zero active downloads. The root cause was **Prowlarr’s SQLite database was corrupted** (`database disk image is malformed`). Because all *arr apps proxy their indexers through Prowlarr, the corruption made every indexer unavailable, so Radarr/Lidarr/Sonarr could not grab new releases.

Manual fix: restore Prowlarr from the most recent clean scheduled backup, then restart the *arr apps to clear their indexer backoff caches.

## 2. Goals

- Detect Prowlarr DB corruption automatically.
- Restore from the newest clean scheduled backup without manual steps.
- Integrate the repair into the existing health monitor so it can auto-heal.
- Keep auto-heal **opt-in**; default behavior remains alert-only.
- Provide a scaffold for future arr-stack repair modules.

## 3. Components

### 3.1 `scripts/prowlarr-db-repair.sh`

A standalone, idempotent repair script.

Responsibilities:
- Locate the live Prowlarr DB at `~/homelab-data/arr/prowlarr/prowlarr.db`.
- Run `PRAGMA integrity_check`.
- If the DB is healthy, exit silently (or log `ok`).
- If corrupt:
  1. Stop the `prowlarr` container.
  2. Back up the corrupt DB with timestamp to `~/homelab-data/arr/prowlarr/prowlarr.db.corrupt.<timestamp>`.
  3. Scan `~/homelab-data/arr/prowlarr/Backups/scheduled/*.zip` from newest to oldest.
  4. For each backup, extract `prowlarr.db` to a temp directory and run `PRAGMA integrity_check`.
  5. Use the first clean backup found.
  6. Replace the live DB, delete stale `-wal`/`-shm` files, and start `prowlarr`.
  7. Wait for the container to report healthy.
  8. Restart `radarr`, `sonarr`, and `lidarr` to clear their indexer backoff caches.
  9. Log every step to `~/homelab-data/logs/prowlarr-db-repair.log`.
  10. If Telegram creds are available, send a concise alert.
- If no clean backup exists, alert and exit without modifying the live DB.

Safety:
- Never overwrite the corrupt DB until a replacement passes `PRAGMA integrity_check`.
- Abort if Docker/Prowlarr container is missing.
- Abort if the backup directory does not exist.

### 3.2 Health-monitor integration

Extend `~/homelab-data/scripts/homelab-health-check.sh`:
- Add a Prowlarr DB corruption check.
- Add an `--autoheal` flag / `AUTOHEAL=1` env var.
- When `AUTOHEAL=1` and corruption is detected:
  - Invoke `scripts/prowlarr-db-repair.sh`.
  - Re-check health after repair.
  - Include the repair result in the Telegram alert.
- Keep `--dry` mode so the monitor reports what it would heal without taking action.

### 3.3 Future toolkit scaffold

Create `~/homelab-data/scripts/repair.d/` as a drop-in directory for future modules. Each module is a standalone executable script that the health monitor can discover and call. For this iteration only `repair.d/prowlarr-db.sh` is implemented; other modules (e.g., qBit stalled-download cleanup, *arr queue re-sync) are documented as future work.

## 4. Data Flow

```
health monitor (cron every 1h, AUTOHEAL=1)
        │
        ▼
Detect Prowlarr DB corruption
        │
   ┌────┴────┐
   │         │
healthy   corrupt
   │         │
  exit   invoke repair script
            │
            ▼
      stop prowlarr
            │
            ▼
      find newest clean backup
            │
            ▼
      restore DB + start prowlarr
            │
            ▼
      restart radarr/sonarr/lidarr
            │
            ▼
      log + alert
```

## 5. Error Handling

- **No clean backup:** stop, alert, leave system as-is.
- **Docker not running:** script exits non-zero; health monitor reports it.
- **Restore succeeds but Prowlarr never becomes healthy:** script exits non-zero; health monitor escalates.
- **Telegram creds missing:** log only, do not fail.

## 6. Testing

- `TEST_MODE=1 ./scripts/prowlarr-db-repair.sh` tests on a temporary copy of the live DB without stopping containers.
- `./homelab-health-check.sh --dry` reports detected problems and would-be repairs.
- After deployment, simulate corruption on a copy of the DB in `/tmp` to verify backup selection logic.

## 7. Operational Notes

- The existing LaunchAgent `com.iamfaulty.homelab-health` runs every 30 minutes. A new hourly cron or a second LaunchAgent will be added for the auto-heal run so it does not conflict with the existing alert-only run.
- The user explicitly requested hourly “still on track” checks; the health/repair job satisfies this.

## 8. Future Work

- `repair.d/qbit-stalled.sh` — remove or force-start stalled downloads beyond a threshold.
- `repair.d/arr-indexer-sync.sh` — trigger RSS sync when *arr apps report long-term indexer failures.
- `repair.d/qbit-port-sync.sh` — verify qBit listening port matches gluetun forwarded port.
