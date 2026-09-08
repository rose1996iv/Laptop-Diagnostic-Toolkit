"""Load data-only seller specification profiles safely."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.models import ExpectedProfile


class ProfileError(ValueError):
    """Raised when a seller profile cannot be loaded or validated."""


def load_profile(path: str | Path) -> ExpectedProfile:
    """Load one JSON profile without executing any profile content."""
    profile_path = Path(path)
    try:
        data: Any = json.loads(profile_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProfileError(f"Cannot read profile: {profile_path}") from exc
    except json.JSONDecodeError as exc:
        raise ProfileError(f"Profile is not valid JSON: {profile_path}") from exc
    if not isinstance(data, dict):
        raise ProfileError("Profile root must be a JSON object")
    return ExpectedProfile.from_dict(data)


def discover_profiles(directory: str | Path) -> list[Path]:
    """Return JSON profiles in a directory in deterministic order."""
    profile_dir = Path(directory)
    return sorted(profile_dir.glob("*.json")) if profile_dir.is_dir() else []
