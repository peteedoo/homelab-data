# Faulty Link — Portfolio Overview

> **Self-healing homelab infrastructure with intelligent mesh-network backend, unified observability, and public coordination tools.**

I built a four-system operational stack: a Python health monitor that keeps the host honest, a Go mesh-network bridge that brings off-grid sensor data into the modern world, a real-time dashboard with health trending, and a public daily brief with a message board and meeting scheduler. Together they form a complete operational story — infrastructure that heals itself, networks that work off-grid, and interfaces that let anyone coordinate with me.

---

## Executive Summary

I operate a homelab that runs a Meshtastic mesh-network gateway. When the gateway goes unhealthy, the off-grid sensors go dark. I built `homelab-monitor` (Python) to detect resource exhaustion and container failures before they kill the mesh backend, `faulty-link-backend` (Go) to ingest protobuf telemetry from the mesh and serve it over REST, `stack-dashboard` (FastAPI) to visualize health trends and service topology, and `daily-brief` (FastAPI) to surface a public message board and meeting scheduler. The result is a self-healing stack where the monitor watches the bridge, the dashboard watches the monitor, and the brief lets the world coordinate with me.

---

## Project 1: homelab-monitor

**What it is:** A Python CLI for Docker and system health monitoring. It reports CPU, memory, disk usage, top processes, and Docker container status in human-readable tables or JSON. It exits non-zero when thresholds are breached, making it easy to wire into cron, systemd, or CI pipelines.

**Why it matters:** Infrastructure failures are usually preceded by resource pressure. By surfacing per-mount disk usage, top CPU consumers, and Docker health checks in a single command, I can diagnose problems in seconds instead of minutes. The non-zero exit code means I can drop it into any automation layer without writing a parser.

**Key technical decisions:**
- **Modular architecture** — `monitor.py` collects data, `format.py` renders it, `config.py` loads thresholds. Separation of concerns makes unit testing trivial.
- **Graceful degradation** — The Docker SDK is optional. If the daemon is unreachable, the tool still reports system metrics instead of crashing.
- **Threshold-driven exit codes** — Returning `1` on alert breach makes the CLI composable with shell operators (`&&`, `||`) and CI gates.
- **Rich terminal output** — Tables are formatted with `rich` so operators get color-coded, scannable output without needing a dashboard.

---

## Project 2: faulty-link-backend

**What it is:** A Go HTTP bridge that connects to a Meshtastic mesh node over TCP (port 4403), decodes length-delimited protobuf streams, and exposes a REST JSON API for node registry and telemetry. It includes a Python CLI consumer and is designed to run as a Docker service.

**Why it matters:** Meshtastic nodes speak protobuf over TCP, but most modern tools expect JSON over HTTP. This bridge closes that gap without adding heavy infrastructure. It auto-reconnects when the mesh node drops, buffers telemetry in ring buffers, and evicts stale data — so a brief network blip doesn't lose state or require manual intervention.

**Key technical decisions:**
- **Auto-reconnect with jittered backoff** — Exponential backoff capped at 30s with ±25% jitter prevents thundering-herd reconnects and keeps the gateway resilient.
- **Length-delimited protobuf decoder** — Meshtastic streams are `[varint length][payload]`. The decoder handles framing separately from unmarshalling, so protobuf schema changes don't break the wire protocol layer.
- **Thread-safe in-memory store with TTL** — A `sync.RWMutex`-protected store with background eviction keeps the API fast and prevents unbounded memory growth.
- **Per-node telemetry ring buffers** — Each node gets a circular buffer (default 64 samples) so the API can return history without hitting a database.
- **Graceful shutdown** — `context.Cancel` + `sync.WaitGroup` ensures in-flight requests and TCP reads finish cleanly before exit.

---

## Integration Story

