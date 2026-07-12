"""Tests for models.py — dual-axis thresholds, fit assessment, profile round-trip."""

import pytest
import yaml
from pydantic import ValidationError

from src.models import (
    ListingInput,
    ListingSource,
    ScoredListing,
    ScoringRubric,
    ScoringThreshold,
    UserProfile,
)


def _scored(sf: int, pf: int) -> ScoredListing:
    return ScoredListing(
        url="https://example.com/job",
        source=ListingSource.OTHER,
        date_added="2026-07-01",
        company_name="Loopwork",
        role_title="Manager",
        skills_fit=sf,
        preference_fit=pf,
        skills_reasoning="r",
        preference_reasoning="r",
    )


class TestScoringThresholdBoundaries:
    """Both axes must be met — boundary behavior for BOTH threshold methods."""

    def test_prep_threshold_boundaries(self):
        r = ScoringRubric()  # defaults: skills 6, preference 7
        assert r.is_above_prep_threshold(6, 7) is True
        assert r.is_above_prep_threshold(5, 7) is False
        assert r.is_above_prep_threshold(6, 6) is False
        assert r.is_above_prep_threshold(10, 0) is False
        assert r.is_above_prep_threshold(0, 10) is False

    def test_coaching_threshold_boundaries(self):
        r = ScoringRubric()
        assert r.is_above_coaching_threshold(6, 7) is True
        assert r.is_above_coaching_threshold(5, 7) is False
        assert r.is_above_coaching_threshold(6, 6) is False

    def test_custom_thresholds_respected(self):
        r = ScoringRubric(
            threshold_for_preparation=ScoringThreshold(skills_fit_min=9, preference_fit_min=3)
        )
        assert r.is_above_prep_threshold(9, 3) is True
        assert r.is_above_prep_threshold(8, 10) is False


class TestDeriveFitAssessment:
    def test_strong(self):
        assert _scored(6, 7).fit_assessment == "strong"

    def test_moderate(self):
        assert _scored(5, 5).fit_assessment == "moderate"

    def test_weak(self):
        assert _scored(4, 4).fit_assessment == "weak"

    def test_strong_skills_weak_preference_is_not_strong(self):
        assert _scored(10, 5).fit_assessment == "moderate"


class TestUserProfileRoundTrip:
    def test_from_profile_yaml(self, tmp_path):
        p = tmp_path / "profile.yaml"
        data = {
            "schema_version": "1.0",
            "name": "Maya Rodriguez",
            "target_roles": ["Marketing Manager"],
            "seniority": "Senior",
            "location": "Singapore",
        }
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(data, f)

        profile = UserProfile.from_profile_yaml(p)
        assert profile.name == "Maya Rodriguez"
        assert profile.linkedin == {}  # optional field defaults to empty dict

    def test_missing_required_field_raises(self, tmp_path):
        p = tmp_path / "profile.yaml"
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump({"name": "Maya Rodriguez"}, f)
        with pytest.raises(ValidationError):
            UserProfile.from_profile_yaml(p)


class TestListingInput:
    def test_defaults(self):
        listing = ListingInput(url="https://example.com/job")
        assert listing.source == ListingSource.OTHER
        assert listing.status.value == "queued"
        assert listing.prefetched_text is None
