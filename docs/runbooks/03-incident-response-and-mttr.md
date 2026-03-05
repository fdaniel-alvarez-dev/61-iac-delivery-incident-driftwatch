# Runbook: Incident response and MTTR reduction

## When to use

- An alert triggers for availability, errors, or latency.
- Customer-impacting degradation is suspected.

## Goals

- Stabilize quickly.
- Keep comms consistent.
- Reduce MTTR by making the next incident easier than the last.

## Procedure

1) Declare incident and assign roles:
   - incident commander
   - communications lead
   - subject-matter responders
2) Stabilize:
   - stop the bleeding (rollback, feature flag, rate limiting)
   - confirm customer impact window
3) Diagnose with observability:
   - error rate, saturation, dependency health
   - latency breakdown (p50/p95/p99)
4) Resolve and verify:
   - confirm SLO recovery
   - document what changed
5) Learn:
   - add a concrete action item per root cause
   - ensure runbooks link to dashboards and rollback steps

## Verification

- Incident MTTR is tracked and trending down.
- SLOs are defined for the service and referenced during triage.

