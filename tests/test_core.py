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
    checks_by_name = {check.name: check for check in checks}
    assert checks_by_name["GPU"].status is Status.PASS
    assert checks_by_name["Dedicated VRAM"].status is Status.FAIL


def test_expected_profile_handles_multi_device_inventory():
    profile = ExpectedProfile.from_dict({"gpu_contains_any": ["RTX"], "gpu_vram_gb_min": 6, "storage_gb_min": 512, "display_resolution": "1920x1080", "refresh_rate_hz_min": 120})
    checks = compare_expected({"gpus": [{"name": "Intel Graphics", "dedicated_vram_gb": None}, {"name": "AMD Radeon", "dedicated_vram_gb": 8}], "storage": [{"capacity_gb": 256}, {"capacity_gb": 1024}], "display": [{"resolution": "1920x1080", "refresh_rate_hz": 144}]}, profile)
    checks_by_name = {check.name: check for check in checks}
    assert checks_by_name["GPU"].status is Status.FAIL
    assert checks_by_name["Dedicated VRAM"].status is Status.PASS
    assert checks_by_name["Storage"].status is Status.PASS
    assert checks_by_name["Display"].status is Status.PASS
    assert checks_by_name["Refresh rate"].status is Status.PASS

def test_score_has_hardware_failure_status():
    profile = ExpectedProfile(gpu_contains_any=["RTX 3050"])
    checks = compare_expected({"gpu": {"name": "Intel Graphics"}}, profile)
    score, status, reasons = calculate_score(checks)
    assert score == 0 and status is Status.FAIL and reasons

def test_storage_benchmark_is_bounded_and_returns_values():
    result = storage_benchmark(16)
    assert result["size_mb"] == 16
    assert result["read_mb_s"] > 0 and result["write_mb_s"] > 0
