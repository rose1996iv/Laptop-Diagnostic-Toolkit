# Laptop Diagnostic Toolkit

Portable Windows diagnostic toolkit for checking a laptop before purchase. Designed for in-store testing of CPU, RAM, GPU, VRAM, SSD, display refresh rate, battery, Wi-Fi and Windows health.

## One-click workflow

1. Download the latest EXE from GitHub Releases.
2. Right-click → **Run as administrator** (recommended, but not strictly required for every test).
3. Click **RUN COMPLETE TEST**.
4. Let it finish (typically 2–4 minutes depending on the SSD and GPU/D3D test).
5. Save both **HTML** and **JSON** reports.
6. For a gaming/CAD laptop, confirm that the exact NVIDIA GPU and VRAM match the listing.

## Tests included

- Exact Windows model, serial, BIOS, CPU cores/threads, RAM and OS
- GPU enumeration and VRAM from Windows WMI
- NVIDIA telemetry when `nvidia-smi` is available
- Windows built-in Direct3D validation via `winsat d3d`
- CPU bounded quick benchmark (not a scientific CPU benchmark)
- Temporary SSD sequential write/read benchmark (256 MB)
- Display resolution + refresh-rate detection (e.g. 144 Hz)
- Battery information when available
- Wi-Fi adapter information + 4-packet latency check to cloudflare.com
- DISM `/CheckHealth`
- Overall score + issues/warnings
- HTML and JSON report export

## Important limitations

This is a **purchase-side sanity/verification tool**, not a laboratory benchmark. It does not replace 3DMark, HWInfo, CrystalDiskInfo or vendor diagnostics for formal testing. Temperature values are shown when Windows/NVIDIA telemetry exposes them; some laptops do not expose CPU temperature through built-in WMI.

The disk test creates and deletes a temporary 256 MB file. The GPU test does not intentionally run a long-duration burn-in; it performs telemetry sampling and a Windows D3D assessment.

## Build locally

Windows + Python 3.11+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app\laptop_diagnostic.py
```

Build EXE:

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name LaptopDiagnostic app\laptop_diagnostic.py
```

The EXE will be created in `dist\LaptopDiagnostic.exe`.

## GitHub Actions

The repository includes a Windows CI workflow that builds the EXE on `windows-latest` and publishes it as a workflow artifact when run manually or on a release tag.
