import ctypes
import datetime as dt
import html
import json
import os
import platform
import re
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_NAME = "Laptop Diagnostic Toolkit"
APP_VERSION = "1.0.0"


def run_cmd(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str))
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as e:
        return -1, "", str(e)


def ps(script, timeout=20):
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script]
    return run_cmd(cmd, timeout)


def admin():
    if os.name != "nt":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def bytes_to_gib(v):
    x = safe_float(v)
    return round(x / (1024**3), 2) if x is not None else None


def now_str():
    return dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def get_system_info():
    info = {}
    _, out, _ = ps("Get-CimInstance Win32_ComputerSystem | Select Manufacturer,Model,TotalPhysicalMemory,Domain | ConvertTo-Json -Compress")
    try:
        d = json.loads(out)
        info.update({"manufacturer": d.get("Manufacturer"), "model": d.get("Model"), "ram_gib": bytes_to_gib(d.get("TotalPhysicalMemory")), "domain": d.get("Domain")})
    except Exception:
        pass
    _, out, _ = ps("Get-CimInstance Win32_BIOS | Select SerialNumber,SMBIOSBIOSVersion,ReleaseDate | ConvertTo-Json -Compress")
    try:
        d = json.loads(out)
        info.update({"serial": d.get("SerialNumber"), "bios": d.get("SMBIOSBIOSVersion"), "bios_date": str(d.get("ReleaseDate"))})
    except Exception:
        pass
    _, out, _ = ps("Get-CimInstance Win32_Processor | Select -First 1 Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | ConvertTo-Json -Compress")
    try:
        d = json.loads(out)
        info.update({"cpu": d.get("Name"), "cores": d.get("NumberOfCores"), "threads": d.get("NumberOfLogicalProcessors"), "max_mhz": d.get("MaxClockSpeed")})
    except Exception:
        pass
    _, out, _ = ps("Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber,OSArchitecture,LastBootUpTime | ConvertTo-Json -Compress")
    try:
        d = json.loads(out)
        info.update({"os": d.get("Caption"), "os_version": d.get("Version"), "build": d.get("BuildNumber"), "arch": d.get("OSArchitecture"), "last_boot": str(d.get("LastBootUpTime"))})
    except Exception:
        pass
    return info


def get_gpus():
    _, out, _ = ps("Get-CimInstance Win32_VideoController | Select Name,AdapterRAM,DriverVersion,VideoModeDescription,PNPDeviceID | ConvertTo-Json -Compress")
    try:
        d = json.loads(out)
        if isinstance(d, dict):
            d = [d]
        result = []
        for x in d:
            result.append({
                "name": x.get("Name"),
                "vram_gib": bytes_to_gib(x.get("AdapterRAM")),
                "driver": x.get("DriverVersion"),
                "mode": x.get("VideoModeDescription"),
                "pnp": x.get("PNPDeviceID"),
            })
        return result
    except Exception:
        return []


def nvidia_smi_available():
    return shutil.which("nvidia-smi") is not None


