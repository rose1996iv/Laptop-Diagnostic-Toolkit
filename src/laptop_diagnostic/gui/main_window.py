"""Responsive PySide6 dashboard with a worker-thread scan."""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path
from . import __name__ as _gui_package
from ..collectors.battery import collect_battery
from ..collectors.display import collect_display
from ..collectors.gpu import collect_gpus, nvidia_telemetry
from ..collectors.storage import collect_storage
from ..collectors.system import collect_cpu, collect_ram, collect_system
from ..core.models import DiagnosticReport, ExpectedProfile
from ..main import diagnostic_report
from ..profiles.loader import ProfileError, load_profile
from ..reporting.html_report import write_html_report
from ..reporting.json_report import write_json_report
from ..version import __version__

try:
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
    from PySide6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QPushButton, QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
except ImportError as exc:
    raise RuntimeError("Install requirements.txt to use the desktop GUI.") from exc

class Signals(QObject):
    progress = Signal(int, str)
    complete = Signal(object)
    failed = Signal(str)

class ScanWorker(QRunnable):
    def __init__(self, complete: bool, profile: ExpectedProfile | None):
        super().__init__(); self.complete_mode = complete; self.profile = profile; self.signals = Signals()

    @Slot()
    def run(self):
        try:
            self.signals.progress.emit(10, "Collecting hardware")
            report = diagnostic_report(self.profile, complete=self.complete_mode)
            self.signals.progress.emit(100, "Complete")
            self.signals.complete.emit(report)
        except Exception as exc: self.signals.failed.emit(str(exc))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f"Laptop Diagnostic Toolkit {__version__}"); self.resize(1000, 700); self.pool = QThreadPool.globalInstance(); self.report = None; self.profile = None; self._build()

    def _build(self):
        root = QWidget(); self.setCentralWidget(root); layout = QVBoxLayout(root)
        title = QLabel("Laptop Diagnostic Toolkit\nWindows Hardware & Performance Validator"); title.setStyleSheet("font-size:22px;font-weight:700;color:#17324d;padding:8px"); layout.addWidget(title)
        actions = QHBoxLayout(); self.run_button = QPushButton("RUN COMPLETE TEST"); self.run_button.clicked.connect(lambda: self.start_scan(True)); actions.addWidget(self.run_button); quick = QPushButton("Quick Scan"); quick.clicked.connect(lambda: self.start_scan(False)); actions.addWidget(quick); profile_button = QPushButton("Load Seller Profile"); profile_button.clicked.connect(self.load_profile); actions.addWidget(profile_button); self.json_button = QPushButton("Export JSON"); self.json_button.clicked.connect(self.export_json); self.json_button.setEnabled(False); actions.addWidget(self.json_button); self.html_button = QPushButton("Export HTML"); self.html_button.clicked.connect(self.export_html); self.html_button.setEnabled(False); actions.addWidget(self.html_button); layout.addLayout(actions)
        self.progress = QProgressBar(); layout.addWidget(self.progress); self.status = QLabel("Ready. Diagnostics are read-only; benchmark actions are bounded."); layout.addWidget(self.status)
        self.table = QTableWidget(0, 3); self.table.setHorizontalHeaderLabels(["Check", "Status", "Summary"]); self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table)

    def start_scan(self, complete: bool):
        self.run_button.setEnabled(False); worker = ScanWorker(complete, self.profile); worker.signals.progress.connect(lambda value, label: (self.progress.setValue(value), self.status.setText(label))); worker.signals.complete.connect(self.scan_complete); worker.signals.failed.connect(self.scan_failed); self.pool.start(worker)

    @Slot(object)
    def scan_complete(self, payload):
        self.report = payload; self.table.setRowCount(0)
        for check in self.report.checks:
            row = self.table.rowCount(); self.table.insertRow(row)
            for column, value in enumerate((check.name, check.status.value, check.summary)): self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.status.setText(f"Complete: {self.report.overall_status.value}. Score {self.report.score}/100. Review unavailable sensors before deciding."); self.run_button.setEnabled(True); self.json_button.setEnabled(True); self.html_button.setEnabled(True)

    def scan_failed(self, message: str): self.status.setText(f"Scan error: {message}"); self.run_button.setEnabled(True)
    def load_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Seller Profile", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.profile = load_profile(path)
            self.status.setText(f"Seller profile loaded: {self.profile.name}")
        except ProfileError as exc:
            self.status.setText(f"Profile error: {exc}")
    def export_json(self):
        if self.report:
            path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "laptop-diagnostic-report.json", "JSON (*.json)")
            if path: write_json_report(self.report, Path(path))
    def export_html(self):
        if self.report:
            path, _ = QFileDialog.getSaveFileName(self, "Export HTML", "laptop-diagnostic-report.html", "HTML (*.html)")
            if path: write_html_report(self.report, Path(path))

def run_gui() -> int:
    app = QApplication(sys.argv); window = MainWindow(); window.show(); return app.exec()
