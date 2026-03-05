from __future__ import annotations

import dataclasses
import datetime as dt
import json
import pathlib
import re
import tomllib
from typing import Any

from .model import Finding, PainPoint, Severity
from .secrets import scan_for_secrets
from .util import parse_utc


@dataclasses.dataclass(frozen=True)
class EngineContext:
    examples_dir: pathlib.Path
    now: dt.datetime
    desired: dict[str, Any]
    observed: dict[str, Any]
    pipeline: dict[str, Any]
    slo: dict[str, Any]
    incidents: list[dict[str, Any]]


class DemoEngine:
    def __init__(self, ctx: EngineContext) -> None:
        self._ctx = ctx

    @classmethod
    def from_examples_dir(cls, examples_dir: pathlib.Path, now_override: str | None) -> "DemoEngine":
        meta = _load_toml(examples_dir / "meta.toml")
        now_raw = now_override or meta.get("demo_now")
        now = parse_utc(now_raw) if now_raw else dt.datetime(1970, 1, 1, tzinfo=dt.UTC)

        desired = _load_toml(examples_dir / "desired_infra.toml")
        observed = _load_toml(examples_dir / "observed_infra.toml")
        pipeline = _load_toml(examples_dir / "cicd_pipeline.toml")
        slo = _load_toml(examples_dir / "slo.toml")
        incidents = _load_jsonl(examples_dir / "incidents.jsonl")

        scan_for_secrets(examples_dir)

        ctx = EngineContext(
            examples_dir=examples_dir,
            now=now,
            desired=desired,
            observed=observed,
            pipeline=pipeline,
            slo=slo,
            incidents=incidents,
        )
        return cls(ctx)

    def context_summary(self) -> dict[str, str]:
        service = (self._ctx.slo.get("service") or {}).get("name", "unknown-service")
        pipeline_name = (self._ctx.pipeline.get("pipeline") or {}).get("name", "unknown-pipeline")
        return {
            "service": str(service),
            "pipeline": str(pipeline_name),
            "examples_dir": str(self._ctx.examples_dir),
            "now": self._ctx.now.isoformat().replace("+00:00", "Z"),
        }

    def validate(self) -> list[Finding]:
        findings: list[Finding] = []
        findings.extend(_check_drift(self._ctx.desired, self._ctx.observed))
        findings.extend(_check_delivery(self._ctx.pipeline))
        findings.extend(_check_reliability(self._ctx.slo, self._ctx.incidents))
        return sorted(findings, key=lambda f: (f.severity.rank, f.pain_point.value, f.title))


def _load_toml(path: pathlib.Path) -> dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict TOML at {path}")
    return data


def _load_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"Expected JSON object line in {path}")
        out.append(obj)
    return out


