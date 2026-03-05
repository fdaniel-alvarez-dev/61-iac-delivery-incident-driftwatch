from __future__ import annotations

import pathlib
import re


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token (classic)", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("GitHub token (fine-grained)", re.compile(r"github_pat_[A-Za-z0-9_]{80,}")),
    ("Private key header", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Bearer token", re.compile(r"Authorization:\\s*Bearer\\s+[A-Za-z0-9._\\-]{20,}")),
]


def scan_for_secrets(root: pathlib.Path) -> None:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in _PATTERNS:
            if pattern.search(text):
                raise ValueError(f"Secret pattern detected ({label}) in {path}")

