"""Tests for profile.py — load_profile, ProfileError, schema validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.profile import (
    CURRENT_SCHEMA_VERSION,
    ProfileError,
    load_profile,
    validate_profile_file,
)


def _write_profile(dir_path: Path, data: dict) -> None:
    profile = dir_path / "profile.yaml"
    with open(profile, "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(data, f)


def _minimal_profile() -> dict:
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "name": "Maya Rodriguez",
        "target_roles": ["Marketing Manager"],
        "seniority": "Senior",
        "location": "Singapore",
    }


class TestLoadProfileMissing:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ProfileError, match="hasn't been set up"):
            load_profile(tmp_path)

    def test_empty_yaml_raises(self, tmp_path):
        (tmp_path / "profile.yaml").write_text("", encoding="utf-8")
        with pytest.raises(ProfileError):
            load_profile(tmp_path)

    def test_corrupt_yaml_raises(self, tmp_path):
        (tmp_path / "profile.yaml").write_text("{{{bad yaml: [", encoding="utf-8")
        with pytest.raises(ProfileError, match="saved incorrectly"):
            load_profile(tmp_path)


class TestLoadProfileRequiredFields:
    def test_missing_name_raises(self, tmp_path):
        data = _minimal_profile()
        del data["name"]
        _write_profile(tmp_path, data)
        with pytest.raises(ProfileError, match="missing required"):
            load_profile(tmp_path)

    def test_missing_target_roles_raises(self, tmp_path):
        data = _minimal_profile()
        del data["target_roles"]
        _write_profile(tmp_path, data)
        with pytest.raises(ProfileError, match="missing required"):
            load_profile(tmp_path)

    def test_missing_seniority_raises(self, tmp_path):
        data = _minimal_profile()
        del data["seniority"]
        _write_profile(tmp_path, data)
        with pytest.raises(ProfileError, match="missing required"):
            load_profile(tmp_path)

    def test_missing_location_raises(self, tmp_path):
        data = _minimal_profile()
        del data["location"]
        _write_profile(tmp_path, data)
        with pytest.raises(ProfileError, match="missing required"):
            load_profile(tmp_path)


class TestLoadProfileSuccess:
    def test_minimal_profile_loads(self, tmp_path):
        _write_profile(tmp_path, _minimal_profile())
        profile, rubric = load_profile(tmp_path)
        assert profile.name == "Maya Rodriguez"
        assert "Marketing Manager" in profile.target_roles

    def test_returns_profile_and_rubric(self, tmp_path):
        _write_profile(tmp_path, _minimal_profile())
        result = load_profile(tmp_path)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_rubric_uses_scoring_section(self, tmp_path):
        data = _minimal_profile()
        data["scoring"] = {
            "threshold_for_preparation": 8,
            "threshold_for_coaching": 6,
        }
        _write_profile(tmp_path, data)
        _, rubric = load_profile(tmp_path)
        # Legacy int value maps to both axes equally
        assert rubric.threshold_for_preparation.skills_fit_min == 8
        assert rubric.threshold_for_preparation.preference_fit_min == 8
        assert rubric.threshold_for_coaching.skills_fit_min == 6
        assert rubric.threshold_for_coaching.preference_fit_min == 6

    def test_rubric_has_defaults_when_no_scoring(self, tmp_path):
        _write_profile(tmp_path, _minimal_profile())
        _, rubric = load_profile(tmp_path)
        # Default: skills_fit_min=6, preference_fit_min=7
        assert rubric.threshold_for_preparation.skills_fit_min == 6
        assert rubric.threshold_for_preparation.preference_fit_min == 7
        assert rubric.threshold_for_coaching.skills_fit_min == 6
        assert rubric.threshold_for_coaching.preference_fit_min == 7

    def test_rubric_accepts_dict_threshold(self, tmp_path):
        data = _minimal_profile()
        data["scoring"] = {
            "threshold_for_preparation": {
                "skills_fit_min": 5,
                "preference_fit_min": 8,
            },
        }
        _write_profile(tmp_path, data)
        _, rubric = load_profile(tmp_path)
        assert rubric.threshold_for_preparation.skills_fit_min == 5
        assert rubric.threshold_for_preparation.preference_fit_min == 8


class TestSchemaVersion:
    def test_old_major_version_raises(self, tmp_path):
        data = _minimal_profile()
        data["schema_version"] = "0.9"
        _write_profile(tmp_path, data)
        with pytest.raises(ProfileError, match="older version"):
            load_profile(tmp_path)

    def test_current_version_loads(self, tmp_path):
        data = _minimal_profile()
        data["schema_version"] = CURRENT_SCHEMA_VERSION
        _write_profile(tmp_path, data)
        profile, _ = load_profile(tmp_path)
        assert profile.name == "Maya Rodriguez"

    def test_missing_version_defaults_to_current(self, tmp_path):
        data = _minimal_profile()
        del data["schema_version"]
        _write_profile(tmp_path, data)
        # Should load without error — missing version treated as "1.0"
        profile, _ = load_profile(tmp_path)
        assert profile.name == "Maya Rodriguez"


class TestValidateProfileFile:
    def test_valid_file_returns_empty_list(self, tmp_path):
        _write_profile(tmp_path, _minimal_profile())
        issues = validate_profile_file(tmp_path / "profile.yaml")
        assert issues == []

    def test_missing_file_returns_issue(self, tmp_path):
        issues = validate_profile_file(tmp_path / "profile.yaml")
        assert len(issues) == 1
        assert "not found" in issues[0].lower()

    def test_corrupt_yaml_returns_issue(self, tmp_path):
        path = tmp_path / "profile.yaml"
        path.write_text("{{{bad:", encoding="utf-8")
        issues = validate_profile_file(path)
        assert len(issues) == 1
        assert "yaml" in issues[0].lower()

    def test_missing_required_field_returns_issue(self, tmp_path):
        data = _minimal_profile()
        del data["name"]
        _write_profile(tmp_path, data)
        issues = validate_profile_file(tmp_path / "profile.yaml")
        assert any("name" in issue for issue in issues)


class TestThresholdWrongTypes:
    """Wrong-type threshold values silently fall back to defaults — pin that
    behavior so a future change to it is deliberate, not accidental."""

    def test_string_threshold_falls_back_to_defaults(self, tmp_path):
        data = _minimal_profile()
        data["scoring"] = {"threshold_for_preparation": "high"}
        _write_profile(tmp_path, data)
        _, rubric = load_profile(tmp_path)
        assert rubric.threshold_for_preparation.skills_fit_min == 6
        assert rubric.threshold_for_preparation.preference_fit_min == 7

    def test_list_threshold_falls_back_to_defaults(self, tmp_path):
        data = _minimal_profile()
        data["scoring"] = {"threshold_for_coaching": [6, 7]}
        _write_profile(tmp_path, data)
        _, rubric = load_profile(tmp_path)
        assert rubric.threshold_for_coaching.skills_fit_min == 6
        assert rubric.threshold_for_coaching.preference_fit_min == 7
