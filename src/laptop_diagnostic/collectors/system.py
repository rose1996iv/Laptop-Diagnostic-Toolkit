"""Windows system, CPU, and memory collection."""

from __future__ import annotations

import platform
import socket
import time
from typing import Any

import psutil

from ..core.models import CheckResult, Status
from ..utils.command import powershell_json


def _one(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def collect_system() -> dict[str, Any]:
    """Collect identity and OS information without requiring administrator access."""
    computer = _one(powershell_json("Get-CimInstance Win32_ComputerSystem | Select Manufacturer,Model,Name | ConvertTo-Json -Compress"))
    bios = _one(powershell_json("Get-CimInstance Win32_BIOS | Select SerialNumber,SMBIOSBIOSVersion,ReleaseDate | ConvertTo-Json -Compress"))
    os_info = _one(powershell_json("Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber,OSArchitecture | ConvertTo-Json -Compress"))
    return {"manufacturer": computer.get("Manufacturer"), "model": computer.get("Model"), "bios": bios.get("SMBIOSBIOSVersion"), "bios_date": bios.get("ReleaseDate"), "serial": bios.get("SerialNumber"), "os": os_info.get("Caption") or platform.platform(), "os_version": os_info.get("Version"), "build": os_info.get("BuildNumber"), "architecture": os_info.get("OSArchitecture") or platform.machine(), "hostname": computer.get("Name") or socket.gethostname(), "uptime_seconds": max(0, time.time() - psutil.boot_time())}


def collect_cpu() -> dict[str, Any]:
    """Collect CPU identity and current utilization."""
    cpu = _one(powershell_json("Get-CimInstance Win32_Processor | Select -First 1 Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | ConvertTo-Json -Compress"))
    frequency = psutil.cpu_freq()
    return {"name": cpu.get("Name") or platform.processor() or "N/A", "physical_cores": cpu.get("NumberOfCores") or psutil.cpu_count(False), "logical_processors": cpu.get("NumberOfLogicalProcessors") or psutil.cpu_count(True), "max_mhz": cpu.get("MaxClockSpeed") or (frequency.max if frequency else None), "current_mhz": frequency.current if frequency else None, "utilization_pct": psutil.cpu_percent(interval=0.2)}


def collect_ram() -> dict[str, Any]:
    """Collect RAM capacity and current usage."""
    memory = psutil.virtual_memory()
    return {"total_gb": round(memory.total / 1024**3, 2), "available_gb": round(memory.available / 1024**3, 2), "used_gb": round(memory.used / 1024**3, 2), "percent": memory.percent}


def system_checks(system: dict[str, Any], cpu: dict[str, Any], ram: dict[str, Any]) -> list[CheckResult]:
    return [CheckResult("System identity", Status.PASS if system.get("model") else Status.NOT_AVAILABLE, f"{system.get('manufacturer') or ''} {system.get('model') or 'N/A'}"), CheckResult("CPU", Status.PASS if cpu.get("name") and cpu["name"] != "N/A" else Status.NOT_AVAILABLE, str(cpu.get("name") or "N/A")), CheckResult("RAM", Status.PASS if ram.get("total_gb") else Status.NOT_AVAILABLE, f"{ram.get('total_gb', 'N/A')} GB")]