def _resource_map(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = inventory.get("resources") or []
    if not isinstance(items, list):
        raise ValueError("resources must be a list")
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        rid = str(item.get("id", "")).strip()
        if not rid:
            continue
        out[rid] = item
    return out


def _check_drift(desired: dict[str, Any], observed: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    dmap = _resource_map(desired)
    omap = _resource_map(observed)

    missing = sorted(set(dmap) - set(omap))
    extra = sorted(set(omap) - set(dmap))
    common = sorted(set(dmap) & set(omap))

    if missing:
        findings.append(
            Finding(
                pain_point=PainPoint.IAC_DRIFT,
                severity=Severity.HIGH,
                title="Missing resources in observed state",
                details={"missing": missing},
                recommendation="Investigate failed applies; reconcile via IaC (never manual).",
                runbook="docs/runbooks/01-drift-detection-and-remediation.md",
            )
        )

    if extra:
        findings.append(
            Finding(
                pain_point=PainPoint.IAC_DRIFT,
                severity=Severity.HIGH,
                title="Unmanaged resources exist (observed but not desired)",
                details={"unmanaged": extra},
                recommendation="Decide adopt(import) vs delete; route decision through PR and approvals.",
                runbook="docs/runbooks/01-drift-detection-and-remediation.md",
            )
        )

    changed: list[dict[str, Any]] = []
    tag_issues: list[str] = []
    immutable_violations: list[dict[str, Any]] = []

    for rid in common:
        d = dmap[rid]
        o = omap[rid]
        if str(d.get("type")) != str(o.get("type")):
            changed.append({"id": rid, "field": "type", "desired": d.get("type"), "observed": o.get("type")})

        dattrs = (d.get("attrs") or {}) if isinstance(d.get("attrs"), dict) else {}
        oattrs = (o.get("attrs") or {}) if isinstance(o.get("attrs"), dict) else {}

        dtags = dattrs.get("tags") if isinstance(dattrs.get("tags"), dict) else {}
        otags = oattrs.get("tags") if isinstance(oattrs.get("tags"), dict) else {}
        for required_tag in ("env", "owner", "cost_center"):
            if required_tag not in otags:
                tag_issues.append(f"{rid}: missing tag '{required_tag}' in observed")
            if required_tag not in dtags:
                tag_issues.append(f"{rid}: missing tag '{required_tag}' in desired")

        immutable = d.get("immutable_attrs") or []
        if not isinstance(immutable, list):
            immutable = []
        for key in immutable:
            if key in dattrs and key in oattrs and dattrs[key] != oattrs[key]:
                immutable_violations.append(
                    {"id": rid, "attr": key, "desired": dattrs[key], "observed": oattrs[key]}
                )

        for k, v in dattrs.items():
            if k == "tags":
                continue
            if k in oattrs and oattrs[k] != v:
                changed.append({"id": rid, "field": f"attrs.{k}", "desired": v, "observed": oattrs[k]})

    if immutable_violations:
        findings.append(
            Finding(
                pain_point=PainPoint.IAC_DRIFT,
                severity=Severity.HIGH,
                title="Immutable infrastructure attributes changed",
                details={"violations": immutable_violations},
                recommendation="Treat immutable deltas as break-glass events; reconcile via replacement or explicit migration plan.",
                runbook="docs/runbooks/01-drift-detection-and-remediation.md",
            )
        )

    if changed:
        findings.append(
            Finding(
                pain_point=PainPoint.IAC_DRIFT,
                severity=Severity.MEDIUM,
                title="Desired vs observed configuration drift detected",
                details={"deltas": changed[:25], "delta_count": len(changed)},
                recommendation="Make drift reviewable: generate a plan, review in PR, and apply with approvals.",
                runbook="docs/runbooks/01-drift-detection-and-remediation.md",
            )
        )

    if tag_issues:
        findings.append(
            Finding(
                pain_point=PainPoint.IAC_DRIFT,
                severity=Severity.MEDIUM,
                title="Tagging contract violations reduce traceability",
                details={"issues": tag_issues[:25], "issue_count": len(tag_issues)},
                recommendation="Enforce required tags in IaC modules and in drift validation (owner/env/cost_center).",
                runbook="docs/runbooks/01-drift-detection-and-remediation.md",
            )
        )

    return findings


def _check_delivery(pipeline: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    p = pipeline.get("pipeline") if isinstance(pipeline.get("pipeline"), dict) else {}
    required = p.get("required_gates") if isinstance(p.get("required_gates"), list) else []
    required = [str(x) for x in required]

    missing_gates = [g for g in ("fmt", "lint", "unit_tests", "terraform_plan", "deploy_approval", "smoke_tests") if g not in required]
    if missing_gates:
        findings.append(
            Finding(
                pain_point=PainPoint.DELIVERY_FRICTION,
                severity=Severity.HIGH,
                title="Pipeline is missing required delivery gates",
                details={"missing_gates": missing_gates},
                recommendation="Define a single CI/CD contract and enforce it across repos/environments.",
                runbook="docs/runbooks/02-safe-release-and-rollback.md",
            )
        )

    if not bool(p.get("requires_plan_before_apply", False)):
        findings.append(
            Finding(
                pain_point=PainPoint.DELIVERY_FRICTION,
                severity=Severity.HIGH,
                title="Plan-before-apply is not enforced",
                details={},
                recommendation="Block applies unless a reviewed plan artifact exists for the same commit.",
                runbook="docs/runbooks/02-safe-release-and-rollback.md",
            )
        )

    if not bool(p.get("requires_approval_to_deploy", False)):
        findings.append(
            Finding(
                pain_point=PainPoint.DELIVERY_FRICTION,
                severity=Severity.HIGH,
                title="Deployment approval is not required",
                details={},
                recommendation="Require an explicit approval for production deploys (separate from code review).",
                runbook="docs/runbooks/02-safe-release-and-rollback.md",
            )
        )

    if not bool(p.get("requires_protected_branch", False)):
        findings.append(
            Finding(
                pain_point=PainPoint.DELIVERY_FRICTION,
                severity=Severity.MEDIUM,
                title="Protected branch requirement missing",
                details={},
                recommendation="Protect the deploy branch and require CI to pass before merge.",
                runbook="docs/runbooks/02-safe-release-and-rollback.md",
            )
        )

    retention = int(p.get("requires_artifact_retention_days", 0) or 0)
    if retention < 14:
        findings.append(
            Finding(
                pain_point=PainPoint.DELIVERY_FRICTION,
                severity=Severity.MEDIUM,
                title="Artifact retention is too low for audits/rollbacks",
                details={"retention_days": retention},
                recommendation="Retain plans, reports, and deploy artifacts long enough to cover incident investigations.",
                runbook="docs/runbooks/02-safe-release-and-rollback.md",
            )
        )

    rollback = str(p.get("rollback_strategy", "")).strip()
    if rollback not in {"blue-green", "canary", "feature-flag", "roll-forward"}:
        findings.append(
            Finding(
                pain_point=PainPoint.DELIVERY_FRICTION,
                severity=Severity.MEDIUM,
                title="Rollback strategy is missing or unclear",
                details={"rollback_strategy": rollback or None},
                recommendation="Declare and test a rollback strategy (blue/green or canary) as part of the pipeline contract.",
                runbook="docs/runbooks/02-safe-release-and-rollback.md",
            )
        )

    return findings


def _check_reliability(slo: dict[str, Any], incidents: list[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    service = slo.get("service") if isinstance(slo.get("service"), dict) else {}
    slos = slo.get("slos") if isinstance(slo.get("slos"), dict) else {}

    missing = [k for k in ("availability_target", "error_rate_target", "latency_p95_ms_target") if k not in slos]
    if missing:
        findings.append(
            Finding(
                pain_point=PainPoint.RELIABILITY_INCIDENTS,
                severity=Severity.HIGH,
                title="SLO coverage is incomplete (availability/errors/latency)",
                details={"missing_slos": missing},
                recommendation="Define SLOs for availability, errors, and latency (GenAI systems are latency-bound).",
                runbook="docs/runbooks/03-incident-response-and-mttr.md",
            )
        )

    mttr_minutes = _compute_mttr_minutes(incidents)
    if mttr_minutes is None:
        findings.append(
            Finding(
                pain_point=PainPoint.RELIABILITY_INCIDENTS,
                severity=Severity.MEDIUM,
                title="No resolvable incidents found to compute MTTR",
                details={},
                recommendation="Track incidents with start/resolved timestamps to measure MTTR and drive reliability work.",
                runbook="docs/runbooks/03-incident-response-and-mttr.md",
            )
        )
    else:
        sev2_plus = [i for i in incidents if str(i.get("severity", "")).lower() in {"sev1", "sev2"}]
        if mttr_minutes > 60 and sev2_plus:
            findings.append(
                Finding(
                    pain_point=PainPoint.RELIABILITY_INCIDENTS,
                    severity=Severity.HIGH,
                    title="MTTR is high for recent high-severity incidents",
                    details={"mttr_minutes": mttr_minutes, "high_sev_incidents": [i.get("id") for i in sev2_plus]},
                    recommendation="Improve runbooks + rollback + observability; make mitigation steps executable in minutes.",
                    runbook="docs/runbooks/03-incident-response-and-mttr.md",
                )
            )
        else:
            findings.append(
                Finding(
                    pain_point=PainPoint.RELIABILITY_INCIDENTS,
                    severity=Severity.LOW,
                    title="MTTR signal is present (use it to keep improving)",
                    details={"mttr_minutes": mttr_minutes},
                    recommendation="Keep incident hygiene strong: consistent comms, clear ownership, and actionable follow-ups.",
                    runbook="docs/runbooks/03-incident-response-and-mttr.md",
                )
            )

    for runbook in (
        "docs/runbooks/01-drift-detection-and-remediation.md",
        "docs/runbooks/02-safe-release-and-rollback.md",
        "docs/runbooks/03-incident-response-and-mttr.md",
    ):
        if not pathlib.Path(runbook).exists():
            findings.append(
                Finding(
                    pain_point=PainPoint.RELIABILITY_INCIDENTS,
                    severity=Severity.HIGH,
                    title="Required runbooks are missing from repo",
                    details={"missing_runbook": runbook},
                    recommendation="Add minimal runbooks that responders can execute at 3am.",
                    runbook="docs/runbooks/03-incident-response-and-mttr.md",
                )
            )

    if str(service.get("tier", "")).lower() in {"critical", "tier-0", "tier0"} and "latency_p95_ms_target" in slos:
        target = int(slos.get("latency_p95_ms_target", 0) or 0)
        if target <= 0:
            findings.append(
                Finding(
                    pain_point=PainPoint.RELIABILITY_INCIDENTS,
                    severity=Severity.MEDIUM,
                    title="Latency SLO is defined but invalid",
                    details={"latency_p95_ms_target": target},
                    recommendation="Set a realistic p95 latency target and alert on burn rate.",
                    runbook="docs/runbooks/03-incident-response-and-mttr.md",
                )
            )

    return findings


def _compute_mttr_minutes(incidents: list[dict[str, Any]]) -> float | None:
    durations: list[float] = []
    for inc in incidents:
        try:
            started = parse_utc(str(inc["started"]))
            resolved = parse_utc(str(inc["resolved"]))
        except Exception:
            continue
        if resolved <= started:
            continue
        durations.append((resolved - started).total_seconds() / 60.0)
    if not durations:
        return None
    return round(sum(durations) / len(durations), 1)

