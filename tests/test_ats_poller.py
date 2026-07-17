"""Tests for ats_poller.py — provider parsing, filtering, detection, and dedup."""

from datetime import date, datetime, timedelta, timezone

import pytest

from src.ats_poller import (
    ATSPoller,
    Candidate,
    _ashby_parse,
    _greenhouse_parse,
    _lever_parse,
    _parse_when,
    candidate_slugs,
    title_matches,
)
from src.utils import detect_source, load_yaml, save_yaml


@pytest.fixture
def poller(tmp_path):
    """Create an ATSPoller with temporary config and data directories."""
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_dir.mkdir()
    data_dir.mkdir()
    return ATSPoller(config_dir=config_dir, data_dir=data_dir)


# --- Fixtures: canned provider payloads ---


GREENHOUSE_PAYLOAD = {
    "jobs": [
        {
            "id": 1,
            "title": "Growth Marketing Manager",
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
            "location": {"name": "Singapore"},
            "first_published": "2026-07-10T08:00:00-04:00",
            "updated_at": "2026-07-12T08:00:00-04:00",
            "content": "&lt;p&gt;Own our &lt;b&gt;growth&lt;/b&gt; engine.&lt;/p&gt;",
        },
        {
            "id": 2,
            "title": "Site Reliability Engineer",
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/2",
            "location": {"name": "Remote"},
            "updated_at": "2026-07-01T08:00:00-04:00",
            "content": "",
        },
    ]
}

LEVER_PAYLOAD = [
    {
        "id": "abc",
        "text": "Marketing Manager, Growth",
        "hostedUrl": "https://jobs.lever.co/acme/abc",
        "createdAt": 1783468800000,  # 2026-07-08 UTC
        "categories": {"location": "Singapore", "commitment": "Full-time"},
        "descriptionPlain": "Drive growth marketing.",
        "lists": [
            {"text": "Requirements", "content": "<li>5 years experience</li>"},
        ],
    },
]

ASHBY_PAYLOAD = {
    "jobs": [
        {
            "title": "Product Marketing Manager",
            "jobUrl": "https://jobs.ashbyhq.com/acme/xyz",
            "location": "Singapore",
            "publishedAt": "2026-07-11T00:00:00Z",
            "isListed": True,
            "descriptionHtml": "<p>Tell our story.</p>",
        },
        {
            "title": "Hidden Role",
            "jobUrl": "https://jobs.ashbyhq.com/acme/hidden",
            "isListed": False,
        },
    ]
}


# --- Provider parsing ---


class TestProviderParsing:
    def test_greenhouse_parse(self):
        jobs = _greenhouse_parse(GREENHOUSE_PAYLOAD, "Acme")
        assert len(jobs) == 2
        first = jobs[0]
        assert first.url == "https://boards.greenhouse.io/acme/jobs/1"
        assert first.role_title == "Growth Marketing Manager"
        assert first.location == "Singapore"
        assert first.posted_at == date(2026, 7, 10)  # first_published wins
        # HTML-escaped content is unescaped and stripped to text
        assert "growth" in first.description_text
        assert "<" not in first.description_text

    def test_lever_parse(self):
        jobs = _lever_parse(LEVER_PAYLOAD, "Acme")
        assert len(jobs) == 1
        job = jobs[0]
        assert job.url == "https://jobs.lever.co/acme/abc"
        assert job.role_title == "Marketing Manager, Growth"
        assert job.posted_at == date(2026, 7, 8)
        assert "Drive growth marketing." in job.description_text
        assert "5 years experience" in job.description_text  # lists appended

    def test_lever_parse_rejects_non_list(self):
        assert _lever_parse({"error": "not found"}, "Acme") == []

    def test_ashby_parse_skips_unlisted(self):
        jobs = _ashby_parse(ASHBY_PAYLOAD, "Acme")
        assert len(jobs) == 1
        assert jobs[0].role_title == "Product Marketing Manager"
        assert jobs[0].posted_at == date(2026, 7, 11)
        assert "Tell our story." in jobs[0].description_text

    def test_parse_when_handles_bad_input(self):
        assert _parse_when(None) is None
        assert _parse_when("not-a-date") is None
        assert _parse_when([1, 2]) is None


