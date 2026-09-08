"""Display resolution and refresh-rate collection."""

from __future__ import annotations

from typing import Any

from ..utils.command import powershell_json


def collect_display() -> list[dict[str, Any]]:
    """Collect active display modes exposed by Windows."""
    raw = powershell_json("Get-CimInstance Win32_VideoController | Select Name,CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate,VideoModeDescription | ConvertTo-Json -Compress")
    items = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
    displays = []
    for item in items:
        if not isinstance(item, dict):
            continue
        width, height = item.get("CurrentHorizontalResolution"), item.get("CurrentVerticalResolution")
        displays.append({"gpu": item.get("Name"), "resolution": f"{width}x{height}" if width and height else None, "refresh_rate_hz": item.get("CurrentRefreshRate"), "mode": item.get("VideoModeDescription")})
    return displays
