from laptop_diagnostic.collectors.gpu import nvidia_telemetry
from laptop_diagnostic.utils.command import powershell_json

def test_missing_nvidia_tool_is_empty(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert nvidia_telemetry() == []

def test_invalid_powershell_json_is_none(monkeypatch):
    monkeypatch.setattr("laptop_diagnostic.utils.command.shutil.which", lambda name: "powershell")
    monkeypatch.setattr("laptop_diagnostic.utils.command.run_command", lambda *args, **kwargs: (0, "not-json", ""))
    assert powershell_json("Get-CimInstance") is None
