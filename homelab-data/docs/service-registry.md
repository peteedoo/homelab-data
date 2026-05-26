# Master Service Registry

**Maintained by:** Documentation & Access WG (Pidge)  
**Date:** 2026-05-06  
**Charter:** `~/homelab-data/docs/docs-wg-charter.md`

---

## Legend

- **Status:** `running` | `exited` | `stopped` | `not-started` | `down`
- **Health:** `healthy` | `none` | `unhealthy`
- **Credentials:** Location of auth secrets; `none` if no auth required
- **Network:** `bridge` | `host` | `service:gluetun` | `external`

---

## Running Services

| Name | Port | URL | Purpose | Status | Health | Credentials Location |
|------|------|-----|---------|--------|--------|---------------------|
| Stack Status | 3004 | http://localhost:3004 | Live service state dashboard | running | none | none |
| Homepage | 3005 | http://localhost:3005 | Application dashboard / startpage | running | healthy | none |
| Gitea | 3000 | http://localhost:3000 | Self-hosted Git | running | none | Gitea internal auth; admin account in 1Password |
| Jellyfin | 8096 | http://localhost:8096 | Media server | running | healthy | Jellyfin local user accounts |
| Jellyseerr | 5055 | http://localhost:5055 | Media request manager | running | none | Jellyseerr local auth |
| Lidarr | 8686 | http://localhost:8686 | Music acquisition manager | running | none | none (local network) |
| MeTube | 8081 | http://localhost:8081 | YouTube downloader | running | healthy | none |
| Mylar3 | 8090 | http://localhost:8090 | Comic book manager | running | none | none (local network) |
| Radarr | 7878 | http://localhost:7878 | Movie acquisition manager | running | none | none (local network) |
| Sonarr | 8989 | http://localhost:8989 | TV acquisition manager | running | none | none (local network) |
| Prowlarr | 9696 | http://localhost:9696 | Indexer manager | running | none | none (local network) |
| qBittorrent | 8080 | http://localhost:8080 | BitTorrent client | running | none | `admin` / `jBucrbchz` (change required) |
| slskd | 5030 | http://localhost:5030 | Soulseek client | running | healthy | `~/.hermes/secrets/soulseek.env` |
| Portainer | 9000 / 9443 | http://localhost:9000 | Container management | running | none | Portainer internal admin account |
| Planka | 3333 | http://localhost:3333 | Kanban board | running | healthy | `demo@demo.demo` / `demo` (change required) |
| Board (Planka dashboard) | 3335 | http://localhost:3335 | Planka metrics dashboard | running | none | `~/.hermes/.env` (PLANKA_URL env needed) |
| links-dashboard | 3334 | http://localhost:3334 | Stack links page | running | none | none |
| Soularr | 8265 | internal | Soulseek *arr bridge | running | none | none |
| stack-status | 3004 | http://localhost:3004 | Stack health dashboard | running | none | none |

---

## Exited / Down Services

| Name | Port | URL | Purpose | Status | Health | Notes |
|------|------|-----|---------|--------|--------|-------|
| dashboard (Planka metrics) | — | — | Planka metrics | **exited** | none | Missing `PLANKA_URL` env var — fix in compose |
| Agent Network | 8091 | http://localhost:8091 | Phone-friendly agent UI | not-started | none | Built but not running; `docker compose up -d --build` |
| DripDrip | 3001 | http://localhost:3001 | API service | not-started | none | Scaffolded, not built |
| Beszel | — | — | Monitoring sidecar | not-started | none | Exited (1) in prior check |
| NPM (nginx-proxy-manager) | — | — | Reverse proxy | not-started | none | Image present, no container |
| Watchtower | — | — | Auto-updates | not-started | none | Image present, no container |
| Agent Network (gateway) | — | — | Agent mesh gateway | not-started | none | Image present, no container |
| AnythingLLM | — | — | LLM interface | not-started | none | Image present, no container |
| Daily Brief | — | — | News digest | not-started | none | Image present, no container |
| Portfolio | — | — | Personal site | not-started | none | No image or container |
| Duplicati | — | — | Backups | not-started | none | Image present, no container |
| Gluetun | — | — | VPN tunnel | not-started | none | Image present, no container |
| Dozzle | — | — | Docker logs viewer | not-started | none | Image present, no container |

---

## Credentials Registry

| Service | Username | Password / Token Location | Notes |
|---------|----------|---------------------------|-------|
| qBittorrent | `admin` | `jBucrbchz` (hardcoded in config) | **Rotate immediately** — QA P0 flagged |
| slskd | `doodoogreen` | `~/.hermes/secrets/soulseek.env` | SLSKD_USERNAME / SLSKD_PASSWORD |
| Planka | `demo@demo.demo` | `demo` (hardcoded in compose) | **Rotate immediately** — QA P0 flagged |
| Board | — | `~/.hermes/.env` (needs PLANKA_URL) | Missing env var causes crash |
| Obsidian REST API | — | `~/.hermes/secrets/obsidian-api.key` | Port 27124; key `afa22cfbeedb9b6f6a8561f71514f50881ef538e2f8fde196d69fe5f52d62174` |
| 1Password Service Account | — | `~/.hermes/.env` (OP_SERVICE_ACCOUNT_TOKEN) | Used for `op read` CLI access |
| NAS (ILLMATIC) | `peteedoo` | `~/.hermes/.env` (NAS_HOST, NAS_USER) | Host: `192.168.68.69` — static reservation recommended |

