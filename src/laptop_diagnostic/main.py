"""CLI and GUI entry point."""
from __future__ import annotations
import argparse
import json
from datetime import datetime
from .collectors.battery import collect_battery
from .collectors.display import collect_display
from .collectors.gpu import collect_gpus, nvidia_telemetry
from .collectors.storage import collect_storage
from .collectors.system import collect_cpu, collect_ram, collect_system
from .version import __version__

def collect_inventory() -> dict:
    return {"timestamp": datetime.now().astimezone().isoformat(timespec="seconds"), "version": __version__, "system": collect_system(), "cpu": collect_cpu(), "ram": collect_ram(), "gpus": collect_gpus(), "gpu_telemetry": nvidia_telemetry(), "storage": collect_storage(), "battery": collect_battery(), "display": collect_display()}

def main() -> int:
    parser = argparse.ArgumentParser(description="Offline-first Windows laptop diagnostics")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()
    if args.version:
        print(__version__); return 0
    if args.gpu:
        print(json.dumps({"gpus": collect_gpus(), "telemetry": nvidia_telemetry()}, indent=2, default=str)); return 0
    if args.quick or args.complete or args.report:
        print(json.dumps(collect_inventory(), indent=2, default=str)); return 0
    from .gui.main_window import run_gui
    return run_gui()

if __name__ == "__main__":
    raise SystemExit(main())
