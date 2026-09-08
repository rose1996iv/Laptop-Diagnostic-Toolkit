"""Short, bounded, non-destructive benchmarks."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path


def cpu_benchmark(duration_seconds: float = 10) -> dict[str, float | int]:
    """Run the clearly-labelled Toolkit Quick CPU Benchmark."""
    started = time.perf_counter()
    operations = 0
    value = 1
    while time.perf_counter() - started < max(1, min(duration_seconds, 30)):
        for _ in range(20_000):
            value = (value * 1_664_525 + 1_013_904_223) & 0xFFFFFFFF
            operations += 1
    elapsed = time.perf_counter() - started
    return {"duration_seconds": round(elapsed, 3), "operations": operations, "operations_per_second": round(operations / elapsed)}


def storage_benchmark(size_mb: int = 128) -> dict[str, float | int]:
    """Measure temporary sequential I/O and always delete the temporary file."""
    size_mb = max(16, min(size_mb, 256))
    path: Path | None = None
    block = os.urandom(4 * 1024 * 1024)
    total = size_mb * 1024 * 1024
    try:
        with tempfile.NamedTemporaryFile(prefix="ldt-", suffix=".tmp", delete=False) as handle:
            path = Path(handle.name)
            started = time.perf_counter()
            remaining = total
            while remaining:
                chunk = block[: min(len(block), remaining)]
                handle.write(chunk)
                remaining -= len(chunk)
            handle.flush()
            os.fsync(handle.fileno())
            write_seconds = max(time.perf_counter() - started, 1e-6)
        started = time.perf_counter()
        with path.open("rb", buffering=0) as handle:
            while handle.read(len(block)):
                pass
        read_seconds = max(time.perf_counter() - started, 1e-6)
        return {"size_mb": size_mb, "write_mb_s": round(size_mb / write_seconds, 1), "read_mb_s": round(size_mb / read_seconds, 1)}
    finally:
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