---

## VPN Setup

**Method:** NordVPN macOS app + host networking for select containers  
**Status:** App installed; not currently routing container traffic (Gluetun stopped)

### How it works
- NordVPN app runs on the Mac mini host, encrypting all host traffic
- Containers with `network_mode: host` (qBittorrent, slskd) share the host network namespace and therefore route through the VPN automatically
- Other containers use Docker bridge networking and do **not** route through VPN unless explicitly configured

### Host-networking services
| Service | Port | Risk |
|---------|------|------|
| qBittorrent | 8080 | WebUI exposed on host interface; ensure firewall blocks WAN |
| slskd | 5030 | WebUI + Soulseek listen port exposed on host interface |

### Future hardening
- Start Gluetun container (`network_mode: service:gluetun`) to isolate VPN traffic per-container
- Move qBittorrent and slskd off `host` networking into Gluetun service network
- Document this migration in the registry when complete

---

## Known Issues & Cross-WG Tracker

| Issue | Severity | WG Responsible | Status |
|-------|----------|----------------|--------|
| Planka `SECRET_KEY` placeholder in compose | P0 | QA → Ops | Unchanged; needs rotation |
| Planka Postgres `POSTGRES_HOST_AUTH_METHOD=trust` | P0 | QA → Ops | Unchanged; remove trust |
| Board hardcoded `PLANKA_EMAIL` / `PLANKA_PASSWORD` | P0 | QA → Ops | Unchanged; move to `.env` |
| Port 3334 collision (board vs links-dashboard) | P1 | QA → Planning | **Resolved** — board moved to 3335 |
| qBittorrent + slskd on `host` network | P1 | QA → Ops | Pending Gluetun migration |
| Portainer mounts `/var/run/docker.sock` | P1 | QA → Ops | Acceptable if behind reverse proxy with auth |
| Homepage mounts `/var/run/docker.sock` | P1 | QA → Ops | Consider docker-socket-proxy |
| No health checks on any service | P1 | QA → Ops | Add healthcheck sections to all composes |
| All images use `:latest` | P1 | QA → Planning | Pin to semver or digest |
| Jellyfin mounts entire `~/Downloads` | P1 | QA → Ops | Narrow to media subdirs |
| `dashboard` container missing `PLANKA_URL` | P2 | Ops → Docs | **Documented**; fix in `apps/docker-compose.yml` |
| ILLMATIC NAS not mounted | Critical | Ops → Planning | Blocks all NAS-dependent services |

---

## Obsidian Service Notes

**API:** `https://127.0.0.1:27124`  
**Key:** `~/.hermes/secrets/obsidian-api.key`  
**Status:** API reachable (empty response on `/` is expected)

### Notes status
| Service | Note Exists | Action |
|---------|-------------|--------|
| Stack Status | Unknown | Verify via Obsidian API; create if missing |
| qBittorrent | Unknown | Verify via Obsidian API; create if missing |
| slskd | Unknown | Verify via Obsidian API; create if missing |
| Planka | Unknown | Verify via Obsidian API; create if missing |
| Gluetun/VPN | Unknown | Verify via Obsidian API; create if missing |
| Agent Network | Unknown | Verify via Obsidian API; create if missing |

*Obsidian note verification deferred to next pass — REST API returned empty response (normal for root path). Use `/search` or `/vault` endpoints to check existing notes.*

---

## Homepage & Dashboards

| Dashboard | URL | Status | Notes |
|-----------|-----|--------|-------|
| Homepage | http://localhost:3005 | running | Default config — needs service widgets configured |
| links-dashboard | http://localhost:3334 | running | Stack links page |
| Stack Status | http://localhost:3004 | running | Live container state |
| Board | http://localhost:3335 | running | Planka metrics |

### Homepage config
- Config dir: `~/homelab-data/homepage/config/`
- Currently only `settings.yaml` and `kubernetes.yaml` present
- **Action:** Add `services.yaml` and `widgets.yaml` to link to all running services

---

## Links Dashboard Status

| Service | links-dashboard URL | Correct? |
|---------|---------------------|----------|
| Stack Status | http://localhost:3004 | ✅ |
| Planka | http://localhost:3333 | ✅ |
| Board | http://localhost:3335 | ✅ |
| qBittorrent | http://localhost:8080 | ✅ |
| slskd | http://localhost:5030 | ✅ |

*All URLs verified against live container census. No corrections needed at this time.*

---

## Change Log

| Date | Change | WG |
|------|--------|-----|
| 2026-05-06 | Registry created | Documentation & Access |
| 2026-05-06 | Board port confirmed as 3335 (collision resolved) | Documentation & Access |
| 2026-05-06 | VPN setup documented | Documentation & Access |
| 2026-05-06 | P0/P1 issues cross-referenced from QA audit | Documentation & Access |

---

*Registry version 1.0 — maintained by Documentation & Access WG*