# --- Slug generation ---


class TestCandidateSlugs:
    def test_single_word(self):
        assert candidate_slugs("Stripe") == ["stripe"]

    def test_multi_word_gives_joined_and_hyphenated(self):
        slugs = candidate_slugs("Acme Corp")
        assert "acmecorp" in slugs
        assert "acme-corp" in slugs
        # Suffix-stripped variant too ("Corp" is a corporate suffix)
        assert "acme" in slugs

    def test_punctuation_stripped(self):
        slugs = candidate_slugs("O'Reilly Media, Inc.")
        assert "oreillymedia" in slugs

    def test_empty_name(self):
        assert candidate_slugs("...") == []


# --- Title matching ---


class TestTitleMatches:
    ROLES = ["Growth Marketing Manager", "Product Manager"]

    def test_verbatim_match(self):
        assert title_matches("Senior Growth Marketing Manager", self.ROLES)

    def test_reordered_tokens_match(self):
        assert title_matches("Marketing Manager, Growth", self.ROLES)

    def test_seniority_words_ignored(self):
        assert title_matches("Lead Product Manager", self.ROLES)

    def test_different_role_rejected(self):
        assert not title_matches("Site Reliability Engineer", self.ROLES)

    def test_partial_overlap_rejected(self):
        # Shares "Manager" but is not a marketing or product role
        assert not title_matches("Engineering Manager", self.ROLES)


# --- detect_source integration ---


class TestDetectSource:
    def test_ats_hosts(self):
        assert detect_source("https://boards.greenhouse.io/acme/jobs/1") == "ats"
        assert detect_source("https://jobs.lever.co/acme/abc") == "ats"
        assert detect_source("https://jobs.ashbyhq.com/acme/xyz") == "ats"

    def test_non_ats_unchanged(self):
        assert detect_source("https://www.linkedin.com/jobs/view/1") == "linkedin"
        assert detect_source("https://sg.indeed.com/viewjob?jk=1") == "indeed"
        assert detect_source("https://example.com/careers/role") == "careers_page"
        # Not fooled by ATS-like strings outside the host
        assert detect_source("https://example.com/jobs/greenhouse.io-role") == "careers_page"


# --- Watchlist management ---


class TestWatchlist:
    def test_add_company_creates_file(self, poller):
        assert poller.add_company("Acme", "greenhouse", "acme") is True
        data = load_yaml(poller.data_dir / "target_companies.yaml")
        assert data["companies"][0]["name"] == "Acme"
        assert data["companies"][0]["ats"] == "greenhouse"
        assert data["companies"][0]["board_token"] == "acme"

    def test_add_company_dedupes_on_token(self, poller):
        poller.add_company("Acme", "greenhouse", "acme")
        assert poller.add_company("ACME Inc", "greenhouse", "acme") is False
        data = load_yaml(poller.data_dir / "target_companies.yaml")
        assert len(data["companies"]) == 1

    def test_preserves_careers_page_only_entries(self, poller):
        save_yaml(poller.data_dir / "target_companies.yaml", {
            "companies": [{"name": "OldCo", "careers_url": "https://oldco.com/careers"}]
        })
        poller.add_company("Acme", "lever", "acme")
        data = load_yaml(poller.data_dir / "target_companies.yaml")
        assert len(data["companies"]) == 2


# --- Polling with mocked HTTP ---


@pytest.fixture
def profile(poller):
    save_yaml(poller.config_dir / "profile.yaml", {
        "name": "Test User",
        "target_roles": ["Growth Marketing Manager"],
        "search": {"max_age_days": 30},
    })


