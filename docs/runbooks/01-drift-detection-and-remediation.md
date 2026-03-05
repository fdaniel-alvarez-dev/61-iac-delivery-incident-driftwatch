# Runbook: Drift detection and remediation

## When to use

- The drift report shows unmanaged resources, missing resources, or unsafe configuration deltas.
- A deploy fails in one environment but not another (“staging/prod mismatch”).

## Goals

- Restore environment parity.
- Eliminate manual changes by routing fixes through IaC.
- Reduce the blast radius of future drift.

## Procedure

1) Freeze change: pause applies while you assess scope.
2) Classify drift:
   - **Unmanaged**: observed exists but not in desired → decide “adopt” vs “delete”.
   - **Missing**: desired exists but not observed → fix failed apply or provisioning.
   - **Changed**: attribute delta → confirm whether it’s safe/intentional.
3) For each drift item:
   - Record owner and ticket.
   - Choose remediation: adopt (import), reconcile (update desired), or remove.
4) Add a drift prevention guardrail:
   - tag enforcement
   - immutable attribute list (prevent “silent” changes)
   - environment contract checks in CI
5) Re-run validation:
   - `make lint` (runs `validate`)
   - `make demo` (regenerate report)

## Verification

- Drift count returns to 0 (or explicitly acknowledged with a time-bound exception).
- Desired and observed inventories match within tolerated attributes.

