# ADR-006: Terraform vs Pulumi for Homelab Infrastructure

## Status
Accepted — Terraform primary, Pulumi experimental

## Context
We need Infrastructure as Code (IaC) for:
- AWS/GCP homelab mirror (VPC, compute, storage, DNS)
- Reproducible deployments across regions
- Version-controlled infrastructure changes
- Team onboarding (future hires need to understand the stack)

## Decision
Use Terraform as the primary IaC tool. Maintain a Pulumi Python prototype for comparison and learning.

## Consequences

### Positive (Terraform)
- **Mature ecosystem** — every cloud provider has a first-party provider
- **State management** — battle-tested remote state with locking (S3 + DynamoDB)
- **HCL is declarative** — easy to read, hard to mess up control flow
- **Tooling** — `terraform plan`, `terraform fmt`, `tflint`, `tfsec`
- **Community** — vast module registry, Stack Overflow answers

### Positive (Pulumi prototype)
- **Familiar language** — Python instead of HCL
- **Abstraction** — loops, functions, classes for reusable components
- **Testing** — unit test infrastructure logic with pytest
- **Learning** — keeps the team fluent in both paradigms

### Negative
- **Two tools** — more cognitive load, risk of drift between implementations
- **HCL limitations** — no true loops or conditionals before Terraform 0.12
- **Pulumi maturity** — smaller community, fewer examples

## Resolution
- **Primary:** Terraform for all production infrastructure
- **Experimental:** Pulumi Python for side projects and team learning
- **Decision gate:** Re-evaluate if Pulumi reaches feature parity and community size by 2027

## References
- `homelab-data/infra/terraform/` — VPC, EC2, S3, Route53 modules
- `homelab-data/infra/pulumi/` — Python prototype (optional)
