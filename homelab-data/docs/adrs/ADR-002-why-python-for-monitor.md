# ADR-002: Why Python for the Health Monitor

## Status
Accepted

## Context
The homelab monitor needs to:
- Run as a CLI tool on macOS and Linux
- Inspect Docker containers, system CPU, memory, disk usage
- Format output as human-readable tables or JSON
- Support configurable alert thresholds via YAML
- Exit with non-zero codes for automation integration
- Be testable with pytest and deployable via pip

## Decision
Use Python 3.11+ for the monitor implementation.

## Consequences

### Positive
- **Rich ecosystem** — `psutil`, `docker`, `rich`, `pyyaml` are mature and well-documented
- **Rapid development** — dynamic typing and REPL make iteration fast
- **CLI frameworks** — `click` handles arguments, flags, and help text with decorators
- **Testing** — pytest with fixtures and parametrize makes test coverage easy
- **Distribution** — `pip install` or Docker image; no compilation step

### Negative
- **GIL** — true parallelism is limited; but the monitor is I/O bound (Docker API calls)
- **Packaging** — virtualenvs and dependency resolution can be fragile
- **Performance** — slower than Go for tight loops; irrelevant for a monitoring CLI

## Alternatives Considered

| Language | Why Rejected |
|----------|-------------|
| Go | Faster but more verbose; no equivalent to `psutil` or `rich` in stdlib |
| Bash | Unmaintainable beyond 100 lines; no structured data handling |
| Rust | Overkill for a CLI tool; compile times slow iteration |
| Node.js | Good for CLIs but weaker systems/ops library ecosystem |

## References
- `homelab-monitor/src/homelab_monitor/cli.py` — argparse entrypoint
- `homelab-monitor/src/homelab_monitor/monitor.py` — system data collection
- `homelab-monitor/src/homelab_monitor/format.py` — rich table formatting
