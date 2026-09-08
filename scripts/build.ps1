$ErrorActionPreference = 'Stop'
py -3 -m pip install -r requirements.txt
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name LaptopDiagnostic app.py
Write-Host "Built dist\LaptopDiagnostic.exe"
