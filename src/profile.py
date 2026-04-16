"""Profile loader and validator for the Job Seeker AI Toolkit.

Single entry point for loading config/profile.yaml. Validates required fields,
checks schema version, and returns a (UserProfile, ScoringRubric) tuple.

If required fields are missing, raises ProfileError with a user-readable message
that tells the user what to do — not what went wrong internally.
"""

from pathlib import Path
from typing import Any

import yaml

from src.models import ScoringRubric, ScoringThreshold, UserProfile

# Current schema version this code expects
CURRENT_SCHEMA_VERSION = "1.0"

# Fields required before any skill can run
_REQUIRED_FIELDS = ["name", "target_roles", "seniority", "location"]


class ProfileError(Exception):
    """Raised when the profile is missing, incomplete, or has a schema mismatch."""
    pass


def load_profile(config_dir: str | Path) -> tuple[UserProfile, ScoringRubric]:
    """Load and validate user profile from config/profile.yaml.

    Args:
        config_dir: Path to the config/ directory (repo root / "config").

    Returns:
        (UserProfile, ScoringRubric) tuple ready for use by skills.

    Raises:
        ProfileError: With a plain-English message if the profile is missing,
                      incomplete, or has a schema version mismatch.
    """
    config_dir = Path(config_dir)
    profile_path = config_dir / "profile.yaml"

    if not profile_path.exists():
        raise ProfileError(
            "Your profile hasn't been set up yet. Run /setup to get started — "
            "it takes about 5 minutes."
        )

    try:
        with open(profile_path, "r", encoding="utf-8", newline="\n") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError:
        raise ProfileError(
            "Your profile file may have been saved incorrectly. "
            "Run /setup to check and repair it."
        )

    if not isinstance(data, dict):
        raise ProfileError(
            "Your profile file appears to be empty or corrupted. "
            "Run /setup to rebuild it."
        )

    # Schema version check
    schema_version = data.get("schema_version", "1.0")
    if schema_version != CURRENT_SCHEMA_VERSION:
        major_current = int(CURRENT_SCHEMA_VERSION.split(".")[0])
        major_found = int(str(schema_version).split(".")[0])
        if major_found < major_current:
            raise ProfileError(
                f"Your profile was created with an older version (v{schema_version}). "
                "Run /setup --migrate to update it to the current format."
            )

    # Required field check
    missing = [f for f in _REQUIRED_FIELDS if not data.get(f)]
    if missing:
        missing_str = ", ".join(missing)
        raise ProfileError(
            f"Your profile is missing required information: {missing_str}. "
            "Run /setup to complete it."
        )

    # Build models
    try:
        profile = UserProfile(**data)
    except Exception as e:
        raise ProfileError(
            f"Your profile has an unexpected format issue: {e}. "
            "Run /setup to review and repair it."
        )

    # Build ScoringRubric from profile.scoring section
    scoring_data = data.get("scoring", {})

    def _build_threshold(val: Any, default_sf: int = 6, default_pf: int = 7) -> ScoringThreshold:
        """Accept int (legacy) or dict with skills_fit_min/preference_fit_min."""
        if isinstance(val, int):
            return ScoringThreshold(skills_fit_min=val, preference_fit_min=val)
        if isinstance(val, dict):
            return ScoringThreshold(
                skills_fit_min=val.get("skills_fit_min", default_sf),
                preference_fit_min=val.get("preference_fit_min", default_pf),
            )
        return ScoringThreshold(skills_fit_min=default_sf, preference_fit_min=default_pf)

    rubric = ScoringRubric(
        threshold_for_preparation=_build_threshold(
            scoring_data.get("threshold_for_preparation")
        ),
        threshold_for_coaching=_build_threshold(
            scoring_data.get("threshold_for_coaching")
        ),
        dimensions=scoring_data.get("dimensions", {}),
        deal_breaker_rules=scoring_data.get("deal_breaker_rules", []),
    )

    return profile, rubric


def validate_profile_file(profile_path: str | Path) -> list[str]:
    """Validate a profile.yaml file and return a list of issues found.

    Returns an empty list if the file is valid.
    Used by the YAML validation hook for non-blocking integrity checks.
    """
    path = Path(profile_path)
    issues = []

    if not path.exists():
        return ["File not found"]

    try:
        with open(path, "r", encoding="utf-8", newline="\n") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]

    if not isinstance(data, dict):
        return ["File is empty or not a YAML mapping"]

    for field in _REQUIRED_FIELDS:
        if not data.get(field):
            issues.append(f"Missing required field: {field}")

    return issues
