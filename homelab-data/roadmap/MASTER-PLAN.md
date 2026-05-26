# Faulty Link Master Plan

> **Goal:** Build a portfolio-grade, production-hardened, publicly-visible homelab platform that demonstrates TPM-level system thinking, engineering depth, and operational excellence.

**Current state:** 5 repos, CI/CD, benchmarks, ADRs, blog post, RFCs. All local.
**Target state:** Deployed, monitored, documented, demoable, job-interview-ready.

---

## Phase 1: Deploy to Production (Days 1-2)

### 1.1 Infrastructure
- [ ] Terraform: AWS VPC + EC2 t4g.small (ARM, cheap) or GCP e2-micro
- [ ] Tailscale: Auth key for EC2, join mesh
- [ ] Caddy: Reverse proxy with auto-TLS for `*.iamfaulty.com`
- [ ] Docker Compose: All 5 services on single host
- [ ] Health checks: Caddy upstream health, auto-failover
- [ ] Monitoring: Prometheus + Grafana on host
- [ ] Backups: S3 bucket for SQLite dbs, daily cron

### 1.2 Service Deployment
- [ ] `homelab-monitor`: Run as systemd service on host (not Docker, needs host access)
- [ ] `faulty-link-backend`: Docker, port 8080, env for MESHTASTIC_HOST
- [ ] `stack-dashboard`: Docker, port 3336, volume for SQLite
- [ ] `daily-brief`: Docker, port 3337, volume for SQLite, env for CALENDAR_EMBED_URL
- [ ] `faulty-gateway`: Docker, port 8888, routes to all backends

### 1.3 DNS + TLS
- [ ] `bridge.iamfaulty.com` → Caddy → gateway → backend
- [ ] `dashboard.iamfaulty.com` → Caddy → gateway → dashboard
- [ ] `brief.iamfaulty.com` → Caddy → gateway → daily-brief (public)
- [ ] `brief.iamfaulty.com/?public=1` → public view
- [ ] `health.iamfaulty.com` → gateway `/health`

### 1.4 Security
- [ ] Fail2ban on host
- [ ] Rate limiting at gateway (already implemented)
- [ ] Tailscale ACL: only my devices can access private ports
- [ ] Cloudflare proxy for DDoS protection (optional)

---

## Phase 2: Observability + Alerting (Days 2-3)

### 2.1 Prometheus Metrics
- [ ] `faulty-link-backend`: Export mesh_nodes_total, mesh_telemetry_received_total, mesh_connection_state
- [ ] `faulty-gateway`: Export gateway_requests_total, gateway_rate_limited_total, gateway_backend_health
- [ ] `stack-dashboard`: Export dashboard_snapshots_total, dashboard_services_up
- [ ] Node exporter: Host CPU, memory, disk

### 2.2 Grafana Dashboards
- [ ] "Mesh Overview": Node count, telemetry rate, connection state
- [ ] "Infrastructure": Host CPU/memory/disk, Docker container status
- [ ] "Gateway": Request rate, error rate, latency p50/p95/p99
- [ ] "Daily Brief": Message count, calendar views

### 2.3 Alerting
- [ ] Prometheus Alertmanager → Telegram/Discord
- [ ] Alerts:
  - mesh_connection_state == 0 for >5min
  - node_count == 0 for >10min
  - host_memory_percent > 90
  - host_disk_percent > 85
  - gateway_backend_health != healthy

### 2.4 Log Aggregation
- [ ] Promtail → Loki (or Grafana Agent)
- [ ] Structured logs from all services (JSON)
- [ ] Dashboard: error rate, slow queries, failed requests

---

## Phase 3: Faulty Link v2 — Real-Time Mesh (Days 3-5)

### 3.1 WebSocket Live Updates
- [ ] `/ws` endpoint on bridge
- [ ] Event types: node.joined, node.updated, node.expired, telemetry.received, position.received
- [ ] JavaScript client on dashboard for real-time updates
- [ ] Reconnect logic with exponential backoff

### 3.2 Geographic Map
- [ ] Leaflet.js map on `/map`
- [ ] Markers for each node with popup (info, telemetry, last heard)
- [ ] Auto-refresh via WebSocket
- [ ] Offline map tiles (for off-grid demo)

### 3.3 Grafana Integration
- [ ] Prometheus metrics endpoint on bridge
- [ ] Grafana dashboard JSON in repo
- [ ] Recording rules for derived metrics (telemetry rate per node)

### 3.4 Multi-Gateway Federation (Stretch)
- [ ] gRPC bi-directional streaming between gateways
- [ ] Node sync with last-write-wins conflict resolution
- [ ] mTLS authentication

---

## Phase 4: Content + Community (Days 5-7)

### 4.1 Demo Video
- [ ] 5-minute screen recording: dashboard, bridge, message board, calendar
- [ ] Voiceover or captions
- [ ] Upload to YouTube, embed in portfolio

