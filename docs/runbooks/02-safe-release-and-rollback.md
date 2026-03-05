# Runbook: Safe release and rollback

## When to use

- Pipeline guardrail validation fails (missing approvals, missing tests, or missing rollback strategy).
- A release causes errors, latency regressions, or availability drops.

## Goals

- Keep releases boring: predictability over heroics.
- Make rollback a first-class operation.

## Procedure

1) Confirm gates:
   - Unit tests and static checks passed.
   - Infra plan exists and is reviewed.
   - Deploy requires explicit approval.
2) Deploy progressively:
   - smallest blast radius first (canary, subset, or one environment)
   - monitor SLOs (including latency SLO)
3) If SLOs breach:
   - execute rollback immediately (no debate)
   - capture timeline and key metrics
4) Post-incident:
   - add/adjust automated tests for the failure mode
   - update guardrail rules if the pipeline allowed a risky path

## Verification

- Rollback completes within the agreed RTO.
- The report reflects the rollback strategy and required gates.

