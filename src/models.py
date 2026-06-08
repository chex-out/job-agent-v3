"""Data models for the Job Seeker AI Toolkit."""

from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class ListingSource(str, Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    CAREERS_PAGE = "careers_page"
    OTHER = "other"


class ListingStatus(str, Enum):
    QUEUED = "queued"
    SCORED = "scored"
    PREPARED = "prepared"
    UNDER_REVIEW = "under_review"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    REJECTED = "rejected"
    OFFER = "offer"
    SKIPPED = "skipped"
    ERROR = "error"


class ListingInput(BaseModel):
    """A job listing URL queued for scoring."""

    url: str
    source: ListingSource = ListingSource.OTHER
    date_added: date = Field(default_factory=date.today)
    status: ListingStatus = ListingStatus.QUEUED
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    prefetched_text: Optional[str] = None  # Body text from get_job_details (MCP-sourced)


class ScoredListing(BaseModel):
    """A listing that has been fetched and scored by Claude."""

    url: str
    source: ListingSource
    date_added: date
    date_scored: date = Field(default_factory=date.today)
    status: ListingStatus = ListingStatus.SCORED

    # Extracted from listing page
    company_name: str
    role_title: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    key_requirements: list[str] = []
    nice_to_haves: list[str] = []
    salary_range: Optional[str] = None

    # Scoring output
    skills_fit: int = Field(ge=0, le=10)
    preference_fit: int = Field(ge=0, le=10)
    skills_reasoning: str
    preference_reasoning: str
    fit_assessment: str = ""  # "strong" / "moderate" / "weak"
    concerns: list[str] = []
    strengths: list[str] = []

    # Pipeline tracking
    digested: bool = False
    prepared: bool = False
    drive_folder_url: Optional[str] = None
    culture_notes: Optional[str] = None  # Glassdoor enrichment summary

    def derive_fit_assessment(self) -> str:
        if self.skills_fit >= 6 and self.preference_fit >= 7:
            return "strong"
        elif self.skills_fit >= 5 and self.preference_fit >= 5:
            return "moderate"
        return "weak"

    def model_post_init(self, __context: Any) -> None:
        if not self.fit_assessment:
            self.fit_assessment = self.derive_fit_assessment()


class UserProfile(BaseModel):
    """Candidate profile used for scoring and personalizing all outputs."""

    # Schema version — checked by profile.py on load
    schema_version: str = "1.0"

    # Identity
    name: str
    target_roles: list[str]
    seniority: str
    location: str
    preferred_work_arrangement: str = "hybrid or remote"
    experience_years: int = 0

    # Positioning
    key_skills: list[str] = []
    positioning_strengths: list[str] = []
    known_concerns: list[str] = []
    certifications: list[str] = []  # Explicit list for anti-fabrication validation

    # Company preferences
    company_preferences: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "minimum_bar": [],
            "ideal_signals": [],
            "nice_to_have": [],
            "deal_breakers": [],
        }
    )

    # Scoring config
    scoring: dict[str, Any] = Field(
        default_factory=lambda: {
            "threshold_for_preparation": 7,
            "threshold_for_coaching": 7,
            "glassdoor_enrich_limit": 5,
        }
    )

    # Feedback style
    feedback_directness: int = Field(default=5, ge=1, le=5)

    # Document paths
    resume_path: str = "config/resume_base.md"
    cover_letter_path: str = "config/cover_letter_base.md"

    # Search config
    search: dict[str, Any] = Field(
        default_factory=lambda: {
            "max_age_days": 30,
            "additional_keywords": [],
        }
    )

    # LinkedIn config (optional — only needed for --apify mode)
    linkedin: dict[str, Any] = Field(
        default_factory=dict
    )  # user_agent: set once; used by Mode 5 Apify actor auth

    @classmethod
    def from_profile_yaml(cls, path: str | Path) -> "UserProfile":
        """Load and validate UserProfile from profile.yaml."""
        with open(path, "r", encoding="utf-8", newline="\n") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)


class ScoringThreshold(BaseModel):
    """Dual-axis threshold: a listing must clear both axes to qualify."""

    skills_fit_min: int = 6    # Can they do the job?
    preference_fit_min: int = 7  # Do they want this job?


class ScoringRubric(BaseModel):
    """Scoring configuration for fit assessment."""

    threshold_for_preparation: ScoringThreshold = Field(default_factory=ScoringThreshold)
    threshold_for_coaching: ScoringThreshold = Field(default_factory=ScoringThreshold)

    dimensions: dict[str, dict] = Field(default_factory=dict)
    deal_breaker_rules: list[str] = []

    def is_above_prep_threshold(self, skills_fit: int, preference_fit: int) -> bool:
        """Return True if both scores meet the preparation threshold."""
        return (
            skills_fit >= self.threshold_for_preparation.skills_fit_min
            and preference_fit >= self.threshold_for_preparation.preference_fit_min
        )

    def is_above_coaching_threshold(self, skills_fit: int, preference_fit: int) -> bool:
        """Return True if both scores meet the coaching bridge threshold."""
        return (
            skills_fit >= self.threshold_for_coaching.skills_fit_min
            and preference_fit >= self.threshold_for_coaching.preference_fit_min
        )
