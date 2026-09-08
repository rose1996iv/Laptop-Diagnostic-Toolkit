"""GPU detection and optional NVIDIA telemetry."""

from __future__ import annotations

import shutil
import csv
from io import StringIO
from typing import Any

from ..utils.command import powershell_json, run_command


def collect_gpus() -> list[dict[str, Any]]:
    """Detect GPUs using WMI, with no dependency on NVIDIA tooling."""
    raw = powershell_json("Get-CimInstance Win32_VideoController | Select Name,AdapterCompatibility,AdapterRAM,DriverVersion,DriverDate,VideoModeDescription,PNPDeviceID | ConvertTo-Json -Compress")
    items = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        vram = item.get("AdapterRAM")
        name = str(item.get("Name") or "")
        vendor_text = f"{item.get('AdapterCompatibility') or ''} {name}".casefold()
        vendor = "NVIDIA" if "nvidia" in vendor_text else "AMD" if "amd" in vendor_text or "radeon" in vendor_text else "Intel" if "intel" in vendor_text else "Unknown"
        dedicated = vendor == "NVIDIA" or (isinstance(vram, (int, float)) and vram >= 2 * 1024**3 and "integrated" not in name.casefold())
        result.append({"name": item.get("Name"), "vendor": vendor, "kind": "dedicated" if dedicated else "integrated_or_shared", "dedicated_vram_gb": round(vram / 1024**3, 2) if dedicated and isinstance(vram, (int, float)) and vram > 0 else None, "driver_version": item.get("DriverVersion"), "driver_date": item.get("DriverDate"), "mode": item.get("VideoModeDescription"), "pnp_id": item.get("PNPDeviceID")})
    return result


def nvidia_telemetry() -> list[dict[str, Any]]:
    """Read NVML-equivalent telemetry through nvidia-smi when present."""
    if shutil.which("nvidia-smi") is None:
        return []
    query = "name,driver_version,memory.total,memory.used,temperature.gpu,utilization.gpu,clocks.gr"
    code, output, _ = run_command(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"], 10)
    if code != 0:
        return []
    telemetry = []
    for row in csv.reader(StringIO(output)):
        parts = [part.strip() for part in row]
        if len(parts) >= 7:
            def number(value: str) -> float | None:
                try:
                    return float(value)
                except ValueError:
                    return None
            telemetry.append({"name": parts[0], "driver_version": parts[1], "dedicated_vram_mb": number(parts[2]), "memory_used_mb": number(parts[3]), "temperature_c": number(parts[4]), "utilization_pct": number(parts[5]), "clock_mhz": number(parts[6])})
    return telemetry
