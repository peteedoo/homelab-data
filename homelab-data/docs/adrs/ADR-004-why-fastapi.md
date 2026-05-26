# ADR-004: Why FastAPI over Flask/Django

## Status
Accepted

## Context
Both `stack-dashboard` and `daily-brief` need:
- HTTP REST APIs with JSON responses
- HTML template rendering for dashboards
- Async support for concurrent requests
- Automatic OpenAPI/Swagger documentation
- Type hints for maintainability
- Easy Docker deployment

## Decision
Use FastAPI for both services.

## Consequences

### Positive
- **Performance** — async/await handles concurrent requests without thread overhead
- **Type safety** — Pydantic models validate request/response shapes at runtime
- **Auto-docs** — `/docs` endpoint generates interactive Swagger UI from type hints
- **Modern** — built on Starlette + Pydantic, actively maintained
- **Template support** — Jinja2 integration for HTML dashboards

### Negative
- **Learning curve** — async Python and Pydantic models are new to some developers
- **Smaller ecosystem** — fewer plugins than Flask or Django
- **Debugging** — async stack traces can be harder to read

## Alternatives Considered

| Framework | Why Rejected |
|-----------|-------------|
| Flask | Simpler but synchronous by default; no auto-docs or type validation |
| Django | Full-stack ORM + admin is overkill for microservices; heavier footprint |
| Tornado | Mature but less popular; smaller community than FastAPI |
| Go stdlib | Fast but no template auto-reload; more verbose for HTML rendering |

## References
- `stack-dashboard/main.py` — FastAPI app with SQLite, Jinja2 templates
- `daily-brief/main.py` — FastAPI app with message board, calendar
