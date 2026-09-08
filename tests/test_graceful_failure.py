from laptop_diagnostic.collectors.gpu import collect_gpus, nvidia_telemetry
from laptop_diagnostic.utils.command import powershell_json

def test_missing_nvidia_tool_is_empty(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert nvidia_telemetry() == []

def test_invalid_powershell_json_is_none(monkeypatch):
    monkeypatch.setattr("laptop_diagnostic.utils.command.shutil.which", lambda name: "powershell")
    monkeypatch.setattr("laptop_diagnostic.utils.command.run_command", lambda *args, **kwargs: (0, "not-json", ""))
    assert powershell_json("Get-CimInstance") is None


def test_gpu_collection_classifies_multiple_vendors(monkeypatch):
    monkeypatch.setattr("laptop_diagnostic.collectors.gpu.powershell_json", lambda script: [{"Name": "Intel Graphics", "AdapterCompatibility": "Intel", "AdapterRAM": 512 * 1024**2}, {"Name": "AMD Radeon", "AdapterCompatibility": "AMD", "AdapterRAM": 8 * 1024**3}])
    gpus = collect_gpus()
    assert [gpu["vendor"] for gpu in gpus] == ["Intel", "AMD"]
    assert gpus[1]["kind"] == "dedicated"
