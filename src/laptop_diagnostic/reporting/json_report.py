"""Privacy-aware JSON report export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.models import DiagnosticReport


def write_json_report(report: DiagnosticReport, path: Path, *, include_serial: bool = False, include_hostname: bool = False, include_ip: bool = False) -> None:
    """Write a report while masking sensitive identifiers by default."""
    data: dict[str, Any] = report.to_dict()
    system = data.get("results", {}).get("system", {})
    for key, enabled in (("serial", include_serial), ("hostname", include_hostname), ("ip_address", include_ip)):
        if not enabled:
            system.pop(key, None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True, default=str), encoding="utf-8")
