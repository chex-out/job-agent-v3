"""Tests for file_writer.py — update_section, read_section, section_is_populated, Change Log cap."""

from pathlib import Path

import pytest

from src.file_writer import (
    CHANGE_LOG_MAX_ENTRIES,
    SECTION_KEYS,
    read_section,
    section_is_populated,
    update_section,
)


class TestUpdateSectionNewFile:
    def test_creates_file_if_not_exists(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "Lead with demand gen expertise.")
        assert path.exists()
        assert "## Cover Letter Focus" in path.read_text(encoding="utf-8")

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "notes.md"
        update_section(path, "positioning_focus", "Content here.")
        assert path.exists()

    def test_new_section_written_to_empty_file(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "what_changed", "- Moved skills section up.")
        content = path.read_text(encoding="utf-8")
        assert "## What Changed" in content
        assert "Moved skills section up" in content

    def test_unknown_key_raises_value_error(self, tmp_path):
        path = tmp_path / "notes.md"
        with pytest.raises(ValueError, match="Unknown section key"):
            update_section(path, "not_a_real_key", "Content.")


class TestUpdateSectionOverwrite:
    def test_overwrites_existing_section(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "First version.")
        update_section(path, "positioning_focus", "Second version.")
        content = path.read_text(encoding="utf-8")
        assert "Second version." in content
        assert "First version." not in content

    def test_does_not_duplicate_heading(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "Draft A.")
        update_section(path, "positioning_focus", "Draft B.")
        content = path.read_text(encoding="utf-8")
        assert content.count("## Cover Letter Focus") == 1

    def test_other_sections_preserved(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "Focus here.")
        update_section(path, "watch_outs", "Watch out for this.")
        update_section(path, "positioning_focus", "Updated focus.")
        content = path.read_text(encoding="utf-8")
        assert "Updated focus." in content
        assert "Watch out for this." in content


class TestChangeLog:
    def test_change_log_not_written_for_new_section(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "First write.", reason="Initial")
        content = path.read_text(encoding="utf-8")
        # Change Log should not be created for first write of a new section
        assert "## Change Log" not in content

    def test_change_log_written_on_overwrite(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "First.")
        update_section(path, "positioning_focus", "Second.", reason="Better angle found")
        content = path.read_text(encoding="utf-8")
        assert "## Change Log" in content
        assert "Better angle found" in content

    def test_change_log_no_entry_without_reason(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "First.")
        update_section(path, "positioning_focus", "Second.")
        content = path.read_text(encoding="utf-8")
        # No reason → no Change Log entry (section may or may not exist)
        # Specifically: no entry text
        assert "## Change Log" not in content or "- [" not in content

    def test_change_log_capped_at_max_entries(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "First.")
        # Write enough updates to overflow the cap
        for i in range(CHANGE_LOG_MAX_ENTRIES + 5):
            update_section(path, "positioning_focus", f"Update {i}.", reason=f"Reason {i}")
        content = path.read_text(encoding="utf-8")
        log_lines = [
            line for line in content.splitlines()
            if line.strip().startswith("- [")
        ]
        assert len(log_lines) <= CHANGE_LOG_MAX_ENTRIES

    def test_oldest_entries_dropped_on_overflow(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "Start.")
        # Write exactly MAX + 1 entries
        for i in range(CHANGE_LOG_MAX_ENTRIES + 1):
            update_section(path, "positioning_focus", f"V{i}.", reason=f"reason-{i}")
        content = path.read_text(encoding="utf-8")
        # The earliest reason should be dropped
        assert "reason-0" not in content
        # The latest should be present
        assert f"reason-{CHANGE_LOG_MAX_ENTRIES}" in content


class TestReadSection:
    def test_returns_section_content(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "Demand gen expert.")
        result = read_section(path, "positioning_focus")
        assert result is not None
        assert "Demand gen expert" in result

    def test_returns_none_for_missing_file(self, tmp_path):
        path = tmp_path / "nonexistent.md"
        assert read_section(path, "positioning_focus") is None

    def test_returns_none_for_missing_section(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "Content.")
        assert read_section(path, "watch_outs") is None

    def test_unknown_key_raises(self, tmp_path):
        path = tmp_path / "notes.md"
        with pytest.raises(ValueError):
            read_section(path, "fake_key")


class TestSectionIsPopulated:
    def test_populated_returns_true(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "career_highlights", "- Led Horizon launch campaign")
        assert section_is_populated(path, "career_highlights") is True

    def test_whitespace_only_returns_false(self, tmp_path):
        path = tmp_path / "notes.md"
        # Write section with only whitespace content
        path.write_text("### Career Highlights\n   \n\n", encoding="utf-8")
        assert section_is_populated(path, "career_highlights") is False

    def test_missing_section_returns_false(self, tmp_path):
        path = tmp_path / "notes.md"
        path.write_text("# Empty file\n", encoding="utf-8")
        assert section_is_populated(path, "career_highlights") is False

    def test_missing_file_returns_false(self, tmp_path):
        path = tmp_path / "nonexistent.md"
        assert section_is_populated(path, "career_highlights") is False


class TestLfLineEndings:
    def test_writes_lf_not_crlf(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "Line one.\nLine two.")
        raw = path.read_bytes()
        assert b"\r\n" not in raw

    def test_overwrites_preserve_lf(self, tmp_path):
        path = tmp_path / "notes.md"
        update_section(path, "positioning_focus", "First.")
        update_section(path, "positioning_focus", "Second.\nMore.")
        raw = path.read_bytes()
        assert b"\r\n" not in raw


class TestSectionBoundaryAtHigherLevelHeading:
    """Regression: an h3 section must stop at a following h2 heading.

    The original lookahead only matched same-level headings, so updating
    '### Superpower' consumed and deleted the '## Interview Loops' section
    that follows it in coaching_state.md.
    """

    def test_h3_update_preserves_following_h2(self, tmp_path):
        path = tmp_path / "coaching_state.md"
        path.write_text(
            "# Coaching State\n\n"
            "## Storybank\n\n"
            "### Superpower\nOld superpower text\n\n"
            "## Interview Loops\n- Acme — Researching\n\n"
            "## Outcome Log\n[Empty]\n",
            encoding="utf-8",
            newline="\n",
        )

        update_section(path, "superpower", "New superpower text")

        content = path.read_text(encoding="utf-8")
        assert "New superpower text" in content
        assert "Old superpower text" not in content
        assert "## Interview Loops" in content
        assert "- Acme — Researching" in content
        assert "## Outcome Log" in content

    def test_h3_update_still_stops_at_same_level(self, tmp_path):
        path = tmp_path / "notes.md"
        path.write_text(
            "## Storybank\n\n"
            "### Career Highlights\nOld highlights\n\n"
            "### Positioning Statement\nKeep me intact\n",
            encoding="utf-8",
            newline="\n",
        )

        update_section(path, "career_highlights", "New highlights")

        content = path.read_text(encoding="utf-8")
        assert "New highlights" in content
        assert "Old highlights" not in content
        assert "Keep me intact" in content
