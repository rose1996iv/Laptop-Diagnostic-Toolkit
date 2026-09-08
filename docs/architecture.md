# Architecture

The application is split into collectors, safe benchmarks, core models/scoring, reporting, and the PySide6 GUI.

Collectors are best-effort and return empty or `N/A` values when Windows tools or sensors are unavailable. The GUI runs scans on a Qt worker thread so the window remains responsive. Reports are generated locally and are never uploaded.
