"""Eval: structural assertions on profile schema.

These tests verify that:
- A complete profile produced by /setup passes validation without errors
- Required fields are enforced
- Anti-fabrication anchors (certifications) are always lists
- Scoring thresholds and dimensions are properly structured
- feedback_directness is in the valid 1-5 range

These are golden-set evals — no live API calls, no mocking.
"""

import pytest
import yaml

from src.models import ScoringRubric, UserProfile
from src.profile import CURRENT_SCHEMA_VERSION, ProfileError, load_profile


class TestCompleteProfileLoads:
    """A complete profile fixture must load without errors."""

    def test_load_returns_profile_and_rubric(self, profile_config_dir):
        profile, rubric = load_profile(profile_config_dir)
        assert isinstance(profile, UserProfile)
        assert isinstance(rubric, ScoringRubric)

    def test_name_is_populated(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert profile.name == "Alex Rivera"

    def test_target_roles_is_list(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert isinstance(profile.target_roles, list)
        assert len(profile.target_roles) >= 1

    def test_location_is_populated(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert profile.location

    def test_seniority_is_populated(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert profile.seniority


class TestAntiFabricationAnchors:
    """certifications must always be an explicit list — never missing or null."""

    def test_certifications_is_list(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert isinstance(profile.certifications, list)

    def test_certifications_contents_are_strings(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        for cert in profile.certifications:
            assert isinstance(cert, str), f"Certification must be a string, got: {type(cert)}"

    def test_profile_without_certifications_field_defaults_to_empty_list(self, minimal_profile_config_dir):
        """certifications field may be absent in minimal profiles — must default to []."""
        profile, _ = load_profile(minimal_profile_config_dir)
        assert isinstance(profile.certifications, list)


class TestFeedbackDirectness:
    """feedback_directness must be an integer in [1, 5]."""

    def test_feedback_directness_in_range(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert 1 <= profile.feedback_directness <= 5

    def test_feedback_directness_is_integer(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert isinstance(profile.feedback_directness, int)


class TestScoringThresholds:
    """Scoring thresholds are dual-axis ScoringThreshold objects with skills_fit_min and preference_fit_min."""

    def test_threshold_for_preparation_present(self, profile_config_dir):
        from src.models import ScoringThreshold
        _, rubric = load_profile(profile_config_dir)
        assert isinstance(rubric.threshold_for_preparation, ScoringThreshold)

    def test_threshold_for_coaching_present(self, profile_config_dir):
        from src.models import ScoringThreshold
        _, rubric = load_profile(profile_config_dir)
        assert isinstance(rubric.threshold_for_coaching, ScoringThreshold)

    def test_is_above_prep_threshold(self, profile_config_dir):
        _, rubric = load_profile(profile_config_dir)
        sf_min = rubric.threshold_for_preparation.skills_fit_min
        pf_min = rubric.threshold_for_preparation.preference_fit_min
        # Both at threshold — should pass
        assert rubric.is_above_prep_threshold(sf_min, pf_min) is True
        # skills_fit just below threshold
        assert rubric.is_above_prep_threshold(sf_min - 1, pf_min) is False
        # preference_fit just below threshold
        assert rubric.is_above_prep_threshold(sf_min, pf_min - 1) is False

    def test_is_above_coaching_threshold(self, profile_config_dir):
        _, rubric = load_profile(profile_config_dir)
        sf_min = rubric.threshold_for_coaching.skills_fit_min
        pf_min = rubric.threshold_for_coaching.preference_fit_min
        assert rubric.is_above_coaching_threshold(sf_min, pf_min) is True
        assert rubric.is_above_coaching_threshold(sf_min - 1, pf_min) is False


class TestScoringDimensions:
    """Scoring dimensions must have required sub-keys."""

    def test_skills_fit_dimension_present(self, profile_config_dir):
        _, rubric = load_profile(profile_config_dir)
        assert "skills_fit" in rubric.dimensions

    def test_preference_fit_dimension_present(self, profile_config_dir):
        _, rubric = load_profile(profile_config_dir)
        assert "preference_fit" in rubric.dimensions

    def test_skills_fit_has_description(self, profile_config_dir):
        _, rubric = load_profile(profile_config_dir)
        assert "description" in rubric.dimensions["skills_fit"]

    def test_skills_fit_has_components(self, profile_config_dir):
        _, rubric = load_profile(profile_config_dir)
        assert "components" in rubric.dimensions["skills_fit"]
        assert isinstance(rubric.dimensions["skills_fit"]["components"], dict)


class TestSchemaVersion:
    """Schema version must match CURRENT_SCHEMA_VERSION."""

    def test_complete_profile_has_current_schema_version(self, profile_config_dir):
        profile, _ = load_profile(profile_config_dir)
        assert profile.schema_version == CURRENT_SCHEMA_VERSION

    def test_missing_schema_version_defaults_to_current(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        # Profile without schema_version field
        (config_dir / "profile.yaml").write_text(
            'name: "No Version"\ntarget_roles: ["Dev"]\nseniority: "junior"\nlocation: "Remote"\n',
            encoding="utf-8",
        )
        # Should load fine — defaults to "1.0"
        profile, _ = load_profile(config_dir)
        assert profile.schema_version == "1.0"

    def test_old_major_version_raises_profile_error(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "profile.yaml").write_text(
            'schema_version: "0.9"\nname: "Old"\ntarget_roles: ["Dev"]\nseniority: "mid"\nlocation: "Remote"\n',
            encoding="utf-8",
        )
        with pytest.raises(ProfileError, match="older version"):
            load_profile(config_dir)


class TestMissingRequiredFields:
    """Missing required fields must raise ProfileError with actionable message."""

    @pytest.mark.parametrize("missing_field", ["name", "target_roles", "seniority", "location"])
    def test_missing_required_field_raises(self, tmp_path, missing_field):
        required = {"name": "Test", "target_roles": ["Dev"], "seniority": "mid", "location": "Remote"}
        del required[missing_field]

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        import yaml
        (config_dir / "profile.yaml").write_text(
            yaml.dump(required), encoding="utf-8"
        )

        with pytest.raises(ProfileError):
            load_profile(config_dir)

    def test_profile_not_found_raises_profile_error(self, tmp_path):
        empty_dir = tmp_path / "config"
        empty_dir.mkdir()
        with pytest.raises(ProfileError, match="/setup"):
            load_profile(empty_dir)

    def test_malformed_yaml_raises_profile_error(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "profile.yaml").write_text(
            "name: [\nbad yaml here: :\n", encoding="utf-8"
        )
        with pytest.raises(ProfileError):
            load_profile(config_dir)
