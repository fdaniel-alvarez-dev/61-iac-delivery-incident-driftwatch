from __future__ import annotations

import dataclasses
import pathlib
from typing import Iterable

from .engine import DemoEngine
from .model import Finding, Severity
from .report import render_report


def _format_findings_for_console(findings: Iterable[Finding]) -> str:
    parts: list[str] = []
    for f in findings:
        parts.append(f"[{f.severity.value}] {f.pain_point}: {f.title}")
    return "\n".join(parts)


def cmd_validate(args) -> int:
    engine = DemoEngine.from_examples_dir(pathlib.Path(args.examples), now_override=args.now)
    findings = engine.validate()
    if any(f.severity in (Severity.HIGH, Severity.MEDIUM) for f in findings):
        return 2
    return 0


def cmd_report(args) -> int:
    artifacts_dir = pathlib.Path(args.artifacts)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    engine = DemoEngine.from_examples_dir(pathlib.Path(args.examples), now_override=args.now)
    findings = engine.validate()
    report_md = render_report(engine.context_summary(), findings)

    (artifacts_dir / "report.md").write_text(report_md, encoding="utf-8")
    return 0

