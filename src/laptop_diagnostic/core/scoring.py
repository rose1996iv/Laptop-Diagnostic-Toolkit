"""Transparent scoring and expected specification validation."""

from __future__ import annotations

from typing import Any

from .models import CheckResult, ExpectedProfile, Status


WEIGHTS = {"system": 10, "cpu": 15, "ram": 10, "gpu": 20, "thermals": 10, "storage": 15, "display": 10, "battery": 5, "network": 5}


def _contains_any(value: Any, expected: list[str]) -> bool:
    text = str(value or "").casefold()
    return not expected or any(item.casefold() in text for item in expected)


def compare_expected(results: dict[str, Any], profile: ExpectedProfile) -> list[CheckResult]:
    """Compare detected values with a profile without treating missing data as a match."""
    system = results.get("system", {})
    gpu = results.get("gpu", {})
    checks: list[CheckResult] = []

    def add(name: str, ok: bool | None, summary: str, details: dict[str, Any]) -> None:
        status = Status.PASS if ok is True else Status.FAIL if ok is False else Status.NOT_AVAILABLE
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
        value = gpu.get("name")
        add("GPU", _contains_any(value, profile.gpu_contains_any) if value else None, f"Detected: {value or 'N/A'}", {"expected": profile.gpu_contains_any, "detected": value})
    if profile.gpu_vram_gb_min is not None:
        value = gpu.get("dedicated_vram_gb")
        add("Dedicated VRAM", float(value) >= profile.gpu_vram_gb_min if value is not None else None, f"Detected: {value or 'N/A'} GB", {"expected_min_gb": profile.gpu_vram_gb_min, "detected_gb": value})
    if profile.storage_gb_min is not None:
        value = results.get("storage", {}).get("capacity_gb")
        add("Storage", float(value) >= profile.storage_gb_min if value is not None else None, f"Detected: {value or 'N/A'} GB", {"expected_min_gb": profile.storage_gb_min, "detected_gb": value})
    if profile.display_resolution:
        value = results.get("display", {}).get("resolution")
        add("Display", value == profile.display_resolution if value else None, f"Detected: {value or 'N/A'}", {"expected": profile.display_resolution, "detected": value})
    if profile.refresh_rate_hz_min is not None:
        value = results.get("display", {}).get("refresh_rate_hz")
        add("Refresh rate", float(value) >= profile.refresh_rate_hz_min if value is not None else None, f"Detected: {value or 'N/A'} Hz", {"expected_min_hz": profile.refresh_rate_hz_min, "detected_hz": value})
    return checks


def calculate_score(checks: list[CheckResult], results: dict[str, Any] | None = None) -> tuple[int, Status, list[str]]:
    """Return score, overall status, and actionable reasons."""
    if not checks:
        return 0, Status.NOT_AVAILABLE, ["No diagnostic checks completed"]
    failed = [check for check in checks if check.status is Status.FAIL]
    unavailable = [check for check in checks if check.status is Status.NOT_AVAILABLE]
    passed = [check for check in checks if check.status is Status.PASS]
    score = round(100 * len(passed) / len(checks))
    reasons = [f"{check.name}: {check.summary}" for check in failed]
    if failed:
        return score, Status.FAIL, reasons
    if unavailable or any(check.status is Status.WARNING for check in checks):
        return score, Status.WARNING, [f"{check.name} requires review" for check in unavailable]
    return score, Status.PASS, []
