# STACK.md — Homelab Single Source of Truth

> **Prime directive for every agent (Claude, Cowork, Codex, Hermes, OpenClaw, subagents):**
> This file is authoritative for the iamfaulty homelab. **If any other doc, skill, memory, or registry contradicts it, this file wins** — and you must *flag the stale source to Petee* rather than silently following it. Do not re-derive facts that are stated here. Do not trust a service map you find elsewhere without checking it against this file.

**Last verified live:** 2026-06-02 (service map below pulled directly from `docker inspect` on the mini).
**Re-verify command (run before trusting an old copy of this file):**
```bash
docker ps -q | xargs docker inspect \
  --format '{{.Name}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.project.config_files"}}'
docker ps --format '{{.Names}}\t{{.Ports}}'
```

---

## 1. Host & access facts (don't re-derive)

- **Host:** Mac mini M4. Live hostname `Ryans-Mac-mini.local`, user `peteedoo`. Target identity `iamfaulty-mini` / `peteemini` — treat `peteedoo` ≡ `peteemini`.
- **Docker runtime:** OrbStack is the active runtime (Docker Desktop also installed but OrbStack is in use). 39 containers running.
- **NAS:** UGREEN `ILLMATIC`, `192.168.68.69`. Share `homelab` → `/Volumes/homelab`. Media at `/Volumes/homelab/media`. **Confirm it's mounted before touching `/Volumes/homelab/...`** — it is NOT always mounted.
- **LAN:** `192.168.68.0/24`. TP-Link router at `.1`.
- **Cloudflare tunnel UUID:** `3727ea81-b7a2-484c-8de9-3e55ab1a050c`. Config `~/.cloudflared/config.yml`. One launchd-managed connector expected (`~/Library/LaunchAgents/com.iamfaulty.cloudflared.plist`).
- **Gitea login is case-sensitive:** `Peteedoo` works, `peteedoo` doesn't.
- **Domain:** `iamfaulty.com`.

## 2. Edge / reverse proxy — **Caddy, not NPM**

- **Caddy is the sole reverse proxy.** NPM (Nginx Proxy Manager) is **decommissioned** — no NPM container runs. Any doc that says "NPM → cloudflared" or "inside the NPM container" is **stale**.
- Flow: **Internet → Cloudflare (TLS) → Cloudflare Tunnel → `127.0.0.1:80` (Caddy) → services.**
- Caddy compose: `~/homelab-agent-stack/docker-compose.yml`; routes: `~/homelab-agent-stack/caddy/Caddyfile` (~20 `iamfaulty.com` subdomains; this file is the authoritative route list).
- Caddy publishes only `127.0.0.1:80` to the host (TLS terminates at Cloudflare). See discrepancy note in §7 re: the "Caddy HTTPS via Cloudflare DNS challenge" change.

## 3. Compose locations — **three real roots**

Forget the old "three named stacks" model (`homelab-agent-stack` / `homelab-data` / `iamfaulty-homelab`). The `~/iamfaulty-homelab/` directory is **defunct** — its services (gitea, jellyfin, portainer, duplicati) now run as individual composes on the NAS. The real roots, per live container labels:

