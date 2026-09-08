"""Cautious value and purchase recommendations based only on supplied evidence."""

from __future__ import annotations

from typing import Any


def value_index(score: int | float | None, price: float | None) -> float | None:
    """Return diagnostic score per thousand currency units when price is supplied."""
    if score is None or price is None or price <= 0:
        return None
    return round(float(score) / (price / 1000), 3)


def purchase_decision(score: int | None, price: float | None, *, critical_failures: int = 0, confidence: int = 0) -> dict[str, Any]:
    """Return a transparent recommendation, never a market valuation."""
    if score is None or price is None or price <= 0 or confidence < 50:
        decision = "INSUFFICIENT DATA"
    elif critical_failures:
        decision = "DO NOT BUY"
    elif score >= 85:
        decision = "BUY"
    elif score >= 70:
        decision = "NEGOTIATE"
    else:
        decision = "CONSIDER ALTERNATIVES"
    return {"decision": decision, "price": price, "value_index": value_index(score, price), "recommended_range": [round(price * 0.9), round(price * 0.95)] if price and decision in ("NEGOTIATE", "CONSIDER ALTERNATIVES") else None, "confidence": confidence, "basis": "Diagnostic recommendation based on supplied price and measured evidence; not an objective market valuation."}


def condition_indicators(*, battery_cycles: int | None = None, storage_power_on_hours: int | None = None, windows_install_age_days: int | None = None) -> dict[str, Any]:
    """Classify usage indicators cautiously; software cannot prove new or used status."""
    known = [value for value in (battery_cycles, storage_power_on_hours, windows_install_age_days) if value is not None]
    if not known:
        result = "UNVERIFIED"
    elif any(value >= threshold for value, threshold in ((battery_cycles, 100), (storage_power_on_hours, 1000), (windows_install_age_days, 180)) if value is not None):
        result = "POSSIBLY USED"
    else:
        result = "NEW-LIKE"
    return {"classification": result, "indicators": {"battery_cycles": battery_cycles, "storage_power_on_hours": storage_power_on_hours, "windows_install_age_days": windows_install_age_days}, "caution": "Indicators suggest usage patterns only; they cannot prove whether a laptop is new or used."}
