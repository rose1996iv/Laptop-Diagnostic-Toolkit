import json

from laptop_diagnostic.core.models import CheckResult, DiagnosticReport, Status
from laptop_diagnostic.reporting.html_report import write_html_report
from laptop_diagnostic.reporting.json_report import write_json_report


def test_reports_mask_serial_by_default(tmp_path):
    report = DiagnosticReport("now", "1.0.0", {"system": {"serial": "secret", "model": "Test"}, "storage": [{"serial": "disk-secret"}]}, [CheckResult("System", Status.PASS, "Test")], 100, Status.PASS)
    json_path = tmp_path / "report.json"; html_path = tmp_path / "report.html"
    write_json_report(report, json_path); write_html_report(report, html_path)
    assert "secret" not in json.loads(json_path.read_text()) ["results"]["system"]
    assert "disk-secret" not in json_path.read_text()
    assert "disk-secret" not in html_path.read_text()
    assert "Laptop Diagnostic Report" in html_path.read_text()
    assert "Code &amp; Designed by Joseph (PhD Scholar)" in html_path.read_text()
