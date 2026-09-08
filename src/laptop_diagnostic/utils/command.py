"""Safe subprocess helpers used by Windows collectors."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Any, Sequence

LOGGER = logging.getLogger(__name__)


def run_command(command: Sequence[str] | str, timeout: float = 20) -> tuple[int, str, str]:
    """Run a read-only command and return code, stdout, stderr."""
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, shell=isinstance(command, str), check=False)
        return completed.returncode, completed.stdout.strip(), completed.stderr.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        LOGGER.warning("Command unavailable: %s (%s)", command, exc)
        return -1, "", str(exc)


def powershell_json(script: str, timeout: float = 20) -> Any:
    """Run PowerShell and parse its JSON output, returning None on failure."""
    if shutil.which("powershell") is None:
        return None
    code, output, _ = run_command(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], timeout)
    if code != 0 or not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None
