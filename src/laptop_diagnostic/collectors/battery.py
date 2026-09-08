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
    static = powershell_json("Get-CimInstance -Namespace root/wmi -ClassName BatteryStaticData | Select DesignedCapacity | ConvertTo-Json -Compress")
    full = powershell_json("Get-CimInstance -Namespace root/wmi -ClassName BatteryFullChargedCapacity | Select FullChargedCapacity | ConvertTo-Json -Compress")
    static_item = static[0] if isinstance(static, list) and static else static if isinstance(static, dict) else {}
    full_item = full[0] if isinstance(full, list) and full else full if isinstance(full, dict) else {}
    design_mwh, full_mwh = static_item.get("DesignedCapacity"), full_item.get("FullChargedCapacity")
    design_wh = round(design_mwh / 1000, 2) if isinstance(design_mwh, (int, float)) else None
    full_wh = round(full_mwh / 1000, 2) if isinstance(full_mwh, (int, float)) else None
    health = battery_health(design_wh, full_wh)
    label = "Excellent" if health is not None and health >= 90 else "Good" if health is not None and health >= 80 else "Fair" if health is not None and health >= 70 else "Poor" if health is not None else "Battery health unverified"
    return {"present": bool(item), "name": item.get("Name"), "percent": item.get("EstimatedChargeRemaining"), "charging": item.get("BatteryStatus") in (2, 6, 7, 8, 9), "estimated_runtime_minutes": item.get("EstimatedRunTime"), "design_voltage": item.get("DesignVoltage"), "design_capacity_wh": design_wh, "full_charge_capacity_wh": full_wh, "health_percent": health, "health_label": label}
