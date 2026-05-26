# Night Shift Plan — Allegro Burn

**Goal:** Burn remaining ~94% of Allegro quota by building deep, portfolio-grade work across all four repos + new infrastructure.

**Constraint:** Work must be reviewable, coherent, and demo-ready by morning. No throwaway code.

---

## Phase 1: Infrastructure as Code (IaC) — 2 hours

### 1.1 Terraform / OpenTofu for AWS/GCP homelab mirror
- VPC, subnets, security groups
- EC2/GCE instance for running the stack
- S3/GCS bucket for backups
- Route53/Cloud DNS for `iamfaulty.com` subdomains
- Outputs: instance IP, bucket name, DNS records

### 1.2 Pulumi alternative (Python)
- Same infrastructure, Pulumi Python for comparison
- Decision doc: when to use Terraform vs Pulumi

### 1.3 GitHub Actions CI/CD matrix
- **homelab-monitor:** Python 3.11, 3.12, 3.13 + lint (ruff, mypy) + coverage
- **faulty-link-backend:** Go 1.22, 1.23 + race detector + benchmark
- **stack-dashboard:** Python + Docker build + push to GHCR
- **daily-brief:** Python + Docker build + push to GHCR

---

## Phase 2: Deep Testing & Benchmarks — 2 hours

### 2.1 Load testing
- `faulty-link-backend`: `k6` or `oha` load test for `/nodes`, `/telemetry`
- `stack-dashboard`: `locust` or `wrk` for `/api/health`, `/api/trend`
- `daily-brief`: `wrk` for `/api/brief`, `/message`

### 2.2 Benchmark suite
- Go: `BenchmarkStore`, `BenchmarkDecoder`, `BenchmarkHandler`
- Python: `pytest-benchmark` for monitor functions

### 2.3 Chaos engineering (light)
- Kill Docker containers mid-run, verify auto-restart
- Drop TCP connections, verify bridge reconnect
- Fill disk, verify monitor alerts

---

## Phase 3: New Project — API Gateway / Reverse Proxy — 3 hours

### 3.1 `faulty-gateway` (Go)
- Reverse proxy for all services with path-based routing
- Rate limiting (token bucket, per-IP)
- JWT auth middleware (optional, stubbed)
- Health check aggregation (calls all service `/health` endpoints)
- Metrics endpoint (`/metrics`) with Prometheus format
- Caddy integration or standalone

### 3.2 Service discovery
- Read `docker-compose.yml` files, auto-register routes
- Hot reload on compose file changes

---

## Phase 4: Documentation & Content — 2 hours

### 4.1 Architecture Decision Records (ADRs)
- ADR-001: Why Go for the bridge
- ADR-002: Why Python for the monitor
- ADR-003: Why SQLite over PostgreSQL for dashboard
- ADR-004: Why FastAPI over Flask/Django
- ADR-005: Public/private boundary design in daily-brief
- ADR-006: Terraform vs Pulumi decision

### 4.2 Blog post: "Building a Self-Healing Homelab"
- 1500 words, technical but accessible
- Code snippets, architecture diagrams
- Target: DevOps / SRE audience

### 4.3 Conference talk outline
- 30-minute talk, 10 slides
- Title: "From Supply Chain to Systems: A TPM's Homelab"
- Demo script: 5-minute live walkthrough

---

## Phase 5: Research & RFCs — 2 hours

### 5.1 Faulty Link v2 RFC
- WebSocket live updates for node telemetry
- Grafana integration (Prometheus metrics export)
- Geographic map visualization (Leaflet.js)
- Multi-gateway federation (gateway-to-gateway mesh)

### 5.2 TPM System Design Scenarios
- Design a rate limiter
- Design a distributed cache
- Design a message queue
- Design a monitoring system (meta: design what you built)

---

## Deliverables by Morning

| Item | Location |
|------|----------|
| IaC (Terraform + Pulumi) | `~/homelab-data/infra/terraform/`, `~/homelab-data/infra/pulumi/` |
| CI/CD workflows | `.github/workflows/` in each repo |
| Load test results | `~/homelab-data/benchmarks/` |
| ADRs | `~/homelab-data/docs/adrs/` |
| Blog post | `~/homelab-data/content/blog/` |
| Talk outline | `~/homelab-data/content/talks/` |
| RFCs | `~/homelab-data/docs/rfcs/` |
| New project: faulty-gateway | `~/faulty-gateway/` |

---

## Review Checklist (Morning)

- [ ] Can I `terraform apply` and get a running instance?
- [ ] Do all CI workflows pass on push?
- [ ] Can I run load tests and see numbers?
- [ ] Does the gateway route to all services?
- [ ] Are ADRs clear and decision-focused?
- [ ] Is the blog post publishable?
- [ ] Can I give the talk from the outline?

---

**Approve this plan and I'll start executing. I'll checkpoint progress every hour.**