def _gh_job(job_id, title, published):
    return {
        "id": job_id,
        "title": title,
        "absolute_url": f"https://boards.greenhouse.io/acme/jobs/{job_id}",
        "location": {"name": "Singapore"},
        "first_published": f"{published.isoformat()}T00:00:00Z",
        "content": "",
    }


def _fresh_gh_payload():
    """Greenhouse payload with dates relative to today, so tests never go stale."""
    fresh = date.today() - timedelta(days=1)
    stale = date.today() - timedelta(days=90)
    return {"jobs": [
        _gh_job(1, "Growth Marketing Manager", fresh),
        _gh_job(2, "Site Reliability Engineer", fresh),
        _gh_job(3, "Growth Marketing Manager (Archive)", stale),
    ]}


class TestPoll:
    def test_poll_filters_by_title_and_age(self, poller, profile, monkeypatch):
        poller.add_company("Acme", "greenhouse", "acme")

        payload = _fresh_gh_payload()
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: payload)
        monkeypatch.setattr("src.ats_poller.time.sleep", lambda s: None)

        candidates = poller.poll()
        # SRE title filtered out; 90-day-old posting filtered out (max_age_days=30)
        assert [c.role_title for c in candidates] == ["Growth Marketing Manager"]

        # last_polled recorded
        data = load_yaml(poller.data_dir / "target_companies.yaml")
        assert data["companies"][0]["last_polled"]

    def test_poll_all_roles_skips_title_filter(self, poller, profile, monkeypatch):
        poller.add_company("Acme", "greenhouse", "acme")
        payload = _fresh_gh_payload()
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: payload)
        monkeypatch.setattr("src.ats_poller.time.sleep", lambda s: None)

        candidates = poller.poll(all_roles=True)
        # Title filter off, but the age filter still drops the 90-day-old job
        assert len(candidates) == 2

    def test_poll_skips_fetch_failures(self, poller, profile, monkeypatch):
        poller.add_company("Acme", "greenhouse", "acme")
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: None)
        assert poller.poll() == []

    def test_poll_ignores_non_ats_entries(self, poller, profile):
        save_yaml(poller.data_dir / "target_companies.yaml", {
            "companies": [{"name": "OldCo", "careers_url": "https://oldco.com/careers"}]
        })
        assert poller.poll() == []


# --- Queueing + dedup ---


class TestAppendCandidates:
    def _candidate(self, url="https://boards.greenhouse.io/acme/jobs/1"):
        return Candidate(
            url=url,
            company_name="Acme",
            role_title="Growth Marketing Manager",
            location="Singapore",
            posted_at=date(2026, 7, 10),
            description_text="Own our growth engine.",
        )

    def test_appends_with_prefetched_text(self, poller):
        added = poller.append_candidates([self._candidate()])
        assert added == 1
        data = load_yaml(poller.data_dir / "input_listings.yaml")
        listing = data["listings"][0]
        assert listing["source"] == "ats"
        assert listing["status"] == "queued"
        assert listing["company_name"] == "Acme"
        assert "Own our growth engine." in listing["prefetched_text"]
        assert listing["prefetched_text"].startswith("Growth Marketing Manager")

    def test_dedupes_against_input_listings(self, poller):
        poller.append_candidates([self._candidate()])
        added = poller.append_candidates(
            [self._candidate(url="https://boards.greenhouse.io/acme/jobs/1?utm_source=x")]
        )
        assert added == 0

    def test_dedupes_against_processed_listings(self, poller):
        save_yaml(poller.data_dir / "processed_listings.yaml", {
            "listings": [{"url": "https://boards.greenhouse.io/acme/jobs/1", "status": "scored"}]
        })
        assert poller.append_candidates([self._candidate()]) == 0

    def test_prefetched_text_capped(self, poller):
        candidate = self._candidate()
        candidate.description_text = "x" * 20000
        poller.append_candidates([candidate])
        data = load_yaml(poller.data_dir / "input_listings.yaml")
        assert len(data["listings"][0]["prefetched_text"]) <= 8000