### 4.2 Blog Posts
- [ ] "Building a Self-Healing Homelab" (done)
- [ ] "Zero-Allocation Telemetry Ring Buffers in Go"
- [ ] "Why I Chose SQLite Over PostgreSQL for My Dashboard"
- [ ] "From Supply Chain to Systems: A TPM's Journey"

### 4.3 Social
- [ ] LinkedIn post series: one per repo
- [ ] Twitter/X thread: architecture decisions
- [ ] Hacker News submission: blog post
- [ ] Reddit r/homelab, r/selfhosted: project showcase

### 4.4 Talks
- [ ] Submit to local meetups (Denver DevOps, Boulder Go)
- [ ] CFP for KubeCon, PromCon, Meshtastic summit
- [ ] 30-minute talk outline + slide deck

---

## Phase 5: Advanced Features (Days 7-10)

### 5.1 Smart Home Integration
- [ ] Home Assistant API: read sensors, control lights
- [ ] Daily brief section: current temp, lights on/off, recent automations
- [ ] Webhook: HA → daily-brief when automation triggers

### 5.2 Media Automation
- [ ] Integrate existing cron jobs: Dilla music scan, podcast feed, YouTube
- [ ] Daily brief: "New releases today", "New podcast episodes"
- [ ] API: add/remove subscriptions

### 5.3 Agent Network
- [ ] Connect to `homelab-data/agent-network/`
- [ ] Agent status in daily brief: who's online, what they're working on
- [ ] Message board: agents can post updates

### 5.4 Mobile App (Stretch)
- [ ] PWA: add to home screen, offline support
- [ ] Push notifications: alerts from Prometheus
- [ ] Geolocation: show nearest mesh node

---

## Phase 6: TPM Interview Prep (Ongoing)

### 6.1 System Design Scenarios
- [ ] Rate limiter (done in RFC-002)
- [ ] Distributed cache (done in RFC-002)
- [ ] Message queue (done in RFC-002)
- [ ] Monitoring system (done in RFC-002)
- [ ] Additional: design a CDN, design a search engine, design a payment system

### 6.2 Behavioral Prep
- [ ] STAR stories for each repo: Situation, Task, Action, Result
- [ ] "Tell me about a time you had to make a trade-off"
- [ ] "How do you handle conflicting priorities?"
- [ ] "Describe a system you built that failed and what you learned"

### 6.3 Mock Interviews
- [ ] Practice with friends, mentors, or AI
- [ ] Record yourself, review for clarity and conciseness
- [ ] Time yourself: 45 minutes per system design

---

## Phase 7: Job Search (Ongoing)

### 7.1 Target Roles
- [ ] Technical Program Manager (TPM) — primary
- [ ] Senior Software Engineer (Infrastructure) — secondary
- [ ] DevOps Engineer / SRE — tertiary

### 7.2 Target Companies
- [ ] Startups: Vercel, Railway, Fly.io, Render
- [ ] Big Tech: AWS, Google, Meta, Apple (TPM roles)
- [ ] Meshtastic / Off-grid: companies building resilient communication
- [ ] Supply Chain Tech: Flexport, Project44, FourKites (leverage domain exp)

### 7.3 Application Materials
- [ ] Resume: one page, metrics-focused, TPM angle
- [ ] Portfolio site: GitHub Pages, links to all repos
- [ ] Cover letter template: customizable per company
- [ ] LinkedIn: updated headline, featured section with repos

---

## Daily Rhythm

| Time | Activity |
|------|----------|
| 06:00 | Check daily brief, review alerts |
| 07:00 | Standup with agents (async) |
| 08:00 | Deep work: one phase, one deliverable |
| 12:00 | Break, lunch |
| 13:00 | Content: blog, social, video |
| 15:00 | Networking: DMs, meetups, applications |
| 17:00 | Review: git commits, deploy status |
| 18:00 | Shutdown: document blockers for tomorrow |

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Repos | 5+ | 5 |
| CI/CD passing | 100% | 100% |
| Test coverage | >80% | ~70% |
| Deployed services | 5 | 0 |
| Public URL | yes | no |
| Blog posts | 4+ | 1 |
| Demo video | 1 | 0 |
| Job applications | 20+ | 0 |
| Interviews | 5+ | 0 |
| Offers | 1+ | 0 |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| AWS costs | $$$ | Use t4g.small spot, set billing alerts |
| Burnout | High | Sleep 7h, one rest day per week |
| Scope creep | High | Strict phase gates, no new repos without retiring old |
| Allegro expires | Medium | Use remaining tokens for deep research, not code |
| No job offers | High | Apply broadly, leverage network, consider contract |

---

*Plan created: 2026-05-26*
*Next review: daily at 06:00*