| Root | Path | What lives here |
|---|---|---|
| **NAS composes** | `/Volumes/homelab/compose/<service>/docker-compose.yml` | anythingllm, beszel, board (planka), daily-brief, dashboard, dozzle, drip-frontend, dripdrip, duplicati, gitea, homepage, jellyfin, portainer, watchtower |  *(portfolio moved local — see §7 #6)*
| **Local composes** | `~/homelab-data/<project>/docker-compose.yml` | arr-stack, faulty-orchestrator, pi3-dns-vpn (blocky), truth-site, **filebrowser** (mounts NAS `/volume3/homelab/shared` via a Docker **NFS volume** — `nfsvers=3,nolock,soft` + `nocopy` — NOT a macOS bind mount, so it dodges the §7.6 OrbStack mount fragility and is restart-safe. NAS `/shared` chowned `1000:10` to match NFS `root_squash` anonuid) |
| **Control plane** | `~/homelab-agent-stack/docker-compose.yml` | caddy, sync-server |

**Binding rule:** HTTP services bind to `127.0.0.1` only; external reach is cloudflared → Caddy. The only intentional `0.0.0.0` exposure is **qBittorrent P2P `6881/tcp+udp`**.
**Stateful containers (SQLite/chown-sensitive: jellyfin, arr apps) run off the local SSD, never SMB/AFP.**

## 4. Live service map (verified 2026-06-02)

Bind address is `127.0.0.1` unless noted. Format: `service — host port → container`.

**Control plane / edge**
- `caddy` — 127.0.0.1:80 (edge) · `sync-server` — 127.0.0.1:13001→3001

**Public (via cloudflared + Caddy)**
- `portfolio` — 3001→80 · `iamfaulty.com`
- `petee-site` — 3009→80 · `petee.me` + `www.petee.me` (personal hub, links to iamfaulty.com; nginx:alpine, compose `~/homelab-data/petee-site/`, html `~/homelab-data/petee-site/html/`, added 2026-06-10). **DNS gotcha:** `petee.me` is a *separate zone* from `iamfaulty.com` but in the **same CF account** (`6a36b4c577fe89a5dbc709ec6ad492f5`). The cloudflared `cert.pem` is scoped to the `iamfaulty.com` zone only, so `cloudflared tunnel route dns ... petee.me` mis-creates `petee.me.iamfaulty.com` — DON'T use it for petee.me. The apex `petee.me` CNAME → `<tunnel-uuid>.cfargotunnel.com` (proxied) was created via the CF API instead (zone `4c253d4eb3769662134a873879d29f02`).
- `gitea` — 3000, SSH 2222→22 · `gitea.iamfaulty.com`
- `jellyfin` — 8096 · `jellyfin.iamfaulty.com` + `login.iamfaulty.com` (vanity alias, same Jellyfin, direct tunnel→8096)
- `filebrowser` — 127.0.0.1:8334→80 · `files.iamfaulty.com` (branded file portal for sharing NAS `/shared`)
- `dashboard` (OpenClaw HQ) — 3004 · `home.iamfaulty.com`

**Apps / infra (LAN / localhost)**
- `portainer` — 9000, 9443 · `duplicati` — 8200 · `dozzle` — 8888 · `homepage` — 3005
- `anythingllm` — 3002→3001 · `daily-brief` — 3003→5000 · `truth-site` — 3008→80
- `planka` — 3333→1337 · `planka-db` (internal 5432) · `board-dashboard` — 3334→8000
- `drip-api` — 3006→3001 · `drip-frontend` — 3007→80
- `beszel` — 8089→8090 · `beszel-agent` — 45876
- `faulty-orchestrator` — 8889 · `faulty-discord-bot` (no port) · `faulty-telegram-bot` (no port)
- `blocky` (DNS) — runs from `~/homelab-data/pi3-dns-vpn/`, no published host port · `watchtower` — auto-updates

**Arr stack** (`~/homelab-data/arr-stack/`, all mount `/Volumes/homelab/media:/data`)
- `qbittorrent` — 8085→8080 WebUI + **0.0.0.0:6881 P2P** · `prowlarr` — 9696 · `sonarr` — 8989 · `radarr` — 7878 · `lidarr` — 8686 · `readarr` — 8787 · `mylar3` — 8090
- `jellyseerr` — 5055 · `metube` — 8081 · `flaresolverr` — 8191 · `bookbounty` — 5000 · `huntorr` — 5002 · `slskd` (no published port; WebUI via gluetun `127.0.0.1:5030`) · `soularr` (internal 8265)
- `decluttarr` — no port; queue janitor in gluetun namespace, talks to radarr/sonarr/lidarr/qbit via localhost. Config: `~/homelab-data/arr-stack/decluttarr/config.yaml`. Sweeps every 5 min: removes+blocklists+re-searches stalled (3 strikes), stuck-metadata, missing-files, failed downloads/imports. `remove_orphans` skipped (no media mount).

**Home Assistant (AV universal remote)**
- `homeassistant` — `~/homelab-data/homeassistant/docker-compose.yml`, image `ghcr.io/home-assistant/home-assistant:stable`, **published `8123:8123` (LAN-accessible on purpose — it's the remote; HA has own auth, deviates from localhost-bind policy)**. Reach at `http://192.168.68.84:8123`. Purpose: universal remote for the AV system via `denonavr` (AVR-3310CI + AVR-X1000, IP/telnet:23), `androidtv_remote` (TCL Google TV), `apple_tv`. **Add AV devices by MANUAL IP** — OrbStack NAT blocks mDNS discovery. CAVEAT: Google-TV/Apple-TV integrations may need HA moved to the Pi 5 (native LAN) if OrbStack NAT trips their bidirectional protocols; Denon control works fine in OrbStack (outbound telnet). AV gear not yet wired to the LAN as of 2026-06-09. See [[project_av_home_theater_build]].

**Monitoring / auto-heal layer**
- **Decluttarr** = silent healing of the download queue (above).
- **Health monitor** — `~/homelab-data/scripts/homelab-health-check.sh`, launchd `com.iamfaulty.homelab-health` every 30 min. Checks ALL containers (unhealthy/crashed), web endpoints, gluetun VPN, disk/NAS, qbit + *arr queue health. On anomaly: Telegram alert + dispatches `hermes -z` for a root-cause diagnosis. Dedups (6h cooldown). Log: `~/homelab-data/logs/homelab-health.log`. `--dry`/`TEST_MODE=1` = detect-only. **Telegram creds: pulled live from the `faulty-telegram-bot` container env (the `.env` files on disk are stale — see §5 drift).** **Predictive "brain" (built):** logs `~/homelab-data/logs/metrics.csv` each run; least-squares forecast of disk-fill / RAM-exhaustion ETA (warns if breach <4 days out, needs ~6 points/24h to warm up); crash-loop detector (RestartCount +3 between runs, state `/tmp/homelab-health.restarts`). Alerts split ⚠️NOW (active → Hermes) from 🔮COMING (forecast → advisory only).
- **Ops stack** — compose root `~/homelab-data/ops/docker-compose.yml` (SSD-backed, monitoring/network tooling).
  - `uptime-kuma` — `127.0.0.1:3011→3001`, visual status board + history + alerts (needs first-run admin account).
  - `speedtest-tracker` — `127.0.0.1:3012→80`, LSIO, sqlite, tests every 6h, graphs up/down/latency.
  - **Download quarantine scanner** — `~/homelab-data/scripts/dmg-quarantine-scan.sh`, launchd `com.iamfaulty.quarantine-scan` every 10 min. Hashes new `.dmg/.pkg/.exe/.msi` in `~/Downloads` + `/Volumes/homelab/media/downloads/complete`, checks VirusTotal (key in Keychain service `virustotal-api`), Telegrams verdict (🚨 malicious / ⚠️ unknown / silent if clean), moves malicious `~/Downloads` files to `~/quarantine`. Telegram creds from the bot container. **Active** (VT key in Keychain, 500 lookups/day).
- **Backlog hunter** — `~/homelab-data/scripts/arr-missing-search.sh`, launchd `com.iamfaulty.arr-search` every 3h. Rate-limited: searches a BATCH=5 page of *arr missing items per app per run, cycling a page cursor (`logs/arr-search.cursor`), skips an app whose queue ≥40. Prevents the "nothing downloading" recurrence WITHOUT hammering indexers (8 were auto-disabled from overload). NOTE: `huntorr` (thewicklowwolf, port 5002) is only a **manual torrent-search GUI** — NOT an auto-hunter; the real Huntarr is archived upstream, hence the homegrown script.
- **Scanner toolbox = host-based** (NOT a container — NAT'd containers can't see the LAN): `nmap` + `nuclei` via Homebrew, driven by `~/homelab-data/scripts/netscan.sh` (`discover` / `ports` [diffs + Telegram on new host/port] / `vuln`). Logs: `~/homelab-data/logs/netscan/`.
  - `netalertx` — `127.0.0.1:20211`, LAN device discovery (degraded nmap-mode on the mini, not ARP — OrbStack NAT). **Volumes must mount `/data/config` + `/data/db`** (NOT `/app/config` — config lives at `/data`). `SCAN_SUBNETS=['192.168.68.0/24 --interface=eth0']` set in `~/homelab-data/ops/netalertx/config/app.conf`.
  - **Uptime Kuma — 32 monitors / 6 groups loaded** (2026-06-08) via `~/homelab-data/scripts/kuma-bulk-load.sh`. Uses the `uptime-kuma-api` lib in venv `~/.venvs/kuma` (Homebrew python can't see `pip --user`). The `uk1_` API key is **metrics-only**; creation needs ADMIN user/pass: `KUMA_USER=peteedoo KUMA_PASS=.. kuma-bulk-load.sh`. `accepted_statuscodes` must be hundred-ranges (`"200-299"`), not `"200-499"`. Re-runs are idempotent (skips existing by name).
  - Planned: Kali web desktop (deferred, disk).
- **Homepage front-door (rebuilt 2026-06-08)** — `localhost:3005`. **Config relocated NAS→SSD**: compose now `~/homelab-data/homepage/docker-compose.yml`, config `~/homelab-data/homepage/config/` (the old NAS mount `/Volumes/homelab/compose/homepage/config` gave the container EACCES → blank dashboard; that NAS compose is superseded, retire it). Runs as **PUID/PGID 0** so it can reach the docker socket for live status dots (socket is root:root inside the container). 23 tiles/5 groups, resources widget, Uptime Kuma iframe. Predictive early-warning pass in the health monitor = **built** (see above).
- **Caddy ↔ tunnel reconciled 2026-06-08.** Routes ADDED: `home`→3004 (OpenClaw HQ), `gitea.iamfaulty.com`→3000, `request.iamfaulty.com`→5055 (jellyseerr). Apex `iamfaulty.com`/`www`→3001 already had an `@root` block (NOTE: it's the bare-domain matcher — easy to miss; do NOT add a second `@root` or Caddy crash-loops on "matcher defined more than once"). Edit Caddyfile → `docker restart caddy` (single-file mount). **Flags:** apex `iamfaulty.com` serves the portfolio landing page (200) — the earlier 403 (portfolio running off the broken NAS html mount) was re-fixed 2026-06-09, see §7 #6; `plex.iamfaulty.com`→:32400 is DEAD (no Plex container; remove from tunnel); `openclaw`→intentional 404; `overseerr`→5055 and `brief`→8010 work direct (bypass Caddy).

## 5. Secrets policy — **macOS Keychain, no new flat files**

- Secrets live in the **macOS Keychain**. `gen-env.sh` regenerates `.env` files from the Keychain. Cloudflare, Spotify, Soulseek, qBittorrent WebUI creds are already migrated.
- `.env` files reference `${VAR}` from compose, are gitignored, and are `chmod 600`.
- **Never create new plaintext credential files.** No keys in compose, on disk, or in stdout.
- NEXO agents may also use `nexo_credential_*`; Keychain is the system-of-record either way.

## 6. Network architecture

```
        Internet ──(TLS)── Cloudflare ── Cloudflare Tunnel ── 127.0.0.1:80 (Caddy) ── services
                                 │
                          Tailscale mesh (100.x.x.x)  ── least-privilege ACL (per-port)
                                 │
        macOS app firewall: ENABLED + stealth mode
```
Tailscale mesh members include the mini, a Le Potato board, and Pi 5 (Ollama). See §7 for the unresolved Blocky-DNS location question. macOS firewall verified ON.

## 7. Open discrepancies — **needs live reconciliation (do not guess; flag)**

1. **Arr-stack VPN — DONE 2026-06-03. All egress via ProtonVPN WireGuard.** Per policy [[vpn-everything]]. The full arr stack runs behind one **gluetun (ProtonVPN WireGuard, killswitch on, NAT-PMP port-forwarding active)**. Verified: qBittorrent + arr apps exit at the Proton IP, not the ISP. **The VPN topology IS now the default `~/homelab-data/arr-stack/docker-compose.yml`** (direct-egress preserved as `docker-compose.direct.yml` for rollback) — so a plain `docker compose up` can't silently revert it. All 13 download/indexer services share gluetun's namespace; inter-app links rewritten to `localhost` (qBit `LocalHostAuth=false` → localhost bypasses auth). `jellyseerr` excepted (public Caddy route). History: NordVPN **OpenVPN** was abandoned (TLS wouldn't pass through OrbStack — MTU wall); WireGuard fixed it. **qBit listening port auto-syncs** to the NAT-PMP forwarded port (which changes on reconnect) via the `qbit-port-sync` sidecar (runs in gluetun's namespace, reads control server `:8000`, sets qBit `:8080` — verified self-healing). Files in `~/homelab-data/arr-stack/`: `docker-compose.yml` (VPN, live), `docker-compose.direct.yml` (rollback), `build-gluetun-compose.sh`, `reconfig-localhost.sh`, `import-proton-wg.sh`, `qbit-port-sync.sh`, `CUTOVER-vpn.md`. Proton WG key in Keychain (`homelab-protonvpn`). NB: blocky (DNS) and Meshtastic (LoRa) do NOT protect torrent traffic.
2. **Blocky DNS location.** A `blocky` container runs on the mini (`network_mode: host`) from `~/homelab-data/pi3-dns-vpn/` — but that's a **Pi-provisioning project** (`flash-armbian.sh`, `user-data`), so the mini instance is likely a test leftover; the intended target is a Pi. The compose defines blocky only — the "vpn" in the project name (a planned WireGuard box) is **not built**. The 2026-05-30 security doc says Blocky runs on the Le Potato (`192.168.68.82`). Determine which is authoritative.
3. **Caddy HTTPS.** SECURITY_FIXES_2026-05-29 says Caddy was upgraded to HTTPS via Cloudflare DNS challenge, but live Caddy only publishes `127.0.0.1:80`. Confirm whether the HTTPS build was applied or TLS is intentionally Cloudflare-only.
4. **`port-map.json` is stale.** `~/homelab-data/dropbox/agent-registry/port-map.json` (read by Hermes' stack-manager skill) lists 25 services incl. dead `npm`, and is missing ~15 running containers. **This file wins → it does not.** Regenerate it from §4 before relying on it.
5. **Tailscale IPs** (Le Potato `100.101.175.27`, Pi 5 `100.84.3.40`) are from the 2026-05-30 doc, not re-verified here.
6. **Apex `iamfaulty.com` serves the portfolio (re-fixed 2026-06-09; originally 2026-06-03).** Was routed to OpenClaw (`:18800`) via Caddy `@root`; repointed to `portfolio:3001` (apex + `www`). **NAS bind mounts are broken at the OrbStack level:** restarting/recreating ANY container whose source is under `/Volumes/homelab` fails with `mkdir /Volumes/homelab: permission denied` (macOS automounter layers SMB over the NFS mount; OrbStack can't establish a *fresh* mount — running containers survive because their mounts predate this). On 2026-06-09 the live `portfolio` had drifted back onto the broken NAS html mount (that was the apex 403); re-fixed by repointing it local, then **consolidated 2026-06-09**. **Live now (single source of truth):** container `portfolio` runs from the canonical LOCAL compose `~/homelab-data/portfolio/docker-compose.yml`, bind-mounting `~/homelab-data/portfolio/html/` — restart-safe (verified survives `docker restart`). The drift-causing NAS compose was renamed `/Volumes/homelab/compose/portfolio/docker-compose.yml.disabled-20260609`, and the temp staging dir `~/homelab-data/portfolio-html/` removed. Site content (landing page + `resume.pdf` + `cover-letter.pdf` + `drip/`) source: `~/ops/career/site/`. **OrbStack mount gotcha:** the Caddyfile bind mount (`~/homelab-agent-stack/caddy/Caddyfile → /etc/caddy/Caddyfile`) goes stale — the container can't see edits and `caddy reload`/`docker cp` fail ("no such file" / "device busy"). To apply Caddyfile edits you must **recreate** the caddy container (`cd ~/homelab-agent-stack && docker compose up -d --force-recreate caddy`), not reload. Validate first via `docker cp Caddyfile caddy:/tmp/x && docker exec caddy caddy validate --config /tmp/x --adapter caddyfile`. Note: the Caddy **catch-all** `handle { }` for unmatched hosts → **`respond 404`** (was OpenClaw `:18800`). **OpenClaw decommissioned 2026-06-04:** gateway launchd agent `ai.openclaw.gateway` booted out + plist `.disabled`, `ai.openclaw.mac.plist` `.disabled`, `:18800` dead, and both the `@openclaw` subdomain route and the catch-all now return 404. The disk-space cron monitor that lived in `~/.openclaw/workspace/` was relocated to `~/Scripts/disk-monitor.sh` (cron repointed). OpenClaw data dirs (`~/.openclaw`, `~/.openclab`, `~/.openclay`, `~/openclaw-backups`, `~/openclaw-rescue-*`) left on disk.

## 8. Index — canonical doc per topic

| Topic | Canonical doc |
|---|---|
| **Live stack state, services, ports, proxy, paths** | **This file (STACK.md)** |
| Security posture / hardening status | `~/homelab-data/SECURITY_MASTER_2026-05-30.md` |
| Roadmap / pickup order / what's next | `~/homelab-data/ROADMAP.md` |
| Workspace/project layout (non-homelab repos) | `~/AGENTS.md` |
| Homelab task runbooks (bringup, tunnel, pi flash) | `~/.claude/skills/iamfaulty-homelab/references/*.md` |

## 9. Deprecated — do NOT trust as current

These predate the Caddy migration / hardening and are kept only for history. Each should carry a banner pointing here:
- `~/.claude/skills/iamfaulty-homelab/SKILL.md` — service map + "NPM is edge" + "qBit via gluetun" are **stale**.
- `~/homelab-data/INVENTORY.md` — "three stacks" model is **stale**.
- `~/homelab-data/dropbox/agent-registry/port-map.json` — stale/incomplete (see §7.4).

---
*Maintainer note: when the stack changes, update §4 + the "Last verified" date and re-run the verify command. Keep this file thin — link to specialized docs, don't duplicate them.*
