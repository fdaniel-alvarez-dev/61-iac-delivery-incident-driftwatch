from __future__ import annotations

import dataclasses
import enum
from typing import Any


class PainPoint(str, enum.Enum):
    IAC_DRIFT = "iac_drift_and_fragile_automation"
    DELIVERY_FRICTION = "delivery_friction_and_risky_releases"
    RELIABILITY_INCIDENTS = "reliability_under_oncall_pressure"


class Severity(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @property
    def rank(self) -> int:
        return {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[self.value]


@dataclasses.dataclass(frozen=True)
class Finding:
    pain_point: PainPoint
    severity: Severity
    title: str
    details: dict[str, Any]
    recommendation: str
    runbook: str

