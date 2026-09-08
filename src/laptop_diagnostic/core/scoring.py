"""Transparent scoring and expected specification validation."""

from __future__ import annotations

from typing import Any

from .models import CheckResult, ComparisonStatus, ExpectedProfile, Status


WEIGHTS = {"system": 10, "cpu": 15, "ram": 10, "gpu": 20, "thermals": 10, "storage": 15, "display": 10, "battery": 5, "network": 5}


def _contains_any(value: Any, expected: list[str]) -> bool:
    text = str(value or "").casefold()
    return not expected or any(item.casefold() in text for item in expected)


def _as_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _comparison(ok: bool | None) -> ComparisonStatus:
    if ok is True:
        return ComparisonStatus.MATCH
    if ok is False:
        return ComparisonStatus.MISMATCH
    return ComparisonStatus.UNVERIFIED


def compare_expected(results: dict[str, Any], profile: ExpectedProfile) -> list[CheckResult]:
    """Compare detected values with a profile without treating missing data as a match."""
    system = results.get("system", {})
    checks: list[CheckResult] = []

    def add(name: str, ok: bool | None, summary: str, details: dict[str, Any]) -> None:
        status = Status.PASS if ok is True else Status.FAIL if ok is False else Status.NOT_AVAILABLE
        details["comparison"] = _comparison(ok).value
        checks.append(CheckResult(name, status, summary, details, None if ok is not None else "Detection unavailable"))

    if profile.manufacturer:
        value = system.get("manufacturer")
        add("Manufacturer", bool(value) and profile.manufacturer.casefold() in str(value).casefold(), f"Detected: {value or 'N/A'}", {"expected": profile.manufacturer, "detected": value})
    if profile.model_contains:
        value = system.get("model")
        add("Model", bool(value) and profile.model_contains.casefold() in str(value).casefold(), f"Detected: {value or 'N/A'}", {"expected": profile.model_contains, "detected": value})
    if profile.cpu_contains_any:
        value = results.get("cpu", {}).get("name") or system.get("cpu")
        add("CPU", _contains_any(value, profile.cpu_contains_any) if value else None, f"Detected: {value or 'N/A'}", {"expected": profile.cpu_contains_any, "detected": value})
    if profile.ram_gb_min is not None:
        value = results.get("ram", {}).get("total_gb") or system.get("ram_gib")
        add("RAM", float(value) >= profile.ram_gb_min if value is not None else None, f"Detected: {value or 'N/A'} GB", {"expected_min_gb": profile.ram_gb_min, "detected_gb": value})
    if profile.gpu_contains_any:
        gpus = _as_items(results.get("gpus", results.get("gpu")))
        names = [gpu.get("name") for gpu in gpus if gpu.get("name")]
        matched = next((name for name in names if _contains_any(name, profile.gpu_contains_any)), None)
        add("GPU", bool(matched) if names else None, f"Detected: {', '.join(names) or 'N/A'}", {"expected": profile.gpu_contains_any, "detected": names, "matched": matched})
    if profile.gpu_vram_gb_min is not None:
        gpus = _as_items(results.get("gpus", results.get("gpu")))
        values = [gpu.get("dedicated_vram_gb") for gpu in gpus if isinstance(gpu.get("dedicated_vram_gb"), (int, float))]
        value = max(values, default=None)
        add("Dedicated VRAM", float(value) >= profile.gpu_vram_gb_min if value is not None else None, f"Detected: {value or 'N/A'} GB", {"expected_min_gb": profile.gpu_vram_gb_min, "detected_gb": value})
    if profile.storage_gb_min is not None:
        drives = _as_items(results.get("storage"))
        capacities = [drive.get("capacity_gb") for drive in drives if isinstance(drive.get("capacity_gb"), (int, float))]
        value = max(capacities, default=None)
        add("Storage", float(value) >= profile.storage_gb_min if value is not None else None, f"Detected: {value or 'N/A'} GB", {"expected_min_gb": profile.storage_gb_min, "detected_gb": value})
    if profile.display_resolution:
        displays = _as_items(results.get("display"))
        values = [display.get("resolution") for display in displays if display.get("resolution")]
        value = next((item for item in values if item == profile.display_resolution), values[0] if values else None)
        add("Display", value == profile.display_resolution if value else None, f"Detected: {value or 'N/A'}", {"expected": profile.display_resolution, "detected": value})
    if profile.refresh_rate_hz_min is not None:
        displays = _as_items(results.get("display"))
        rates = [display.get("refresh_rate_hz") for display in displays if isinstance(display.get("refresh_rate_hz"), (int, float))]
        value = max(rates, default=None)
        add("Refresh rate", float(value) >= profile.refresh_rate_hz_min if value is not None else None, f"Detected: {value or 'N/A'} Hz", {"expected_min_hz": profile.refresh_rate_hz_min, "detected_hz": value})
    return checks


def calculate_score(checks: list[CheckResult], results: dict[str, Any] | None = None) -> tuple[int, Status, list[str]]:
    """Return score, overall status, and actionable reasons."""
    if not checks:
        return 0, Status.NOT_AVAILABLE, ["No diagnostic checks completed"]
    failed = [check for check in checks if check.status is Status.FAIL]
    unavailable = [check for check in checks if check.status is Status.NOT_AVAILABLE]
    available = [check for check in checks if check.status in (Status.PASS, Status.FAIL, Status.WARNING)]
    passed = [check for check in available if check.status is Status.PASS]
    score = round(100 * len(passed) / len(available)) if available else 0
    reasons = [f"{check.name}: {check.summary}" for check in failed]
    if failed:
        return score, Status.FAIL, reasons
    if unavailable or any(check.status is Status.WARNING for check in checks):
        return score, Status.WARNING, reasons + [f"{check.name} requires review" for check in unavailable]
    return score, Status.PASS, []
