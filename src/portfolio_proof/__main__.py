from __future__ import annotations

import argparse
import sys

from .cli import cmd_report, cmd_validate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="portfolio_proof",
        description="Deterministic drift/delivery/incident guardrail demo.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    report = sub.add_parser("report", help="Generate artifacts/report.md from examples/")
    report.add_argument("--examples", default="examples", help="Path to examples directory")
    report.add_argument("--artifacts", default="artifacts", help="Path to artifacts directory")
    report.add_argument("--now", default=None, help="Deterministic clock (ISO8601, e.g. 2026-03-01T00:00:00Z)")
    report.set_defaults(func=cmd_report)

    validate = sub.add_parser("validate", help="Validate examples/ against guardrails; exit non-zero on violations")
    validate.add_argument("--examples", default="examples", help="Path to examples directory")
    validate.add_argument("--now", default=None, help="Deterministic clock (ISO8601, e.g. 2026-03-01T00:00:00Z)")
    validate.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

