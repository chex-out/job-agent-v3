"""Shared fixtures for eval tests."""

import shutil
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def profile_config_dir(tmp_path):
    """A temporary config/ dir with the golden complete_profile.yaml."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    shutil.copy(FIXTURES_DIR / "complete_profile.yaml", config_dir / "profile.yaml")
    return config_dir


@pytest.fixture
def minimal_profile_config_dir(tmp_path):
    """A temporary config/ dir with a minimal valid profile (required fields only)."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    profile_text = (
        'schema_version: "1.0"\n'
        'name: "Sam Test"\n'
        'target_roles: ["Software Engineer"]\n'
        'seniority: "mid-career"\n'
        'location: "Remote"\n'
        'certifications: []\n'
        'feedback_directness: 3\n'
    )
    (config_dir / "profile.yaml").write_text(profile_text, encoding="utf-8")
    return config_dir


@pytest.fixture
def golden_listings_path():
    """Path to the golden processed_listings.yaml fixture."""
    return FIXTURES_DIR / "processed_listings.yaml"
