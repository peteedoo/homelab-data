# Job Backlog

Queue of roles to apply to. Hermes reads this each morning and preps up to 10 Priority A roles.

| Status | Priority | Company | Role | URL | Resume | Cover | Notes |
|--------|----------|---------|------|-----|--------|-------|-------|
| Ready | C | TestCo | TPM | https://example.com/test | resume-samsara-ats | none | Test row |

## How to add a role

1. Add a row with Status = `Ready`.
2. Set Priority to `A`, `B`, or `C`.
3. Put the base name of the resume/cover PDFs (without `.pdf`) from `ops/career/`.
4. Run `python3 ~/.hermes/scripts/job-hunt/orchestrator.py --dry-run` to preview.
