# Architecture

## Goal

Turn “tribal knowledge” about safe infrastructure change and incident readiness into a **deterministic, reviewable report** that can be enforced in CI.

This repo is intentionally offline and standard-library-only: it focuses on the *guardrail logic* that you can later connect to real backends (Terraform state, cloud APIs, CI providers, ticket systems).

## Data flow

1) **Inputs** (`examples/`)
   - `desired_infra.toml`: desired inventory (what IaC says should exist)
   - `observed_infra.toml`: observed inventory (what actually exists)
   - `cicd_pipeline.toml`: CI/CD contract (required gates and behaviors)
   - `slo.toml`: SLOs (including a latency SLO to reflect GenAI constraints)
   - `incidents.jsonl`: recent incidents for MTTR / readiness signals
   - `meta.toml`: deterministic “demo clock”
2) **Checks** (`src/portfolio_proof/`)
   - Drift detection and risk scoring
   - Delivery guardrail validation
   - Reliability readiness validation (SLO coverage, runbooks, MTTR signals)
   - Secret-pattern scanning of inputs (fail fast)
3) **Outputs** (`artifacts/`)
   - `report.md`: human-readable summary + runbook links
4) **Runbooks** (`docs/runbooks/`)
   - Prescriptive steps you can execute during drift, failed releases, and incidents

## Why this demonstrates the “top 3 pains”

- Drift: makes environment divergence visible and actionable (missing resources, unmanaged resources, unsafe deltas).
- Delivery friction: codifies pipeline “contracts” (plan-before-apply, approvals, tests, rollback readiness).
- Reliability: ensures SLOs and runbooks exist, and uses incident data to keep MTTR honest.

## Threat model notes (pragmatic)

Attack surface:

- Inputs can contain secrets by mistake (copied logs, keys, tokens).
- Reports can leak environment details (resource IDs, endpoints).
- CI can become a privilege escalation vector (malicious changes to “apply” steps).

Controls in this repo:

- `validate` blocks known secret patterns in inputs.
- The example inputs are sanitized and deliberately minimal.
- The report avoids printing any environment secrets; it links to runbooks instead of embedding credentials.

Out-of-scope (by design):

- Real cloud API calls and authentication.
- Terraform state locking / remote backends.
- Real incident ticket integration (PagerDuty/Jira).

