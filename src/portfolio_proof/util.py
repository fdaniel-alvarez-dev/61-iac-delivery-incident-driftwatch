from __future__ import annotations

import datetime as dt


def parse_utc(value: str) -> dt.datetime:
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(v)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)

