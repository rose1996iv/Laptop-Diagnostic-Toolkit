# Architecture

The shipped application is the modular `src/laptop_diagnostic` package launched by `app.py`. It is split into Windows collectors, bounded benchmarks, core models/scoring/decision helpers, optional JSON seller profiles, privacy-aware reporting, and the PySide6 GUI.

`diagnostic_report()` is the shared orchestration path for CLI and GUI scans. Profiles are data-only and never activate automatically from detected manufacturer or model. Collectors are best-effort and return empty or unavailable values when Windows tools or sensors are unavailable. The GUI runs scans on a Qt worker thread so the window remains responsive. Reports are generated locally and redact serials, hostnames, IP addresses, and nested disk identifiers by default.
