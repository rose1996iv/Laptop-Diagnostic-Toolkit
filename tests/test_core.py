from laptop_diagnostic.benchmarks.safe import storage_benchmark
from laptop_diagnostic.collectors.battery import battery_health
from laptop_diagnostic.core.models import ExpectedProfile, Status
from laptop_diagnostic.core.scoring import calculate_score, compare_expected

def test_battery_health():
    assert battery_health(100, 95) == 95.0
    assert battery_health(None, 95) is None

def test_expected_profile_pass_and_fail():
    profile = ExpectedProfile.from_dict({"gpu_contains_any": ["RTX 3050"], "gpu_vram_gb_min": 6, "ram_gb_min": 16})
    checks = compare_expected({"gpu": {"name": "RTX 3050 Laptop GPU", "dedicated_vram_gb": 4}, "ram": {"total_gb": 16}}, profile)
    assert checks[0].status is Status.PASS
    assert checks[1].status is Status.FAIL

def test_score_has_hardware_failure_status():
    profile = ExpectedProfile(gpu_contains_any=["RTX 3050"])
    checks = compare_expected({"gpu": {"name": "Intel Graphics"}}, profile)
    score, status, reasons = calculate_score(checks)
    assert score == 0 and status is Status.FAIL and reasons

def test_storage_benchmark_is_bounded_and_returns_values():
    result = storage_benchmark(16)
    assert result["size_mb"] == 16
    assert result["read_mb_s"] > 0 and result["write_mb_s"] > 0
