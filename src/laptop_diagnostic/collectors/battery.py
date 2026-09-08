"""Battery information and conservative health estimation."""

from __future__ import annotations

from typing import Any

from ..utils.command import powershell_json


def battery_health(design_capacity: float | None, full_charge_capacity: float | None) -> float | None:
    """Return a health percentage only when both capacities are valid."""
    if not design_capacity or not full_charge_capacity or design_capacity <= 0 or full_charge_capacity <= 0:
        return None
    return round(min(100.0, full_charge_capacity / design_capacity * 100), 1)


def collect_battery() -> dict[str, Any]:
    """Collect battery status; missing batteries are a normal result."""
    raw = powershell_json("Get-CimInstance Win32_Battery | Select Name,BatteryStatus,EstimatedChargeRemaining,EstimatedRunTime,DesignVoltage | ConvertTo-Json -Compress")
    item = raw[0] if isinstance(raw, list) and raw else raw if isinstance(raw, dict) else {}
    return {"present": bool(item), "name": item.get("Name"), "percent": item.get("EstimatedChargeRemaining"), "charging": item.get("BatteryStatus") in (2, 6, 7, 8, 9), "estimated_runtime_minutes": item.get("EstimatedRunTime"), "design_voltage": item.get("DesignVoltage"), "health_percent": None, "health_label": "Battery health estimate unavailable"}
