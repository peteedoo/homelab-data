# RFC-002: TPM System Design Interview Preparation

## Status
Draft

## Purpose

Structured preparation for TPM system design interviews. Each scenario is designed to demonstrate:
- Requirements gathering
- Architecture design
- Trade-off analysis
- Operational thinking
- Cross-functional coordination

---

## Scenario 1: Design a Rate Limiter

**Prompt:** Design a rate limiter for a public API that handles 100K requests/second.

### Requirements
- **Functional:** Limit requests per client IP, per API key, per endpoint
- **Non-functional:** <1ms latency overhead, 99.99% availability, horizontal scalability

### Architecture
```
Client → CDN (CloudFront) → API Gateway → Rate Limiter → Backend Service
                              ↓
                         Redis Cluster (token buckets)
```

### Key Decisions
- **Algorithm:** Token bucket (allows bursts, smooths traffic)
- **Store:** Redis with Lua scripts for atomic decrement
- **Sharding:** Consistent hashing on client IP for Redis partitioning
- **Fallback:** Allow requests if Redis is down (fail open vs fail closed)

### Trade-offs
| Approach | Pros | Cons |
|----------|------|------|
| Token bucket | Allows bursts, smooth | Harder to implement distributed |
| Sliding window | Accurate | More memory, harder to shard |
| Fixed window | Simple | Burst at window boundaries |

---

## Scenario 2: Design a Distributed Cache

**Prompt:** Design a cache layer for a read-heavy system (1M reads/sec, 10K writes/sec).

### Requirements
- **Functional:** Key-value store, TTL support, cache invalidation
- **Non-functional:** <5ms p99 read latency, eventual consistency acceptable

### Architecture
```
App → Client Library (consistent hashing) → Cache Cluster (Memcached/Redis)
         ↓
    Database (source of truth)
```

### Key Decisions
- **Eviction:** LRU with TTL
- **Consistency:** Write-through for strong consistency, write-behind for throughput
- **Sharding:** Consistent hashing with virtual nodes
- **Cold start:** Cache warming job on deployment

### Failure Modes
- Cache miss → database hit (degraded performance, not failure)
- Cache node down → rehash to other nodes (brief spike in misses)
- Cache stampede → probabilistic early expiration

---

## Scenario 3: Design a Message Queue

**Prompt:** Design a message queue that guarantees at-least-once delivery.

### Requirements
- **Functional:** Publish/subscribe, durable messages, consumer groups
- **Non-functional:** 100K messages/sec throughput, message retention 7 days

### Architecture
```
Producer → Broker Cluster → Consumer
              ↓
           Storage (append-only log)
```

### Key Decisions
- **Storage:** Append-only log (Kafka-style) for high throughput
- **Acknowledgment:** Consumer acks offset, broker retries unacked messages
- **Partitioning:** By key for ordering, round-robin for load balancing
- **Retention:** Time-based with compaction for key-value topics

### Delivery Guarantees
| Guarantee | Implementation | Trade-off |
|-----------|---------------|-----------|
| At-most-once | Fire and forget | May lose messages |
| At-least-once | Ack + retry | May duplicate messages |
| Exactly-once | Idempotent consumers + transactional ack | Complex, slower |

---

## Scenario 4: Design a Monitoring System (Meta)

**Prompt:** Design the monitoring system you built for Faulty Link, but at scale.

### Requirements
- **Functional:** Metrics, logs, traces, alerts
- **Non-functional:** 1M metrics/sec ingestion, <30s alert latency, 99.9% availability

### Architecture
```
Agent → Collector → Time-Series DB → Query Engine → Dashboard/Alertmanager
          ↓
       Log Store (Elasticsearch/Loki)
          ↓
       Trace Store (Jaeger/Tempo)
```

### Key Decisions
- **Metrics:** Prometheus remote write → Thanos/Cortex for long-term storage
- **Logs:** Fluent Bit → Loki (cheaper than Elasticsearch for structured logs)
- **Traces:** OpenTelemetry → Jaeger (or Tempo for cost efficiency)
- **Alerts:** Prometheus Alertmanager with PagerDuty/OpsGenie integration

### What I Learned from Building It
- Start with the simplest thing that works (SQLite, not InfluxDB)
- Instrument before you optimize (you can't improve what you don't measure)
- Alert on symptoms, not causes ("requests are failing" not "CPU is high")

---

## Interview Tips

1. **Clarify first.** Ask about scale, latency, consistency requirements before designing.
2. **Draw first.** Sketch the architecture before diving into components.
3. **Trade-offs explicitly.** "I chose X over Y because Z. If requirements change, I'd reconsider."
4. **Operational thinking.** How do you deploy, monitor, and rollback this system?
5. **Cross-functional.** How does this interact with security, compliance, cost optimization?

---

## References

- `faulty-gateway/main.go` — token bucket rate limiter implementation
- `faulty-link-backend/internal/mesh/store.go` — in-memory cache with TTL
- `stack-dashboard/main.py` — lightweight monitoring with SQLite
- `homelab-monitor/src/homelab_monitor/cli.py` — metrics collection agent
