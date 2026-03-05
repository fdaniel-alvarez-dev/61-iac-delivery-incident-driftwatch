# Security

## Principles

- **No secrets** in git, in reports, or in terminal output.
- **Least privilege** for any future integration (read-only where possible; separate identities for plan vs apply).
- **Auditability**: every change should be attributable to a PR + an approval + an artifact.

## What this repo enforces today (offline)

- Secret-pattern scanning on `examples/` inputs (common token and private-key signatures).
- Guardrail validation that models real-world expectations:
  - plan-before-apply
  - approvals for deploy
  - mandatory tests and smoke checks
  - rollback strategy declared

## Recommended controls for real integrations (when you wire it up)

- Use OIDC short-lived credentials in CI (no long-lived cloud keys).
- Split permissions:
  - “planner” role: read-only + plan
  - “deployer” role: apply + narrow resource permissions
- Require protected branches and signed commits for deploy paths.
- Store artifacts (plans, reports) in immutable storage with retention.

## Secrets handling checklist (never commit)

- `.env*`
- `*.pem`, `*.key`
- `*credentials*`
- `*.tfstate*` and `.terraform/`
- `artifacts/` (reports can contain sensitive metadata)

