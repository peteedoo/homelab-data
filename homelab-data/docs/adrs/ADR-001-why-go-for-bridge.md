# ADR-001: Why Go for the Mesh Bridge

## Status
Accepted

## Context
The Faulty Link mesh bridge needs to:
- Maintain a persistent TCP connection to a Meshtastic node
- Decode length-delimited protobuf streams in real time
- Serve HTTP REST endpoints for node registry and telemetry
- Handle concurrent access to shared state (nodes, telemetry buffers)
- Auto-reconnect with backoff when the TCP connection drops
- Run as a lightweight Docker container on a Raspberry Pi or Mac mini

## Decision
Use Go (Golang) for the bridge implementation.

## Consequences

### Positive
- **Goroutines + channels** make concurrent TCP reads and HTTP serves trivial
- **Standard library** has everything needed: `net`, `net/http`, `sync`, `context`
- **Static binaries** produce single-file deployables with no runtime dependencies
- **Performance** — Go's scheduler handles thousands of goroutines with minimal overhead
- **Cross-compilation** — build for `linux/arm64` (Raspberry Pi) from macOS with one flag

### Negative
- **Verbosity** — error handling is explicit (`if err != nil`), more lines than Python
- **Protobuf codegen** — requires `protoc` and `protoc-gen-go`, adds build step
- **Smaller ecosystem** — fewer third-party libraries than Python or Node.js

## Alternatives Considered

| Language | Why Rejected |
|----------|-------------|
| Python | GIL limits true concurrency; asyncio adds complexity for sync HTTP + async TCP |
| Node.js | Callback/Promise model is harder to reason about for long-lived TCP connections |
| Rust | Excellent performance but steeper learning curve; borrow checker fights protobuf mutations |
| C | Too low-level for HTTP server; manual memory management is error-prone |

## References
- `faulty-link-backend/internal/mesh/client.go` — TCP client with reconnect
- `faulty-link-backend/internal/mesh/store.go` — thread-safe in-memory store
