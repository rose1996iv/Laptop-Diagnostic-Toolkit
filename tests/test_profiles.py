import json

import pytest

from laptop_diagnostic.core.models import ExpectedProfile
from laptop_diagnostic.profiles.loader import ProfileError, discover_profiles, load_profile


def test_profile_loader_and_discovery(tmp_path):
    profile_path = tmp_path / "seller.json"
    profile_path.write_text(json.dumps({"name": "Store laptop", "gpu_contains_any": "Radeon", "price": 79999}), encoding="utf-8")
    profile = load_profile(profile_path)
    assert isinstance(profile, ExpectedProfile)
    assert profile.gpu_contains_any == ["Radeon"]
    assert profile.price == 79999
    assert discover_profiles(tmp_path) == [profile_path]


def test_profile_loader_rejects_malformed_json(tmp_path):
    profile_path = tmp_path / "broken.json"
    profile_path.write_text("not-json", encoding="utf-8")
    with pytest.raises(ProfileError):
        load_profile(profile_path)