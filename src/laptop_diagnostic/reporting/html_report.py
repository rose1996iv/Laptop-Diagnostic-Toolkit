"""Self-contained HTML report export."""

from __future__ import annotations

import html
import json
from pathlib import Path

from ..core.models import DiagnosticReport
from .json_report import report_data


def write_html_report(report: DiagnosticReport, path: Path, *, include_serial: bool = False, include_hostname: bool = False, include_ip: bool = False) -> None:
    """Write an offline report suitable for sharing or printing."""
    data = report_data(report, include_serial=include_serial, include_hostname=include_hostname, include_ip=include_ip)
    rows = "".join(f"<tr><th>{html.escape(check['name'])}</th><td class='{check['status'].lower().replace(' ', '-')}'>{html.escape(check['status'])}</td><td>{html.escape(check['summary'])}</td></tr>" for check in data["checks"])
    body = f"<!doctype html><html><head><meta charset='utf-8'><title>Laptop Diagnostic Report</title><style>body{{font:15px Segoe UI,Arial;margin:2rem;color:#17202a}}table{{border-collapse:collapse;width:100%}}th,td{{border-bottom:1px solid #d7dee5;padding:.7rem;text-align:left}}.pass{{color:#147d4c}}.fail{{color:#b42318}}.warning{{color:#9a6700}}.not-available{{color:#667085}}footer{{margin-top:2rem;padding-top:1rem;border-top:1px solid #d7dee5;text-align:center;color:#667085;font-size:.9rem}}</style></head><body><h1>Laptop Diagnostic Report</h1><p>{html.escape(data['timestamp'])} | Score: <strong>{data['score']}/100</strong> | {html.escape(data['overall_status'])}</p><table><tr><th>Check</th><th>Status</th><th>Summary</th></tr>{rows}</table><h2>Details</h2><pre>{html.escape(json.dumps(data['results'], indent=2, default=str))}</pre><footer>Code &amp; Designed by Joseph (PhD Scholar)</footer></body></html>"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