# --- Detection with mocked HTTP ---


class TestDetectCompany:
    def test_detects_first_matching_provider(self, poller, monkeypatch):
        def fake_fetch(url):
            if "greenhouse" in url and "/acme/jobs" in url:
                return GREENHOUSE_PAYLOAD
            if "greenhouse" in url and url.endswith("/acme"):
                return {"name": "Acme"}
            return None

        monkeypatch.setattr("src.ats_poller._fetch_json", fake_fetch)
        result = poller.detect_company("Acme")
        assert result == {
            "ats": "greenhouse",
            "board_token": "acme",
            "detected_name": "Acme",
            "jobs_count": 2,
            "verified": True,
            "sample_titles": ["Growth Marketing Manager", "Site Reliability Engineer"],
        }

    def test_rejects_wrong_company_on_slug_collision(self, poller, monkeypatch):
        # Board exists at the slug but belongs to a different company
        def fake_fetch(url):
            if "greenhouse" in url and "/acme/jobs" in url:
                return GREENHOUSE_PAYLOAD
            if "greenhouse" in url and url.endswith("/acme"):
                return {"name": "Completely Different Corp"}
            return None

        monkeypatch.setattr("src.ats_poller._fetch_json", fake_fetch)
        assert poller.detect_company("Acme") is None

    def test_no_match_returns_none(self, poller, monkeypatch):
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: None)
        assert poller.detect_company("Nonexistent Company") is None

    def test_lever_detection_without_name_check(self, poller, monkeypatch):
        def fake_fetch(url):
            if "lever.co" in url and "acme" in url:
                return LEVER_PAYLOAD
            return None

        monkeypatch.setattr("src.ats_poller._fetch_json", fake_fetch)
        result = poller.detect_company("Acme")
        assert result["ats"] == "lever"
        assert result["board_token"] == "acme"


class TestReviewFixes:
    """Regressions for the pre-PR review findings."""

    def test_missing_target_roles_fails_closed(self, poller, monkeypatch):
        """No profile / no target_roles must NOT poll unfiltered — every queued
        listing costs a scoring API call downstream (finding #2)."""
        poller.add_company("Acme", "greenhouse", "acme")
        payload = _fresh_gh_payload()
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: payload)
        monkeypatch.setattr("src.ats_poller.time.sleep", lambda s: None)

        assert poller.poll() == []  # no profile.yaml written → abort
        # ...but --all-roles is the deliberate override
        assert len(poller.poll(all_roles=True)) == 2

    def test_company_filter_fuzzy_matches_stored_org_name(
        self, poller, profile, monkeypatch
    ):
        """--detect stores the provider org name ('Stripe, Inc.'); polling with
        the user's name ('Stripe') must still match (finding #4)."""
        poller.add_company("Acme Corporation, Inc.", "greenhouse", "acme")
        payload = _fresh_gh_payload()
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: payload)
        monkeypatch.setattr("src.ats_poller.time.sleep", lambda s: None)

        candidates = poller.poll(companies=["Acme Corporation"])
        assert [c.role_title for c in candidates] == ["Growth Marketing Manager"]

    def test_company_filter_unmatched_raises(self, poller, profile):
        """A requested company that matches nothing must error loudly, not
        silently report 'Queued 0' (finding #4)."""
        poller.add_company("Acme", "greenhouse", "acme")
        with pytest.raises(LookupError, match="Nonexistent Co"):
            poller.poll(companies=["Nonexistent Co"])

    def test_dry_run_does_not_touch_watchlist(self, poller, profile, monkeypatch):
        """--dry-run must not stamp last_polled or rewrite the watchlist file
        (finding #7)."""
        poller.add_company("Acme", "greenhouse", "acme")
        payload = _fresh_gh_payload()
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: payload)
        monkeypatch.setattr("src.ats_poller.time.sleep", lambda s: None)

        before = (poller.data_dir / "target_companies.yaml").read_bytes()
        candidates = poller.poll(dry_run=True)
        assert candidates  # still returns results
        assert (poller.data_dir / "target_companies.yaml").read_bytes() == before

    def test_last_polled_is_date_granularity(self, poller, profile, monkeypatch):
        """Second-granularity timestamps would produce a no-op commit on every
        scheduled run (finding #7)."""
        poller.add_company("Acme", "greenhouse", "acme")
        payload = _fresh_gh_payload()
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: payload)
        monkeypatch.setattr("src.ats_poller.time.sleep", lambda s: None)

        poller.poll()
        data = load_yaml(poller.data_dir / "target_companies.yaml")
        assert data["companies"][0]["last_polled"] == str(date.today())

    def test_null_companies_key_does_not_crash(self, poller, profile):
        """A hand-edited watchlist with a bare `companies:` key (YAML null)
        must not raise TypeError (finding #6)."""
        (poller.data_dir / "target_companies.yaml").write_text(
            "companies:\n", encoding="utf-8"
        )
        assert poller.poll() == []
        assert poller.add_company("Acme", "greenhouse", "acme") is True

    def test_corrupt_profile_fails_closed(self, poller, monkeypatch):
        """A corrupt profile.yaml must halt the poll (CorruptYamlError), not
        degrade to unfiltered polling (finding #2)."""
        from src.utils import CorruptYamlError

        poller.add_company("Acme", "greenhouse", "acme")
        (poller.config_dir / "profile.yaml").write_text(
            "{{{bad yaml: [unterminated", encoding="utf-8"
        )
        with pytest.raises(CorruptYamlError):
            poller.poll()
        (poller.config_dir / "profile.yaml.corrupt").unlink(missing_ok=True)


