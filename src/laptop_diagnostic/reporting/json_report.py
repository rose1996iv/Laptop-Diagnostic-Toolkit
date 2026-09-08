"""Privacy-aware JSON report export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.models import DiagnosticReport


def report_data(report: DiagnosticReport, *, include_serial: bool = False, include_hostname: bool = False, include_ip: bool = False) -> dict[str, Any]:
    """Return report data with sensitive identifiers removed by default."""
    data: dict[str, Any] = report.to_dict()
    allowed = {"serial": include_serial, "hostname": include_hostname, "ip_address": include_ip}

    def redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: redact(item) for key, item in value.items() if allowed.get(key, True)}
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    return redact(data)


def write_json_report(report: DiagnosticReport, path: Path, *, include_serial: bool = False, include_hostname: bool = False, include_ip: bool = False) -> None:
    """Write a report while masking sensitive identifiers by default."""
    data = report_data(report, include_serial=include_serial, include_hostname=include_hostname, include_ip=include_ip)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True, default=str), encoding="utf-8")
