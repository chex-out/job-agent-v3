"""Tests for digest.py — tier grouping, HTML rendering, pipeline marking."""

import shutil
from pathlib import Path

import pytest

from src.digest import Digest, group_by_tier
from src.utils import load_yaml, save_yaml


@pytest.fixture
def digest(tmp_path):
    """Create a Digest with a temporary data directory and real template."""
    templates = tmp_path / "templates"
    templates.mkdir()
    real_template = Path(__file__).parent.parent / "config" / "templates" / "digest_email.html"
    shutil.copy(real_template, templates / "digest_email.html")
    return Digest(data_dir=tmp_path, template_dir=templates)


@pytest.fixture
def sample_listings():
    return [
        {
            "url": "https://a.com", "company_name": "TopCo", "role_title": "Manager",
            "skills_fit": 9, "preference_fit": 8,
            "skills_reasoning": "Strong demand gen match", "preference_reasoning": "AI-native product",
            "strengths": ["AI-native"], "concerns": [], "location": "Remote", "digested": False,
        },
        {
            "url": "https://b.com", "company_name": "MidCo", "role_title": "Lead",
            "skills_fit": 7, "preference_fit": 6,
            "skills_reasoning": "Decent skills match", "preference_reasoning": "AI-powered but not core",
            "strengths": ["Remote"], "concerns": ["Gap"], "location": "Singapore", "digested": False,
        },
        {
            "url": "https://c.com", "company_name": "LowCo", "role_title": "Exec",
            "skills_fit": 4, "preference_fit": 3,
            "skills_reasoning": "Wrong seniority", "preference_reasoning": "No AI component",
            "strengths": [], "concerns": ["Wrong domain"], "location": "NYC", "digested": False,
        },
        {
            "url": "https://d.com", "company_name": "OldCo", "role_title": "Analyst",
            "skills_fit": 8, "preference_fit": 7,
            "skills_reasoning": "Strong alignment", "preference_reasoning": "AI-first SaaS",
            "strengths": ["AI focus"], "concerns": [], "location": "Remote", "digested": True,
        },
    ]


class TestGroupByTier:
    def test_groups_correctly(self, sample_listings):
        tiers = group_by_tier(sample_listings[:3])

        assert len(tiers["top_fit"]) == 1
        assert tiers["top_fit"][0]["company_name"] == "TopCo"

        assert len(tiers["watchlist"]) == 1
        assert tiers["watchlist"][0]["company_name"] == "MidCo"

        assert len(tiers["passed"]) == 1
        assert tiers["passed"][0]["company_name"] == "LowCo"

    def test_sorts_within_tiers(self):
        listings = [
            {"skills_fit": 8, "preference_fit": 7, "company_name": "A"},
            {"skills_fit": 9, "preference_fit": 9, "company_name": "B"},
            {"skills_fit": 8, "preference_fit": 8, "company_name": "C"},
        ]
        tiers = group_by_tier(listings)
        assert [l["company_name"] for l in tiers["top_fit"]] == ["B", "C", "A"]

    def test_empty_listings(self):
        tiers = group_by_tier([])
        assert tiers == {"top_fit": [], "watchlist": [], "passed": []}

    def test_custom_rubric_changes_tiering(self):
        """Tiers must follow the user's configured thresholds, not hardcoded defaults."""
        from src.models import ScoringRubric, ScoringThreshold

        strict = ScoringRubric(
            threshold_for_preparation=ScoringThreshold(skills_fit_min=9, preference_fit_min=9)
        )
        listings = [{"skills_fit": 8, "preference_fit": 8, "company_name": "A"}]
        # top_fit under defaults (6/7), but only watchlist under a 9/9 rubric
        assert group_by_tier(listings)["top_fit"] == listings
        assert group_by_tier(listings, strict)["watchlist"] == listings


class TestLoadUndigestedListings:
    def test_filters_undigested(self, digest, sample_listings):
        save_yaml(digest.data_dir / "processed_listings.yaml", {"listings": sample_listings})
        result = digest.load_undigested_listings()

        assert len(result) == 3  # OldCo is already digested
        urls = [l["url"] for l in result]
        assert "https://d.com" not in urls

    def test_empty_file(self, digest):
        save_yaml(digest.data_dir / "processed_listings.yaml", {"listings": []})
        result = digest.load_undigested_listings()
        assert result == []

    def test_missing_file(self, digest):
        result = digest.load_undigested_listings()
        assert result == []


class TestMarkDigested:
    def test_marks_sent_listings(self, digest, sample_listings):
        save_yaml(digest.data_dir / "processed_listings.yaml", {"listings": sample_listings})

        sent = [sample_listings[0], sample_listings[1]]
        digest.mark_digested(sent)

        data = load_yaml(digest.data_dir / "processed_listings.yaml")
        for listing in data["listings"]:
            if listing["url"] in ("https://a.com", "https://b.com"):
                assert listing["digested"] is True


class TestRenderDigestHtml:
    def test_renders_with_data(self, digest, sample_listings):
        tiers = group_by_tier(sample_listings[:3])
        stats = {"total": 3, "top_count": 1, "watch_count": 1, "pass_count": 1}
        html = digest.render_html(tiers, stats)

        assert "TopCo" in html
        assert "MidCo" in html
        assert "LowCo" in html
        assert "3" in html
        assert "Job Search Digest" in html

    def test_renders_empty(self, digest):
        tiers = {"top_fit": [], "watchlist": [], "passed": []}
        stats = {"total": 0, "top_count": 0, "watch_count": 0, "pass_count": 0}
        html = digest.render_html(tiers, stats)
        assert "Job Search Digest" in html
