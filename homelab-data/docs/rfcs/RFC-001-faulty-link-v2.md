# RFC-001: Faulty Link v2 — WebSocket Live Updates, Grafana, and Federation

## Status
Draft

## Summary

Extend Faulty Link from a REST-only bridge to a real-time mesh observability platform with WebSocket live updates, Grafana integration, geographic visualization, and multi-gateway federation.

## Motivation

The current v1 bridge polls well for HTTP clients, but real-time mesh networks need push semantics. A node appearing or disappearing, telemetry arriving, or a position update should be visible within seconds, not on the next polling interval.

## Proposed Changes

### 1. WebSocket Live Updates

Add a `/ws` endpoint to the Go bridge that streams JSON events:

```json
{
  "type": "node.joined",
  "timestamp": "2026-05-26T08:00:00Z",
  "data": {
    "node_id": "!12345678",
    "short_name": "TEST",
    "long_name": "Test Node"
  }
}
```

Event types:
- `node.joined` — new node in store
- `node.updated` — node info changed
- `node.expired` — node TTL exceeded
- `telemetry.received` — new telemetry sample
- `position.received` — new position fix

Implementation:
- `internal/mesh/hub.go` — WebSocket hub with pub/sub
- `internal/mesh/broadcaster.go` — channel-based event broadcasting
- `api/websocket.go` — Gorilla WebSocket upgrade handler

### 2. Grafana Integration

Export Prometheus metrics from the bridge:

```
# HELP mesh_nodes_total Number of known mesh nodes
# TYPE mesh_nodes_total gauge
mesh_nodes_total 12

# HELP mesh_telemetry_received_total Total telemetry messages received
# TYPE mesh_telemetry_received_total counter
mesh_telemetry_received_total{node_id="!12345678"} 456

# HELP mesh_connection_state Current TCP connection state (0=disconnected, 1=connecting, 2=connected)
# TYPE mesh_connection_state gauge
mesh_connection_state 2
```

Add Grafana dashboard JSON for:
- Node count over time
- Telemetry rate per node
- Connection state transitions
- Battery level distribution

### 3. Geographic Map Visualization

Add a `/map` endpoint to the bridge or dashboard that serves a Leaflet.js map:
- Markers for each node with last known position
- Popups showing node info, latest telemetry, last heard time
- Auto-refresh via WebSocket or 30s polling fallback

### 4. Multi-Gateway Federation

Allow multiple bridge instances to share state:

```
Gateway A (Denver) <--gRPC--> Gateway B (Boulder)
```

- gRPC bi-directional streaming for node sync
- Conflict resolution: last-write-wins based on `LastUpdate` timestamp
- Authentication: mutual TLS with pinned certificates

## Non-Goals

- Persistent database storage (still in-memory with TTL)
- Mobile app (web UI only)
- Mesh routing decisions (bridge is observer only)

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1 | 2 days | WebSocket live updates |
| 2 | 2 days | Prometheus metrics + Grafana dashboard |
| 3 | 3 days | Leaflet.js map endpoint |
| 4 | 5 days | gRPC federation |

## Open Questions

1. Should WebSocket events include full node state or deltas?
2. Should Grafana dashboard be in the bridge repo or a separate repo?
3. Should federation use gRPC or plain HTTP/2 with Server-Sent Events?

## References

- `faulty-link-backend/internal/mesh/store.go` — current in-memory store
- `faulty-link-backend/api/handlers.go` — current REST handlers
- Prometheus client_golang: https://github.com/prometheus/client_golang
- Gorilla WebSocket: https://github.com/gorilla/websocket
