# ADR-005: Public/Private Boundary Design in Daily Brief

## Status
Accepted

## Context
The `daily-brief` serves two audiences:
- **Private (me):** Local system status, stack health, smart home data — sensitive infrastructure info
- **Public (anyone):** Media feed, message board, calendar scheduling — safe to share

The same FastAPI app serves both. We need a clean boundary that:
- Defaults to private (safe)
- Exposes public data with no auth friction
- Prevents accidental leakage of sensitive data
- Is easy to reason about and audit

## Decision
Use a single query parameter (`?public=1`) to toggle public mode. Private data is only rendered when the parameter is absent or false.

## Consequences

### Positive
- **Simple** — one boolean, no auth system, no session management
- **Explicit** — the URL tells you which mode you're in
- **Cache-friendly** — public pages can be CDN-cached without session concerns
- **Audit-friendly** — grep for `public` in the code to find all boundary checks

### Negative
- **Not truly secure** — anyone can omit `?public=1` and see private data if they reach the instance
- **No user tracking** — can't tell who posted what on the message board
- **Rate limiting** — public endpoint needs protection from spam

## Mitigations
- **Network-level:** Private instance runs on Tailscale or VPN; public instance is a separate deployment
- **Future:** Add basic auth or OAuth for private mode if exposed to the internet
- **Rate limiting:** Add per-IP rate limiting on `/message` endpoint

## Alternatives Considered

| Approach | Why Rejected |
|----------|-------------|
| Separate apps | More containers to maintain; shared SQLite is harder |
| JWT auth | Overkill for a personal dashboard; adds complexity |
| HTTP Basic Auth | Browser prompts are ugly; hard to toggle |
| Cookie-based sessions | Stateful; harder to cache and reason about |

## References
- `daily-brief/main.py` — `public: bool = False` parameter on `/` and `/api/brief`
- `daily-brief/templates/index.html` — `{% if not public %}` blocks
