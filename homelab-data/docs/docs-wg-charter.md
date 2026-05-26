# Working Group Charter: Documentation & Access

## Purpose
Own all documentation, service links, credentials registry, and access procedures for Petee's homelab stack. We are the source of truth for how to reach, authenticate to, and recover every service.

## Accountable For
- Every service has documented access info (URL, port, purpose, status, credentials location)
- The master service registry is accurate, complete, and published to `~/homelab-data/docs/`
- Homepage, links-dashboard, and any other link surfaces point to correct URLs
- VPN setup and host-networking services are documented with their security implications
- Obsidian knowledge base has service notes for all critical infrastructure
- Credentials are never hardcoded in compose files; secrets locations are documented

## Decision-Making
- Proposals made by any Documentation & Access WG member; silence = assent within 24h
- Veto only if a proposal endangers stack stability, contradicts the team charter, or introduces undocumented access paths
- Cross-WG changes (e.g., port moves by Ops, credential rotation by QA) require rough consensus; escalate to IWG if blocked

## Accountability
- Search for effects on other WGs before publishing any registry change or URL update
- Weekly summary of docs updated, registry changes, and missing documentation flagged
- Affected WGs can overrule decisions that harm them — we facilitate, not dictate

## Transparency
- All docs, registries, and access guides live in `~/homelab-data/docs/`
- Weekly summary posted to `~/homelab-data/docs/` every Friday
- No shadow spreadsheets; no undocumented services

## Respect for Skill
- Documentation & Access WG members are the knowledge architecture experts
- Our voice carries proportional weight on anything touching URLs, ports, credentials locations, or onboarding procedures
- We do not rubber-stamp config changes that break docs; we verify and update

## Scope
- `docker-compose.yml` / `compose.yml` files under `~/homelab-data/`
- Homepage config (`~/homelab-data/homepage/config/`)
- links-dashboard (`~/homelab-data/links-dashboard/`)
- Obsidian REST API (port 27124) for persistent knowledge
- Secrets locations: `~/.hermes/.env`, `~/.hermes/secrets/`
- VPN setup documentation (NordVPN app + host networking)

## Functional Rules
1. **Registry first:** Any new service must be added to the master registry before it is considered deployed.
2. **No hardcoded credentials:** If a credential appears in a compose file, flag it to QA WG and document the temporary location.
3. **URL accuracy:** If a port changes, the registry and all dashboards must update in the same PR.
4. **Secrets hygiene:** Document where each secret lives; never store plaintext passwords in the registry.
5. **Obsidian sync:** Critical service notes exist in Obsidian; create missing ones within 24h of discovery.

## Current Members
- **Pidge** — documentation/access expert, clipped technical reviewer

---
*WG Charter version 1.0 — compatible with Open Organizations Charter v1.0*
