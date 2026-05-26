# Building a Self-Healing Homelab: From Supply Chain to Systems

> How I turned a Raspberry Pi and a radio into a four-system operational stack — and what it taught me about technical program management.

---

## The Problem

I run a homelab. Not the kind with a rack of servers and a 10G switch — the kind with a Mac mini on a shelf, a Raspberry Pi in a 3D-printed case, and a Meshtastic radio node that talks to off-grid sensors over LoRa.

The problem is simple: when the Mac mini runs out of memory, the Docker containers die. When the Docker containers die, the Go bridge that ingests mesh telemetry goes offline. When the bridge goes offline, the off-grid sensors go dark. And I'm not there to fix it — I'm at work, or asleep, or in the mountains where the sensors are.

I needed infrastructure that heals itself.

---

## The Stack

I built four systems. Each has one job. Together they form a closed loop.

### 1. homelab-monitor (Python)

A CLI tool that reports CPU, memory, disk, and Docker container status. It exits non-zero when thresholds are breached, so I can drop it into any automation layer without writing a parser.

```bash
$ homelab-monitor --json
{
  "cpu_percent": 12.3,
  "memory": {"percent": 45.2, "used": 7.2, "total": 16.0},
  "disk": {"percent": 67.1, "used": 134.2, "total": 200.0},
  "docker": {"running": 8, "total": 10}
}
```

Key decision: **Graceful degradation.** If the Docker daemon is unreachable, it still reports system metrics instead of crashing. This matters when Docker is the thing that's broken.

### 2. faulty-link-backend (Go)

An HTTP bridge that connects to a Meshtastic node over TCP, decodes length-delimited protobuf streams, and serves REST JSON for node registry and telemetry.

Key decisions:
- **Auto-reconnect with jittered backoff.** Exponential backoff capped at 30s with ±25% jitter prevents thundering-herd reconnects.
- **Thread-safe in-memory store with TTL.** A `sync.RWMutex`-protected store with background eviction keeps the API fast and prevents unbounded memory growth.
- **Per-node telemetry ring buffers.** Each node gets a circular buffer (64 samples) so the API can return history without hitting a database.

Benchmarks on Apple M4:
```
BenchmarkStorePutNode-10        25883964    43.33 ns/op    0 B/op    0 allocs/op
BenchmarkTelemetryRingAppend-10 126842524   9.548 ns/op   0 B/op    0 allocs/op
```

Zero allocations on the hot path. That's the Go I wanted.

### 3. stack-dashboard (FastAPI)

A real-time dashboard with SQLite health trending, canvas sparklines, and service discovery from Docker Compose files.

Key decision: **SQLite over PostgreSQL.** The dashboard stores ~3,000 rows/day. SQLite handles 10,000+ writes/sec. Why add a container, connection pool, and migration framework for data that's ephemeral anyway?

### 4. daily-brief (FastAPI)

A morning dashboard with a twist: a public mode. The private view shows local system status and stack health. The public view (`?public=1`) shows media feeds, a message board, and a calendar scheduler.

Key decision: **No auth for public mode.** The boundary is a query parameter, not a login form. This is a personal dashboard, not a SaaS product. The public instance runs on a separate deployment, and the private instance stays on Tailscale.

---

## The Integration

```
┌─────────────────────────────────────────────────────────────┐
│                         Homelab Host                         │
│  ┌──────────────────┐      ┌──────────────────────────────┐│
│  │ homelab-monitor  │      │ faulty-link-backend          ││
│  │ (Python CLI)     │      │ (Go bridge)                  ││
│  │                  │      │                              ││
│  │ Watches:         │      │ Connects:                    ││
│  │ • CPU/mem/disk   │      │ • Meshtastic TCP 4403        ││
│  │ • Docker health  │◄─────┤ • Protobuf decoder           ││
│  │ • Alert thresholds│ JSON │ • In-memory store            ││
│  └──────────────────┘ exit └──────────────────────────────┘│
│           │                    ▲                           │
│           │                    │ HTTP                       │
│           ▼                    │                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ stack-dashboard (FastAPI)                            │  │
│  │ • SQLite health trending                             │  │
│  │ • Canvas sparklines                                  │  │
│  │ • Service discovery                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│           │                                                │
│           │ cron outputs                                   │
│           ▼                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ daily-brief (FastAPI)                                │  │
│  │ Private: local status, stack health                  │  │
│  │ Public:  media feed, message board, calendar         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Off-Grid Mesh ◄── LoRa ──► Gateway Node ◄── TCP ──► Bridge│
└─────────────────────────────────────────────────────────────┘
```

The monitor watches the bridge. The dashboard watches the monitor. The brief surfaces everything. The mesh watches the physical world.

---

## What I Learned

### System thinking
I didn't build four random side projects — I built a closed loop. Every component has a single responsibility, and the interfaces (JSON stdout, HTTP REST, TCP protobuf, SQLite rows) are explicit contracts. This is the same thinking I applied to supply chain optimization: map the flow, identify the bottlenecks, instrument the critical paths.

### Cross-domain integration
This stack spans Go networking, Python DevOps tooling, FastAPI data visualization, and embedded/IoT protobuf. Integrating them required understanding each domain's constraints — byte-level wire formats, container health semantics, off-grid radio limitations — and designing seams that don't leak complexity.

### Operational excellence
- **Resilience:** The bridge auto-reconnects. The monitor degrades gracefully. The dashboard prunes old data.
- **Observability:** Every component exposes health state — the bridge via `/health`, the monitor via JSON + exit codes, the dashboard via SQLite trends, the brief via cron-aggregated snapshots.
- **Testability:** Both Go and Python repos have unit tests. The Go bridge includes race-detector runs in CI.
- **Composability:** Every interface is designed for machine consumption first — JSON stdout, REST APIs, SQLite rows — so future agents and automations can build on this foundation without parsing HTML.

---

## The TPM Angle

I'm transitioning from supply chain operations to technical program management. This portfolio is my answer to the question: "How do you think about systems?"

The answer: I think in loops. I instrument the critical path. I design for failure. And I never build a dashboard without asking who else might need to see it.

The daily-brief's public mode is the most TPM thing I built. It turns infrastructure visibility into a coordination tool. Anyone can leave a message or schedule time without needing an account. That's the difference between a monitoring stack and a communication stack — and it's the difference between an ops engineer and a program manager.

---

## Repositories

- [`homelab-monitor`](https://github.com/peteedoo/homelab-monitor) — Python CLI for Docker/system health
- [`faulty-link-backend`](https://github.com/peteedoo/faulty-link-backend) — Go HTTP bridge for Meshtastic mesh
- [`stack-dashboard`](https://github.com/peteedoo/stack-dashboard) — FastAPI dashboard with health trending
- [`daily-brief`](https://github.com/peteedoo/daily-brief) — Public daily brief with message board

---

*Built by [Pete Doo](https://github.com/peteedoo) — infrastructure that heals itself, networks that work off-grid, and interfaces that let anyone coordinate.*
