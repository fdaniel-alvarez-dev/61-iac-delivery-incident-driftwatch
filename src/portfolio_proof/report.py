from __future__ import annotations

import json
from typing import Iterable

from .model import Finding, PainPoint, Severity


def render_report(context: dict[str, str], findings: Iterable[Finding]) -> str:
    by_pain: dict[PainPoint, list[Finding]] = {p: [] for p in PainPoint}
    for f in findings:
        by_pain[f.pain_point].append(f)

    lines: list[str] = []
    lines.append(f"# DriftWatch Report: {context.get('service','unknown-service')}")
    lines.append("")
    lines.append("Generated deterministically from `examples/` inputs.")
    lines.append("")
    lines.append("## Context")
    lines.append("")
    lines.append(f"- Service: `{context.get('service')}`")
    lines.append(f"- Pipeline: `{context.get('pipeline')}`")
    lines.append(f"- Examples: `{context.get('examples_dir')}`")
    lines.append(f"- Now: `{context.get('now')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    counts = _counts(findings)
    lines.append(f"- Findings: HIGH={counts['HIGH']}, MEDIUM={counts['MEDIUM']}, LOW={counts['LOW']}")
    lines.append("")

    for pain in PainPoint:
        lines.append(f"## { _pain_title(pain) }")
        lines.append("")
        items = by_pain[pain]
        if not items:
            lines.append("- No findings.")
            lines.append("")
            continue
        for f in items:
            lines.append(f"### [{f.severity.value}] {f.title}")
            lines.append("")
            if f.details:
                details = json.dumps(f.details, indent=2, sort_keys=True)
                lines.append("```json")
                lines.append(details)
                lines.append("```")
                lines.append("")
            lines.append(f"- Recommendation: {f.recommendation}")
            lines.append(f"- Runbook: `{f.runbook}`")
            lines.append("")

    lines.append("## How this maps to interview pain points")
    lines.append("")
    lines.append("- Drift: inventory diffs + immutable attribute enforcement + tag contracts.")
    lines.append("- Delivery: pipeline contract gates + plan/approval + rollback readiness.")
    lines.append("- Incidents: SLO completeness (including latency) + MTTR signal + runbooks.")
    lines.append("")

    return "\n".join(lines)


def _pain_title(pain: PainPoint) -> str:
    return {
        PainPoint.IAC_DRIFT: "Pain Point 1 — IaC Drift & Fragile Automation",
        PainPoint.DELIVERY_FRICTION: "Pain Point 2 — Delivery Friction & Risky Releases",
        PainPoint.RELIABILITY_INCIDENTS: "Pain Point 3 — Reliability Under On-Call Pressure",
    }[pain]


def _counts(findings: Iterable[Finding]) -> dict[str, int]:
    out = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        out[f.severity.value] += 1
    return out

