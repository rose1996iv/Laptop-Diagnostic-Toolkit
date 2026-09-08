# Testing

Run the full platform-independent suite from the repository root with:

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 -m pytest -q
```

The suite covers profile loading, malformed profiles, multi-GPU comparison, VRAM mismatches, battery calculations, privacy-safe reports, purchase/value helpers, and graceful missing-tool behavior.

Windows-only sensor behavior is mocked or treated as unavailable. Manual validation should include an NVIDIA, AMD, Intel-only, and generic laptop; a machine without NVIDIA tools; a laptop without a battery; an offline machine; and a laptop with multiple displays or drives.

Build the portable Windows executable with:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name LaptopDiagnostic app.py
```
