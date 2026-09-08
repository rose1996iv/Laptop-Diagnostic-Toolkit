"""Non-destructive storage inventory."""

from __future__ import annotations

from typing import Any

from ..utils.command import powershell_json


def collect_storage() -> list[dict[str, Any]]:
    """Collect disk model, capacity, interface, and reported status."""
    raw = powershell_json("Get-CimInstance Win32_DiskDrive | Select Model,SerialNumber,Size,InterfaceType,MediaType,Status,FirmwareRevision | ConvertTo-Json -Compress")
    items = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
    return [{"model": item.get("Model"), "serial": item.get("SerialNumber"), "capacity_gb": round(item["Size"] / 1024**3, 1) if isinstance(item.get("Size"), (int, float)) else None, "interface": item.get("InterfaceType"), "media_type": item.get("MediaType"), "status": item.get("Status"), "firmware": item.get("FirmwareRevision")} for item in items if isinstance(item, dict)]
