"""Best-effort local network inventory with optional connectivity checks."""

from __future__ import annotations

import socket
from typing import Any

import psutil

from ..utils.command import run_command


def collect_network(*, check_internet: bool = False) -> dict[str, Any]:
    """Collect adapters and local addresses without requiring internet access."""
    adapters = []
    for name, addresses in psutil.net_if_addrs().items():
        entries = []
        for address in addresses:
            if address.family in (socket.AF_INET, socket.AF_INET6):
                entries.append({"address": address.address, "netmask": address.netmask, "broadcast": address.broadcast})
        adapters.append({"name": name, "addresses": entries, "up": bool(psutil.net_if_stats().get(name) and psutil.net_if_stats()[name].isup)})
    result: dict[str, Any] = {"adapters": adapters, "hostname": socket.gethostname(), "internet_checked": check_internet, "internet_reachable": None, "latency_ms": None}
    if check_internet:
        code, output, _ = run_command(["ping", "-n", "1", "-w", "1000", "1.1.1.1"], 3)
        result["internet_reachable"] = code == 0
        for token in output.split():
            if token.lower().startswith("time="):
                try:
                    result["latency_ms"] = float(token.split("=", 1)[1].removesuffix("ms"))
                except ValueError:
                    pass
                break
    return result
