# ADR-003: Why SQLite over PostgreSQL for the Dashboard

## Status
Accepted

## Context
The stack-dashboard needs to:
- Store periodic health snapshots (CPU, memory, disk, service status)
- Retain data for 48 hours, then auto-prune
- Serve trend data via REST API for canvas sparklines
- Run as a single Docker container with minimal setup
- Support ~1 snapshot per minute = ~2,880 rows/day = lightweight

## Decision
Use SQLite (file-based) instead of PostgreSQL.

## Consequences

### Positive
- **Zero setup** — no separate database container, no connection strings
- **Single file** — easy to backup, copy, or inspect with `sqlite3` CLI
- **Sufficient performance** — SQLite handles 10k+ writes/sec, far above our 1/min rate
- **No network overhead** — in-process, no TCP connections or connection pooling
- **Pragmatic** — the dashboard is a single-node tool, not a distributed system

### Negative
- **No concurrent writes from multiple processes** — but the dashboard is the only writer
- **Limited ALTER TABLE** — schema migrations are manual; acceptable for v1
- **No replication** — but data is ephemeral (48h TTL) and source of truth is the live system

## Alternatives Considered

| Database | Why Rejected |
|----------|-------------|
| PostgreSQL | Requires separate container, connection management, migrations — overkill for 3k rows/day |
| InfluxDB | Time-series optimized but adds container + query language complexity |
| Prometheus | Pull-based metrics, not a general store; harder to query for sparklines |
| Redis | In-memory only; data lost on restart unless persisted |

## References
- `stack-dashboard/main.py` — SQLite init, snapshot recording, pruning
- `stack-dashboard/templates/index.html` — canvas sparkline rendering
