# Testing

Run the platform-independent suite with:

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 -m pytest -q
```

Windows-only sensor behavior is mocked or treated as unavailable. Manual validation should include an NVIDIA laptop, a machine without NVIDIA tools, a laptop without a battery, and an offline machine.
