"""Tests for the email-tier profile bootstrap."""

import json
from unittest.mock import MagicMock

import pytest

from src.bootstrap import build_profile_dict, run_bootstrap
from src.profile import load_profile

EXTRACTED = {
    "key_skills": ["Campaign strategy", "SQL"],
    "experience_years": 8,
    "positioning_strengths": ["Full-funnel results", "Strategic + technical"],
    "known_concerns": ["Single-company tenure"],
    "certifications": [],
    "company_preferences": {
        "minimum_bar": ["Product-led"],
        "ideal_signals": ["Experimentation culture"],
        "nice_to_have": [],
        "deal_breakers": ["Agencies"],
    },
    "resume_analysis": {
        "positioning_strengths_detail": ["Detail 1"],
        "interviewer_concerns_detail": ["Concern 1 — HIGH"],
        "story_seeds": ["Seed 1"],
    },
}


def _mock_client(payload: dict | str) -> MagicMock:
    client = MagicMock()
    block = MagicMock()
    block.text = payload if isinstance(payload, str) else json.dumps(payload)
    client.messages.create.return_value = MagicMock(content=[block])
    return client


class TestBuildProfileDict:
    def test_matches_loader_schema(self, tmp_path):
        profile = build_profile_dict(
            "Maya Rodriguez", ["Marketing Manager"], "Senior", "Singapore", EXTRACTED
        )
        assert profile["schema_version"] == "1.0"
        assert profile["scoring"]["threshold_for_preparation"] == {
            "skills_fit_min": 6,
            "preference_fit_min": 7,
        }
        assert profile["company_preferences"]["deal_breakers"] == ["Agencies"]

    def test_handles_missing_extracted_fields(self):
        profile = build_profile_dict("Maya", ["Manager"], "Senior", "Singapore", {})
        assert profile["key_skills"] == []
        assert profile["experience_years"] == 0


class TestRunBootstrap:
    def test_writes_all_four_files_and_validates(self, tmp_path):
        config_dir = tmp_path / "config"
        state_path = tmp_path / "coaching_state.md"

        run_bootstrap(
            config_dir=config_dir,
            state_path=state_path,
            name="Maya Rodriguez",
            resume_text="# Maya Rodriguez\nMarketing Manager, 8 years...",
            target_roles=["Marketing Manager"],
            seniority="Senior",
            location="Singapore",
            preferences_text="Product-led companies only",
            client=_mock_client(EXTRACTED),
        )

        assert (config_dir / "profile.yaml").exists()
        assert (config_dir / "resume_base.md").exists()
        assert (config_dir / "cover_letter_base.md").exists()
        assert state_path.exists()

        profile, rubric = load_profile(config_dir)
        assert profile.name == "Maya Rodriguez"
        assert rubric.threshold_for_preparation.preference_fit_min == 7

    def test_coaching_state_has_required_sections(self, tmp_path):
        from src.hooks.check_coaching_state import check_coaching_state

        state_path = tmp_path / "coaching_state.md"
        run_bootstrap(
            config_dir=tmp_path / "config",
            state_path=state_path,
            name="Maya",
            resume_text="resume",
            target_roles=["Manager"],
            seniority="Senior",
            location="Singapore",
            client=_mock_client(EXTRACTED),
        )
        assert check_coaching_state(state_path) == []

    def test_default_cover_letter_used_when_blank(self, tmp_path):
        config_dir = tmp_path / "config"
        run_bootstrap(
            config_dir=config_dir,
            state_path=tmp_path / "coaching_state.md",
            name="Maya",
            resume_text="resume",
            target_roles=["Manager"],
            seniority="Senior",
            location="Singapore",
            client=_mock_client(EXTRACTED),
        )
        cover = (config_dir / "cover_letter_base.md").read_text(encoding="utf-8")
        assert "[ROLE]" in cover and "[COMPANY]" in cover

    def test_missing_required_input_raises(self, tmp_path):
        with pytest.raises(ValueError):
            run_bootstrap(
                config_dir=tmp_path / "config",
                state_path=tmp_path / "coaching_state.md",
                name="",
                resume_text="resume",
                target_roles=["Manager"],
                seniority="Senior",
                location="Singapore",
                client=_mock_client(EXTRACTED),
            )

    def test_unparseable_extraction_raises(self, tmp_path):
        with pytest.raises(json.JSONDecodeError):
            run_bootstrap(
                config_dir=tmp_path / "config",
                state_path=tmp_path / "coaching_state.md",
                name="Maya",
                resume_text="resume",
                target_roles=["Manager"],
                seniority="Senior",
                location="Singapore",
                client=_mock_client("I can't help with that."),
            )
