"""Eval: structural assertions on scored listing output.

These tests verify that the data structure produced by /score-job (and saved to
data/processed_listings.yaml) conforms to the pipeline schema:
- All required fields are present on every listing
- Score ranges are valid (0-10)
- Status values are valid pipeline states
- Data types are correct

These are golden-set evals — no live API calls.
"""

from datetime import date

import pytest
import yaml

from src.models import ListingSource, ListingStatus, ScoredListing


VALID_STATUSES = {s.value for s in ListingStatus}
VALID_SOURCES = {s.value for s in ListingSource}

REQUIRED_FIELDS = [
    "url",
    "source",
    "date_added",
    "date_scored",
    "company_name",
    "role_title",
    "skills_fit",
    "preference_fit",
    "skills_reasoning",
    "preference_reasoning",
    "status",
    "prepared",
]


@pytest.fixture
def golden_listings(golden_listings_path):
    """Load the golden processed_listings.yaml fixture."""
    with open(golden_listings_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("listings", [])


class TestRequiredFields:
    """Every scored listing must have all required pipeline fields."""

    def test_listings_exist(self, golden_listings):
        assert len(golden_listings) > 0, "Golden fixture must have at least one listing"

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_all_listings_have_required_field(self, golden_listings, field):
        for listing in golden_listings:
            assert field in listing, (
                f"Listing for '{listing.get('company_name', 'unknown')}' "
                f"is missing required field: '{field}'"
            )


class TestScoreRanges:
    """skills_fit and preference_fit must be integers in [0, 10]."""

    def test_skills_fit_in_range(self, golden_listings):
        for listing in golden_listings:
            score = listing["skills_fit"]
            assert isinstance(score, int), f"skills_fit must be int, got {type(score)}"
            assert 0 <= score <= 10, (
                f"skills_fit={score} out of range for '{listing['company_name']}'"
            )

    def test_preference_fit_in_range(self, golden_listings):
        for listing in golden_listings:
            score = listing["preference_fit"]
            assert isinstance(score, int), f"preference_fit must be int, got {type(score)}"
            assert 0 <= score <= 10, (
                f"preference_fit={score} out of range for '{listing['company_name']}'"
            )


class TestStatusValues:
    """status must be a valid ListingStatus enum value."""

    def test_all_statuses_are_valid(self, golden_listings):
        for listing in golden_listings:
            status = listing["status"]
            assert status in VALID_STATUSES, (
                f"Invalid status '{status}' for '{listing['company_name']}'. "
                f"Valid values: {sorted(VALID_STATUSES)}"
            )

    def test_source_values_are_valid(self, golden_listings):
        for listing in golden_listings:
            source = listing["source"]
            assert source in VALID_SOURCES, (
                f"Invalid source '{source}' for '{listing['company_name']}'. "
                f"Valid values: {sorted(VALID_SOURCES)}"
            )


class TestDataTypes:
    """Type assertions for pipeline-critical fields."""

    def test_prepared_is_boolean(self, golden_listings):
        for listing in golden_listings:
            assert isinstance(listing["prepared"], bool), (
                f"'prepared' must be bool for '{listing['company_name']}'"
            )

    def test_digested_is_boolean(self, golden_listings):
        for listing in golden_listings:
            if "digested" in listing:
                assert isinstance(listing["digested"], bool), (
                    f"'digested' must be bool for '{listing['company_name']}'"
                )

    def test_url_is_string(self, golden_listings):
        for listing in golden_listings:
            assert isinstance(listing["url"], str)
            assert listing["url"].startswith("http"), (
                f"URL must start with http: {listing['url']}"
            )

    def test_concerns_is_list_when_present(self, golden_listings):
        for listing in golden_listings:
            if "concerns" in listing and listing["concerns"] is not None:
                assert isinstance(listing["concerns"], list)

    def test_strengths_is_list_when_present(self, golden_listings):
        for listing in golden_listings:
            if "strengths" in listing and listing["strengths"] is not None:
                assert isinstance(listing["strengths"], list)


class TestScoredListingModel:
    """ScoredListing Pydantic model validates golden fixture data correctly."""

    def test_strong_match_parses(self, golden_listings):
        """The first golden listing (strong match) must parse into ScoredListing."""
        strong = next(l for l in golden_listings if l["status"] == "scored")
        listing = ScoredListing(**strong)
        assert listing.skills_fit >= 7
        assert listing.fit_assessment == "strong"

    def test_skipped_listing_parses(self, golden_listings):
        """A skipped listing must parse cleanly."""
        skipped = next(l for l in golden_listings if l["status"] == "skipped")
        listing = ScoredListing(**skipped)
        assert listing.status == ListingStatus.SKIPPED
        assert listing.prepared is False

    def test_fit_assessment_derived_correctly(self):
        """fit_assessment must be derived from scores when not explicitly set."""
        listing = ScoredListing(
            url="https://example.com/job",
            source=ListingSource.INDEED,
            date_added=date.today(),
            company_name="TestCo",
            role_title="Manager",
            skills_fit=8,
            preference_fit=7,
            skills_reasoning="Good fit",
            preference_reasoning="Good company",
        )
        assert listing.fit_assessment == "strong"

    def test_weak_fit_assessment(self):
        listing = ScoredListing(
            url="https://example.com/job2",
            source=ListingSource.INDEED,
            date_added=date.today(),
            company_name="WeakCo",
            role_title="Manager",
            skills_fit=3,
            preference_fit=2,
            skills_reasoning="Poor fit",
            preference_reasoning="Wrong type",
        )
        assert listing.fit_assessment == "weak"


class TestFitAssessmentLabels:
    """Assessment labels from /score-job must map to correct score ranges."""

    @pytest.mark.parametrize(
        "skills_fit, preference_fit, expected_assessment",
        [
            (9, 9, "strong"),
            (6, 7, "strong"),   # exactly at dual threshold (sf>=6, pf>=7)
            (7, 6, "moderate"), # skills_fit fine but pf below preference threshold
            (5, 5, "moderate"), # both at moderate minimum (sf>=5, pf>=5)
            (3, 3, "weak"),
            (0, 0, "weak"),
        ],
    )
    def test_assessment_label(self, skills_fit, preference_fit, expected_assessment):
        listing = ScoredListing(
            url="https://example.com",
            source=ListingSource.OTHER,
            date_added=date.today(),
            company_name="Co",
            role_title="Role",
            skills_fit=skills_fit,
            preference_fit=preference_fit,
            skills_reasoning="r",
            preference_reasoning="r",
        )
        assert listing.fit_assessment == expected_assessment