def nvidia_query():
    if not nvidia_smi_available():
        return []
    q = "name,driver_version,memory.total,memory.used,temperature.gpu,utilization.gpu,clocks.gr"
    rc, out, _ = run_cmd(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"], 10)
    if rc != 0:
        return []
    res = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 7:
            res.append({"name": parts[0], "driver": parts[1], "memory_total_mb": safe_float(parts[2]), "memory_used_mb": safe_float(parts[3]), "temp_c": safe_float(parts[4]), "util_gpu_pct": safe_float(parts[5]), "clock_mhz": safe_float(parts[6])})
    return res


def get_disks():
    script = "Get-CimInstance Win32_DiskDrive | Select Model,SerialNumber,Size,InterfaceType,Status | ConvertTo-Json -Compress"
    _, out, _ = ps(script)
    try:
        d = json.loads(out)
        if isinstance(d, dict): d = [d]
        return [{"model": x.get("Model"), "serial": x.get("SerialNumber"), "size_gib": bytes_to_gib(x.get("Size")), "interface": x.get("InterfaceType"), "status": x.get("Status")} for x in d]
    except Exception:
        return []


def get_battery():
    _, out, _ = ps("Get-CimInstance Win32_Battery | Select Name,BatteryStatus,EstimatedChargeRemaining,EstimatedRunTime,DesignVoltage | ConvertTo-Json -Compress")
    try:
        d = json.loads(out)
        if isinstance(d, dict): d = [d]
        return d
    except Exception:
        return []


def get_refresh_rates():
    _, out, _ = ps("Get-CimInstance Win32_VideoController | Select Name,CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate | ConvertTo-Json -Compress")
    try:
        d = json.loads(out)
        if isinstance(d, dict): d = [d]
        return d
    except Exception:
        return []


def check_windows_health():
    rc, out, err = run_cmd(["DISM", "/Online", "/Cleanup-Image", "/CheckHealth"], 30)
    return {"returncode": rc, "output": out or err}


def cpu_benchmark(seconds=5):
    # Small, bounded, single-process workload. It is intentionally not a lab-grade benchmark.
    start = time.perf_counter()
    ops = 0
    x = 1
    while time.perf_counter() - start < seconds:
        for _ in range(20000):
            x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
            ops += 1
    elapsed = time.perf_counter() - start
    return {"seconds": round(elapsed, 3), "ops": ops, "ops_per_sec": round(ops / elapsed)}


def disk_benchmark(size_mb=256):
    # Sequential write/read benchmark to a temporary file. Results vary by Windows cache and SSD state.
    path = Path(tempfile.gettempdir()) / f"ldt_disk_test_{os.getpid()}_{int(time.time())}.bin"
    chunk = os.urandom(4 * 1024 * 1024)
    total = size_mb * 1024 * 1024
    written = 0
    t0 = time.perf_counter()
    try:
        with open(path, "wb", buffering=0) as f:
            while written < total:
                n = min(len(chunk), total - written)
                f.write(chunk[:n])
                written += n
            f.flush()
            os.fsync(f.fileno())
        tw = max(time.perf_counter() - t0, 1e-6)
        t1 = time.perf_counter()
        read = 0
        with open(path, "rb", buffering=0) as f:
            while f.read(len(chunk)):
                read += len(chunk)
        tr = max(time.perf_counter() - t1, 1e-6)
        return {"size_mb": size_mb, "write_mb_s": round(size_mb / tw, 1), "read_mb_s": round(size_mb / tr, 1)}
    finally:
        try: path.unlink(missing_ok=True)
        except Exception: pass


def gpu_test(duration=15):
    result = {"method": "nvidia-smi monitoring", "samples": [], "winsat": None}
    if nvidia_smi_available():
        end = time.time() + duration
        while time.time() < end:
            result["samples"].append(nvidia_query())
            time.sleep(1)
        temps = []
        util = []
        for group in result["samples"]:
            for g in group:
                if g.get("temp_c") is not None: temps.append(g["temp_c"])
                if g.get("util_gpu_pct") is not None: util.append(g["util_gpu_pct"])
        result["temperature_max_c"] = max(temps) if temps else None
        result["utilization_max_pct"] = max(util) if util else None
    # Use Windows built-in D3D assessment where available.
    if shutil.which("winsat"):
        rc, out, err = run_cmd("winsat d3d -v", 45)
        result["winsat"] = {"returncode": rc, "output": (out or err)[-5000:]}
    return result


def wifi_test():
    hostname = "cloudflare.com"
    latency_ms = None
    rc, out, _ = run_cmd(["ping", "-n", "4", hostname], 15)
    m = re.search(r"Average = (\d+)ms", out, re.I)
    if m: latency_ms = int(m.group(1))
    # Connection info
    rc2, out2, _ = run_cmd(["netsh", "wlan", "show", "interfaces"], 10)
    return {"ping_host": hostname, "avg_ping_ms": latency_ms, "wifi_info": out2}


def evaluate(results):
    score = 100
    issues = []
    warnings = []
    sysi = results.get("system", {})
    if not sysi.get("model"): score -= 5; issues.append("System model could not be read")
    gpus = results.get("gpus", [])
    if not gpus: score -= 10; issues.append("No GPU information detected")
    if results.get("disk_benchmark"):
        w = results["disk_benchmark"].get("write_mb_s")
        r = results["disk_benchmark"].get("read_mb_s")
        if w is not None and w < 150: warnings.append(f"Low temporary-file write result: {w} MB/s")
        if r is not None and r < 500: warnings.append(f"Low temporary-file read result: {r} MB/s")
    gpu_test_r = results.get("gpu_test", {})
    t = gpu_test_r.get("temperature_max_c")
    if t is not None and t >= 90: score -= 15; issues.append(f"NVIDIA GPU reached {t}°C during the test")
    elif t is not None and t >= 85: score -= 7; warnings.append(f"NVIDIA GPU reached {t}°C")
    if results.get("battery") == []: warnings.append("No battery was reported (may be desktop mode or inaccessible)")
    if results.get("refresh_rates"):
        rates = [x.get("CurrentRefreshRate") for x in results["refresh_rates"] if isinstance(x, dict)]
        if 144 not in rates: warnings.append("144 Hz was not detected on the active display list")
    return {"score": max(0, min(100, score)), "issues": issues, "warnings": warnings}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("980x720")
        self.minsize(900, 650)
        self.results = {"app": APP_NAME, "version": APP_VERSION, "timestamp": now_str()}
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=12); top.pack(fill="x")
        ttk.Label(top, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(side="left")
        self.admin_label = ttk.Label(top, text=("Administrator: YES" if admin() else "Administrator: NO"), foreground=("green" if admin() else "darkorange"))
        self.admin_label.pack(side="right")

        actions = ttk.Frame(self, padding=(12, 0)); actions.pack(fill="x")
        self.start_btn = ttk.Button(actions, text="RUN COMPLETE TEST", command=self.run_complete)
        self.start_btn.pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="System Info", command=lambda: self.run_single("system", get_system_info)).pack(side="left", padx=4)
        ttk.Button(actions, text="GPU Info", command=lambda: self.run_single("gpus", get_gpus)).pack(side="left", padx=4)
        ttk.Button(actions, text="Save JSON", command=self.save_json).pack(side="right", padx=4)
        ttk.Button(actions, text="Save HTML Report", command=self.save_html).pack(side="right", padx=4)

        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=12, pady=10)

        self.status = ttk.Label(self, text="Ready. Use RUN COMPLETE TEST at the store.")
        self.status.pack(fill="x", padx=12)

        body = ttk.Frame(self, padding=12); body.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(body, columns=("value",), show="tree headings")
        self.tree.heading("#0", text="Test / Result")
        self.tree.heading("value", text="Value")
        self.tree.column("#0", width=300)
        self.tree.column("value", width=600)
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview); sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def log(self, text, value=""):
        self.tree.insert("", "end", text=text, values=(value,))

    def set_progress(self, n, msg):
        self.progress["value"] = n; self.status.config(text=msg); self.update_idletasks()

    def run_single(self, key, fn):
        self.tree.delete(*self.tree.get_children())
        try:
            val = fn(); self.results[key] = val; self.log(key, json.dumps(val, ensure_ascii=False)[:1000])
        except Exception as e:
            self.log(key, f"ERROR: {e}")

    def run_complete(self):
        self.start_btn.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        tests = [
            (8, "Collecting system / BIOS / CPU / RAM / Windows info", "system", get_system_info),
            (16, "Detecting GPU(s) and VRAM", "gpus", get_gpus),
            (25, "Reading NVIDIA telemetry", "nvidia", nvidia_query),
            (34, "Checking storage devices", "disks", get_disks),
            (43, "Checking battery", "battery", get_battery),
            (52, "Checking display resolution / refresh rate", "refresh_rates", get_refresh_rates),
            (60, "Checking Windows component health", "windows_health", check_windows_health),
            (68, "Running bounded CPU benchmark (5 sec)", "cpu_benchmark", cpu_benchmark),
            (78, "Running temporary SSD read/write benchmark", "disk_benchmark", disk_benchmark),
            (90, "Running GPU / D3D validation (up to 15 sec)", "gpu_test", gpu_test),
            (96, "Testing Wi-Fi connectivity / latency", "wifi", wifi_test),
        ]
        for n, msg, key, fn in tests:
            self.after(0, self.set_progress, n - 1, msg)
            try:
                self.results[key] = fn()
                value = self._summarize(key, self.results[key])
            except Exception as e:
                self.results[key] = {"error": str(e)}
                value = f"ERROR: {e}"
            self.after(0, self.log, key.upper(), value)
        self.results["evaluation"] = evaluate(self.results)
        self.results["timestamp"] = now_str()
        self.after(0, self._finish)

    def _summarize(self, key, v):
        if key == "system": return f"{v.get('manufacturer')} {v.get('model')} | {v.get('cpu')} | RAM {v.get('ram_gib')} GiB"
        if key == "gpus": return "; ".join(f"{x.get('name')} | VRAM {x.get('vram_gib')} GiB | Driver {x.get('driver')}" for x in v) or "None"
        if key == "nvidia": return "; ".join(f"{x.get('name')} | {x.get('memory_total_mb')} MB | Temp {x.get('temp_c')} C | Util {x.get('util_gpu_pct')}%" for x in v) or "nvidia-smi not available / no NVIDIA GPU"
        if key == "disks": return "; ".join(f"{x.get('model')} | {x.get('size_gib')} GiB | {x.get('status')}" for x in v) or "None"
        if key == "battery": return json.dumps(v, ensure_ascii=False)[:800]
        if key == "refresh_rates": return "; ".join(f"{x.get('Name')} | {x.get('CurrentHorizontalResolution')}x{x.get('CurrentVerticalResolution')} @ {x.get('CurrentRefreshRate')} Hz" for x in v)
        if key == "windows_health": return (v.get("output") or "")[-800:].replace("\n", " ")
        if key == "cpu_benchmark": return f"{v.get('ops_per_sec'):,} ops/s (bounded quick check)"
        if key == "disk_benchmark": return f"Write {v.get('write_mb_s')} MB/s | Read {v.get('read_mb_s')} MB/s"
        if key == "gpu_test": return f"Max NVIDIA Temp {v.get('temperature_max_c')} C | Max Util {v.get('utilization_max_pct')}% | D3D check: {v.get('winsat',{}).get('returncode')}"
        if key == "wifi": return f"Avg ping {v.get('avg_ping_ms')} ms to {v.get('ping_host')}"
        return json.dumps(v, ensure_ascii=False)[:800]

    def _finish(self):
        self.progress["value"] = 100
        e = self.results.get("evaluation", {})
        self.log("OVERALL SCORE", f"{e.get('score')}/100")
        if e.get("issues"): self.log("ISSUES", " | ".join(e["issues"]))
        if e.get("warnings"): self.log("WARNINGS", " | ".join(e["warnings"]))
        self.status.config(text="Complete. Save the report before leaving the store.")
        self.start_btn.config(state="normal")
        try:
            messagebox.showinfo("Test Complete", f"All tests completed. Overall score: {e.get('score')}/100\n\nSave the HTML report before leaving the store.")
        except Exception:
            pass

    def save_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="laptop-diagnostic-report.json")
        if not path: return
        Path(path).write_text(json.dumps(self.results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        messagebox.showinfo("Saved", path)

    def save_html(self):
        path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")], initialfile="laptop-diagnostic-report.html")
        if not path: return
        e = self.results.get("evaluation", {})
        rows = []
        for k, v in self.results.items():
            if k in {"app", "version", "timestamp", "evaluation"}: continue
            rows.append(f"<tr><td><b>{html.escape(k)}</b></td><td><pre>{html.escape(json.dumps(v, ensure_ascii=False, indent=2, default=str))}</pre></td></tr>")
        doc = f"""<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(APP_NAME)} Report</title><style>body{{font-family:Segoe UI,Arial;margin:32px;background:#f7f7f7}}.card{{background:#fff;padding:24px;border-radius:12px;box-shadow:0 1px 8px #ddd}}table{{width:100%;border-collapse:collapse}}td{{border-bottom:1px solid #ddd;padding:10px;vertical-align:top}}pre{{white-space:pre-wrap;max-height:420px;overflow:auto}}.score{{font-size:30px;font-weight:700}}</style></head><body><div class='card'><h1>{html.escape(APP_NAME)}</h1><p>{html.escape(str(self.results.get('timestamp')))}</p><div class='score'>Overall Score: {e.get('score')}/100</div><p><b>Issues:</b> {html.escape('; '.join(e.get('issues',[])) or 'None')}</p><p><b>Warnings:</b> {html.escape('; '.join(e.get('warnings',[])) or 'None')}</p><table>{''.join(rows)}</table></div></body></html>"""
        Path(path).write_text(doc, encoding="utf-8")
        messagebox.showinfo("Saved", path)


if __name__ == "__main__":
    if os.name != "nt":
        print("This toolkit targets Windows laptops. Run the packaged EXE on Windows.")
    app = App(); app.mainloop()
