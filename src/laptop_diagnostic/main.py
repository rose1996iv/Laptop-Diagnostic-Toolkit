"""CLI and GUI entry point."""
from __future__ import annotations
import argparse
import json
from datetime import datetime
from .collectors.battery import collect_battery
from .collectors.display import collect_display
from .collectors.gpu import collect_gpus, nvidia_telemetry
from .collectors.network import collect_network
from .collectors.storage import collect_storage
from .collectors.system import collect_cpu, collect_ram, collect_system, system_checks
from .core.models import CheckResult, DiagnosticReport, ExpectedProfile, Status
from .core.scoring import calculate_score, compare_expected
from .core.decision import condition_indicators, purchase_decision
from .benchmarks.safe import cpu_benchmark, storage_benchmark
from .profiles.loader import ProfileError, load_profile
from .version import __version__

def collect_inventory(*, complete: bool = False) -> dict:
    results = {"timestamp": datetime.now().astimezone().isoformat(timespec="seconds"), "version": __version__, "system": collect_system(), "cpu": collect_cpu(), "ram": collect_ram(), "gpus": collect_gpus(), "gpu_telemetry": nvidia_telemetry(), "storage": collect_storage(), "battery": collect_battery(), "display": collect_display(), "network": collect_network()}
    if complete:
        results["benchmarks"] = {"cpu": cpu_benchmark(), "storage": storage_benchmark()}
    return results


def diagnostic_report(profile: ExpectedProfile | None = None, *, complete: bool = False) -> DiagnosticReport:
    """Collect one report using the same path for CLI and GUI callers."""
    results = collect_inventory(complete=complete)
    checks = system_checks(results["system"], results["cpu"], results["ram"])
    checks.extend([
        CheckResult("GPU", Status.PASS if results["gpus"] else Status.NOT_AVAILABLE, f"{len(results['gpus'])} GPU(s) detected"),
        CheckResult("Storage", Status.PASS if results["storage"] else Status.NOT_AVAILABLE, f"{len(results['storage'])} drive(s) detected"),
        CheckResult("Battery", Status.PASS if results["battery"].get("present") else Status.NOT_AVAILABLE, results["battery"].get("health_label", "Battery unavailable")),
        CheckResult("Display", Status.PASS if results["display"] else Status.NOT_AVAILABLE, f"{len(results['display'])} display(s) detected"),
        CheckResult("Network", Status.PASS if results["network"].get("adapters") else Status.NOT_AVAILABLE, f"{len(results['network'].get('adapters', []))} adapter(s) detected"),
    ])
    if profile is not None:
        checks.extend(compare_expected(results, profile))
    score, overall, reasons = calculate_score(checks, results)
    confidence = round(100 * sum(check.status is not Status.NOT_AVAILABLE for check in checks) / len(checks)) if checks else 0
    results["condition"] = condition_indicators()
    results["purchase_decision"] = purchase_decision(score, profile.price if profile else None, critical_failures=sum(check.status is Status.FAIL for check in checks), confidence=confidence)
    return DiagnosticReport(datetime.now().astimezone().isoformat(timespec="seconds"), __version__, results, checks, score, overall, reasons)

def main() -> int:
    parser = argparse.ArgumentParser(description="Offline-first Windows laptop diagnostics")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--profile", type=str, help="JSON seller specification profile")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()
    if args.version:
        print(__version__); return 0
    if args.gpu:
        print(json.dumps({"gpus": collect_gpus(), "telemetry": nvidia_telemetry()}, indent=2, default=str)); return 0
    if args.quick or args.complete or args.report or args.profile:
        try:
            profile = load_profile(args.profile) if args.profile else None
        except ProfileError as exc:
            parser.error(str(exc))
        report = diagnostic_report(profile, complete=args.complete)
        print(json.dumps(report.to_dict(), indent=2, default=str)); return 0
    from .gui.main_window import run_gui
    return run_gui()

if __name__ == "__main__":
    raise SystemExit(main())
