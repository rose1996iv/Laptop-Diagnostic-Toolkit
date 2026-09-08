"""Typed models shared by collectors, scoring, and reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT AVAILABLE"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


@dataclass
class CheckResult:
    name: str
    status: Status
    summary: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"status": self.status.value}


@dataclass
class ExpectedProfile:
    name: str = "Unspecified laptop"
    manufacturer: str | None = None
    model_contains: str | None = None
    cpu_contains_any: list[str] = field(default_factory=list)
    ram_gb_min: float | None = None
    gpu_contains_any: list[str] = field(default_factory=list)
    gpu_vram_gb_min: float | None = None
    storage_gb_min: float | None = None
    display_resolution: str | None = None
    refresh_rate_hz_min: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpectedProfile":
        return cls(**{key: value for key, value in data.items() if key in cls.__dataclass_fields__})


@dataclass
class DiagnosticReport:
    timestamp: str
    application_version: str
    results: dict[str, Any] = field(default_factory=dict)
    checks: list[CheckResult] = field(default_factory=list)
    score: int | None = None
    overall_status: Status = Status.NOT_AVAILABLE
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "application_version": self.application_version,
            "results": self.results,
            "checks": [check.to_dict() for check in self.checks],
            "score": self.score,
            "overall_status": self.overall_status.value,
            "recommendations": self.recommendations,
        }