These four projects are not isolated repos — they are a single operational system with public and private faces.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Homelab Host                                    │
│                                                                              │
│  ┌──────────────────────┐         ┌──────────────────────────────────────┐  │
│  │  homelab-monitor     │         │  faulty-link-backend                 │  │
│  │  (Python CLI)        │         │  (Go bridge)                         │  │
│  │                      │         │                                      │  │
│  │  Watches:            │         │  Connects:                           │  │
│  │  • CPU / mem / disk  │         │  • Meshtastic TCP 4403               │  │
│  │  • Docker health     │◄────────┤  • Protobuf decoder                  │  │
│  │  • Alert thresholds  │  JSON   │  • In-memory store                   │  │
│  │                      │  exit   │  • REST API :8080                    │  │
│  └──────────────────────┘  code   └──────────────────────────────────────┘  │
│           │                      ▲                                          │
│           │                      │ HTTP                                      │
│           ▼                      │                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  stack-dashboard (FastAPI)                                           │   │
│  │  • SQLite health trending                                            │   │
│  │  • Service discovery from compose files                              │   │
│  │  • Canvas sparklines, Tailscale network view                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│           │                                                                  │
│           │ cron outputs                                                     │
│           ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  daily-brief (FastAPI)                                               │   │
│  │  Private: local status, stack health, smart home                     │   │
│  │  Public:  media feed, message board, calendar scheduler              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Off-Grid Mesh Network <──── LoRa ────>  Gateway Node <──── TCP ────> Bridge  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How they connect

1. **The bridge runs in Docker.** `faulty-link-backend` is deployed as a container on the homelab host.
2. **The monitor watches the bridge.** `homelab-monitor` inspects the container's status and health via the Docker SDK, alongside host-level CPU, memory, and disk metrics.
3. **The dashboard visualizes trends.** `stack-dashboard` consumes the monitor's JSON output, stores snapshots in SQLite, and renders sparklines and service topology.
4. **The brief surfaces everything.** `daily-brief` reads cron job outputs from `~/homelab-data/dropbox/`, shows private status on the internal view, and exposes a public message board + calendar for coordination.
5. **Alerts drive action.** If the bridge container becomes unhealthy or the host runs out of memory, `homelab-monitor` exits with code `1`. A systemd unit or cron job can restart the container or notify the operator.

---

## Skills Demonstrated

| Skill | Evidence |
|-------|----------|
| **Python** | `homelab-monitor` CLI, config loader, table formatting, pytest suite |
| **Go** | `faulty-link-backend` TCP client, HTTP handlers, concurrency primitives |
| **Docker** | Container health inspection, SDK usage, deployment target for the bridge |
| **Protobuf** | Length-delimited framing decoder, `google.golang.org/protobuf` unmarshalling |
| **Networking** | TCP keepalive, exponential backoff with jitter, stale-connection detection |
| **Testing** | pytest (Python), `go test` with race detector, table-driven tests |
| **CI/CD** | GitHub Actions matrix build (Python 3.11 + 3.12), Makefile targets |

---

## TPM Angle

### System thinking
I didn't build four random side projects — I built a closed loop with a public surface. The monitor observes the bridge, the dashboard observes the monitor, the brief surfaces both private and public data, and the mesh observes the physical world. Every component has a single responsibility, and the interfaces (JSON stdout, HTTP REST, TCP protobuf, SQLite snapshots) are explicit contracts.

### Cross-domain integration
This portfolio spans four domains: systems programming (Go networking), DevOps tooling (Python CLI, Docker), data visualization (FastAPI, canvas sparklines), and public-facing web services (message board, calendar integration). Building the daily-brief required designing a privacy boundary — local system data stays on `?public=0`, while the message board and calendar are world-accessible on `?public=1`.

### Operational excellence
- **Resilience:** The bridge auto-reconnects and the monitor degrades gracefully when Docker is unavailable.
- **Observability:** Every component exposes health state — the bridge via `/health`, the monitor via JSON + exit codes, the dashboard via SQLite trends, the brief via cron-aggregated snapshots.
- **Testability:** Both Go and Python repos have unit tests for core logic, with race-detector runs in CI.
- **Composability:** Every interface is designed for machine consumption first — JSON stdout, REST APIs, SQLite rows — so future agents and automations can build on this foundation without parsing HTML.
- **Public coordination:** The daily-brief's public mode turns infrastructure visibility into a networking tool — anyone can leave a message or schedule time without needing an account.

---

## Repositories

- [`homelab-monitor`](https://github.com/peteedoo/homelab-monitor) — Python CLI for Docker/system health monitoring
- [`faulty-link-backend`](https://github.com/peteedoo/faulty-link-backend) — Go HTTP bridge for Meshtastic mesh networks
- [`stack-dashboard`](https://github.com/peteedoo/stack-dashboard) — FastAPI dashboard with health trending and service discovery
- [`daily-brief`](https://github.com/peteedoo/daily-brief) — Public daily brief with message board and meeting scheduler

---

*Built by [Pete Doo](https://github.com/peteedoo) — infrastructure that heals itself, networks that work off-grid, and interfaces that let anyone coordinate.*