class TestDetection:
    """Detection verification + confirmation gate (design fix 2)."""

    def _payloads(self, mapping):
        """Return a _fetch_json stand-in keyed by URL substring."""

        def fake(url):
            for key, payload in mapping.items():
                if key in url:
                    return payload
            return None

        return fake

    def test_greenhouse_org_match_is_verified(self, poller, monkeypatch):
        monkeypatch.setattr(
            "src.ats_poller._fetch_json",
            self._payloads({
                "boards/acme/jobs": _fresh_gh_payload(),
                "boards/acme": {"name": "Acme Corporation"},
            }),
        )
        result = poller.detect_company("Acme")
        assert result["verified"] is True
        assert result["ats"] == "greenhouse"
        assert len(result["sample_titles"]) > 0

    def test_lever_detection_is_unverified(self, poller, monkeypatch):
        lever_payload = [{
            "id": "x", "text": "Growth Marketing Manager",
            "hostedUrl": "https://jobs.lever.co/acme/x",
            "createdAt": 1783468800000, "categories": {},
        }]
        monkeypatch.setattr(
            "src.ats_poller._fetch_json",
            self._payloads({"lever.co": lever_payload}),
        )
        result = poller.detect_company("Acme")
        assert result["ats"] == "lever"
        assert result["verified"] is False
        assert result["sample_titles"] == ["Growth Marketing Manager"]

    def test_dormant_empty_board_does_not_shadow_real_ats(self, poller, monkeypatch):
        """A dormant Lever board (200 []) must not stop probing before Ashby
        (the pre-fix behavior added the empty board and never found the real one)."""
        ashby_payload = {"jobs": [{
            "title": "Growth Marketing Manager",
            "jobUrl": "https://jobs.ashbyhq.com/acme/1",
            "isListed": True,
        }]}
        monkeypatch.setattr(
            "src.ats_poller._fetch_json",
            self._payloads({"lever.co": [], "ashbyhq.com": ashby_payload}),
        )
        result = poller.detect_company("Acme")
        assert result is not None
        assert result["ats"] == "ashby"

    def test_no_board_anywhere_returns_none(self, poller, monkeypatch):
        monkeypatch.setattr("src.ats_poller._fetch_json", lambda url: None)
        assert poller.detect_company("Acme") is None
