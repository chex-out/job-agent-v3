"""Tests for feedback.py — status keyword parsing and listing update logic."""

import shutil
from pathlib import Path

import pytest

from src.coach_bridge import CoachBridge
from src.feedback import apply_status_update, parse_status_update
from src.utils import load_yaml, save_yaml

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_STATE = FIXTURES / "sample_coaching_state.md"


@pytest.fixture
def bridge(tmp_path):
    """Create a CoachBridge with a copy of the sample coaching state."""
    state_file = tmp_path / "coaching_state.md"
    shutil.copy(SAMPLE_STATE, state_file)
    return CoachBridge(state_path=state_file)


@pytest.fixture
def listings_data():
    return {
        "listings": [
            {"company_name": "Anthropic", "role_title": "Marketing Manager", "status": "queued"},
            {"company_name": "Stripe", "role_title": "Lead", "status": "queued"},
            {"company_name": "Supabase", "role_title": "PMM", "status": "queued"},
        ]
    }


class TestParseStatusUpdate:
    def test_extracts_applied(self):
        updates = parse_status_update("applied Anthropic", "", ["Anthropic"])
        assert len(updates) == 1
        assert updates[0]["status"] == "applied"
        assert updates[0]["company"] == "Anthropic"
        assert updates[0]["ambiguous"] is False

    def test_extracts_from_body(self):
        updates = parse_status_update("", "interviewed Stripe today", ["Stripe"])
        assert len(updates) == 1
        assert updates[0]["status"] == "interviewed"
        assert updates[0]["company"] == "Stripe"

    def test_multiple_updates(self):
        body = "applied Anthropic\nrejected Stripe"
        updates = parse_status_update("", body, ["Anthropic", "Stripe"])
        statuses = {u["company"]: u["status"] for u in updates}
        assert statuses["Anthropic"] == "applied"
        assert statuses["Stripe"] == "rejected"

    def test_fuzzy_low_confidence_is_ambiguous(self):
        # "Stripee" should fuzzy-match Stripe but below 95% confidence
        updates = parse_status_update("applied Stripee", "", ["Stripe"])
        # Either ambiguous or no match — should not produce a confident update
        for u in updates:
            assert u.get("ambiguous") is True or u["company"] != "Stripe"

    def test_no_match_skips(self):
        updates = parse_status_update("applied UnknownCo", "", ["Anthropic", "Stripe"])
        # No confident match for UnknownCo
        assert all(u.get("ambiguous") is True for u in updates) or len(updates) == 0

    def test_empty_inputs(self):
        updates = parse_status_update("", "", ["Anthropic"])
        assert updates == []

    def test_case_insensitive(self):
        updates = parse_status_update("APPLIED anthropic", "", ["Anthropic"])
        assert len(updates) == 1
        assert updates[0]["status"] == "applied"


class TestApplyStatusUpdate:
    def test_applied_updates_listing(self, bridge, listings_data):
        update = {"company": "Anthropic", "status": "applied", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is True

        listing = next(l for l in listings_data["listings"] if l["company_name"] == "Anthropic")
        assert listing["status"] == "applied"

    def test_skip_updates_listing(self, bridge, listings_data):
        update = {"company": "Stripe", "status": "skip", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is True

        listing = next(l for l in listings_data["listings"] if l["company_name"] == "Stripe")
        assert listing["status"] == "skipped"

    def test_interviewed_updates_listing(self, bridge, listings_data):
        update = {"company": "Anthropic", "status": "interviewed", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is True

        listing = next(l for l in listings_data["listings"] if l["company_name"] == "Anthropic")
        assert listing["status"] == "interviewing"

    def test_rejected_updates_listing(self, bridge, listings_data):
        update = {"company": "Stripe", "status": "rejected", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is True

        listing = next(l for l in listings_data["listings"] if l["company_name"] == "Stripe")
        assert listing["status"] == "rejected"

    def test_offer_updates_listing(self, bridge, listings_data):
        update = {"company": "Supabase", "status": "offer", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is True

        listing = next(l for l in listings_data["listings"] if l["company_name"] == "Supabase")
        assert listing["status"] == "offer"

    def test_review_updates_listing(self, bridge, listings_data):
        update = {"company": "Anthropic", "status": "review", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is True

        listing = next(l for l in listings_data["listings"] if l["company_name"] == "Anthropic")
        assert listing["status"] == "under_review"

    def test_unknown_company_returns_false(self, bridge, listings_data):
        update = {"company": "NonExistentCo", "status": "applied", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is False

    def test_unknown_status_returns_false(self, bridge, listings_data):
        update = {"company": "Anthropic", "status": "unknown_keyword", "ambiguous": False}
        result = apply_status_update(update, bridge, listings_data)
        assert result is False
