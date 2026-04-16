"""Tests for coach_bridge.py — parsing and writing coaching_state.md."""

import shutil
from pathlib import Path

import pytest

from src.coach_bridge import CoachBridge

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_STATE = FIXTURES / "sample_coaching_state.md"


@pytest.fixture
def bridge(tmp_path):
    """Create a CoachBridge with a copy of the sample coaching state."""
    state_file = tmp_path / "coaching_state.md"
    shutil.copy(SAMPLE_STATE, state_file)
    return CoachBridge(state_path=state_file)


@pytest.fixture
def bridge_path(tmp_path):
    """Return the path to the temporary coaching state file."""
    return tmp_path / "coaching_state.md"


class TestGetInterviewLoops:
    def test_empty_loops(self, bridge):
        """Sample state has empty Interview Loops — returns empty dict."""
        loops = bridge.get_interview_loops()
        assert loops == {}

    def test_loops_after_writing(self, bridge):
        """After writing an entry, it should be readable."""
        bridge.write_research_entry(
            "TestCo", "strong", "AI-native, Series B, remote-first"
        )
        loops = bridge.get_interview_loops()
        assert "testco" in loops
        assert loops["testco"]["company"] == "TestCo"
        assert "strong" in loops["testco"].get("fit assessment", "")


class TestWriteResearchEntry:
    def test_first_entry_replaces_empty_placeholder(self, bridge, bridge_path):
        """Writing the first entry should replace the [Empty] placeholder."""
        result = bridge.write_research_entry(
            "Anthropic",
            "strong",
            "AI-native leader, building Claude — ideal culture fit",
            "2026-03-11",
        )
        assert result is True

        content = bridge_path.read_text(encoding="utf-8")
        assert "### Anthropic" in content
        assert "Researched (via Job Agent)" in content
        assert "strong" in content
        assert "AI-native leader" in content

    def test_second_entry_appends(self, bridge, bridge_path):
        """Writing a second entry should append, not replace the first."""
        bridge.write_research_entry("CompanyA", "strong", "Great fit")
        bridge.write_research_entry("CompanyB", "moderate", "Decent fit")

        content = bridge_path.read_text(encoding="utf-8")
        assert "### CompanyA" in content
        assert "### CompanyB" in content

    def test_no_downgrade_applied(self, bridge, bridge_path):
        """Should not overwrite an entry at 'Applied' status."""
        bridge.write_research_entry("TestCo", "strong", "Initial assessment")
        bridge.update_loop_status("TestCo", "Applied")

        result = bridge.write_research_entry("TestCo", "moderate", "Updated signals")
        assert result is False

        content = bridge_path.read_text(encoding="utf-8")
        assert "Applied" in content
        assert "Updated signals" not in content

    def test_update_existing_researched(self, bridge, bridge_path):
        """Re-researching should update the existing entry."""
        bridge.write_research_entry("TestCo", "moderate", "First pass")
        bridge.write_research_entry("TestCo", "strong", "Better signals after deeper look")

        content = bridge_path.read_text(encoding="utf-8")
        assert "Better signals" in content
        assert content.count("### TestCo") == 1


class TestUpdateLoopStatus:
    def test_update_status(self, bridge, bridge_path):
        bridge.write_research_entry("TestCo", "strong", "Great fit")
        result = bridge.update_loop_status("TestCo", "Applied")
        assert result is True

        content = bridge_path.read_text(encoding="utf-8")
        assert "Applied" in content
        assert "Researched (via Job Agent)" not in content

    def test_update_nonexistent_company(self, bridge):
        result = bridge.update_loop_status("NonExistentCo", "Applied")
        assert result is False


class TestAddOutcome:
    def test_first_outcome_creates_table(self, bridge, bridge_path):
        result = bridge.add_outcome(
            "TestCo", "Marketing Manager", "Screen", "advanced",
            "Good conversation", "2026-03-11"
        )
        assert result is True

        content = bridge_path.read_text(encoding="utf-8")
        assert "TestCo" in content
        assert "advanced" in content

    def test_multiple_outcomes(self, bridge, bridge_path):
        bridge.add_outcome("CompanyA", "Role1", "Screen", "advanced")
        bridge.add_outcome("CompanyB", "Role2", "Final", "rejected")

        content = bridge_path.read_text(encoding="utf-8")
        assert "CompanyA" in content
        assert "CompanyB" in content


class TestPreservesOtherSections:
    def test_storybank_preserved(self, bridge, bridge_path):
        """Writing to Interview Loops should not affect other sections."""
        original = bridge_path.read_text(encoding="utf-8")
        assert "S001" in original

        bridge.write_research_entry("NewCo", "strong", "Test")

        updated = bridge_path.read_text(encoding="utf-8")
        assert "S001" in updated
        assert "The Horizon Campaign" in updated
        assert "Marketo Implementation" in updated

    def test_profile_preserved(self, bridge, bridge_path):
        bridge.write_research_entry("NewCo", "strong", "Test")
        bridge.add_outcome("NewCo", "Role", "Screen", "advanced")

        updated = bridge_path.read_text(encoding="utf-8")
        assert "Maya Rodriguez" in updated
        assert "Digital Marketing Manager" in updated


class TestDefaultStatePath:
    def test_uses_cwd_by_default(self, tmp_path, monkeypatch):
        """Default path should be cwd/coaching_state.md, not relative to __file__."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("COACHING_STATE_PATH", raising=False)
        bridge = CoachBridge()
        assert bridge.state_path == tmp_path / "coaching_state.md"

    def test_uses_env_var_if_set(self, tmp_path, monkeypatch):
        """Should use COACHING_STATE_PATH env var when set."""
        custom_path = tmp_path / "custom" / "state.md"
        monkeypatch.setenv("COACHING_STATE_PATH", str(custom_path))
        bridge = CoachBridge()
        assert bridge.state_path == custom_path
