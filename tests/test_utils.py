"""Tests for utils.py — retry_with_backoff, YAML safety, URL normalization, fuzzy company matching."""

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils import (
    load_yaml,
    normalize_url,
    parse_job_body_company,
    parse_job_body_date,
    resolve_company_name,
    retry_with_backoff,
)


class TestRetryWithBackoff:
    def test_succeeds_first_try(self):
        result = retry_with_backoff(fn=lambda: "success", max_retries=3, base_delay=0.01)
        assert result == "success"

    def test_succeeds_after_retry(self):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient failure")
            return "recovered"

        result = retry_with_backoff(
            fn=flaky, max_retries=3, base_delay=0.01,
            retryable_exceptions=(ConnectionError,),
        )
        assert result == "recovered"
        assert call_count == 3

    def test_exhausts_retries(self):
        def always_fails():
            raise ConnectionError("permanent failure")

        with pytest.raises(ConnectionError, match="permanent failure"):
            retry_with_backoff(
                fn=always_fails, max_retries=2, base_delay=0.01,
                retryable_exceptions=(ConnectionError,),
            )

    def test_non_retryable_exception_raises_immediately(self):
        call_count = 0

        def bad_code():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError, match="not retryable"):
            retry_with_backoff(
                fn=bad_code, max_retries=3, base_delay=0.01,
                retryable_exceptions=(ConnectionError,),
            )
        assert call_count == 1

    def test_returns_none_value(self):
        result = retry_with_backoff(fn=lambda: None, max_retries=1, base_delay=0.01)
        assert result is None


class TestLoadYamlSafety:
    def test_missing_file_returns_empty_dict(self):
        result = load_yaml("/nonexistent/path/file.yaml")
        assert result == {}

    def test_corrupt_yaml_raises_and_backs_up(self):
        """Corrupt YAML must never be silently treated as empty — a later
        save would permanently overwrite the user's recoverable data."""
        from src.utils import CorruptYamlError

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("{{{bad yaml: [unterminated")
            f.flush()
        try:
            with pytest.raises(CorruptYamlError):
                load_yaml(f.name)
            backup = Path(f.name + ".corrupt")
            assert backup.exists()
            assert "bad yaml" in backup.read_text(encoding="utf-8")
            backup.unlink()
        finally:
            Path(f.name).unlink()

    def test_valid_yaml_loads_normally(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("key: value\nlist:\n  - a\n  - b\n")
            f.flush()
            result = load_yaml(f.name)
            assert result == {"key": "value", "list": ["a", "b"]}
        Path(f.name).unlink()

    def test_empty_yaml_returns_empty_dict(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            result = load_yaml(f.name)
            assert result == {}
        Path(f.name).unlink()


class TestNormalizeUrl:
    def test_strips_trailing_slash(self):
        assert normalize_url("https://example.com/jobs/123/") == "https://example.com/jobs/123"

    def test_lowercases_scheme_and_host(self):
        result = normalize_url("HTTPS://EXAMPLE.COM/Jobs/123")
        assert result.startswith("https://example.com/")
        assert "/Jobs/123" in result

    def test_removes_utm_params(self):
        url = "https://example.com/job?id=42&utm_source=email&utm_medium=link"
        result = normalize_url(url)
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "id=42" in result

    def test_removes_fbclid(self):
        url = "https://example.com/job?fbclid=abc123&jk=456"
        result = normalize_url(url)
        assert "fbclid" not in result
        assert "jk=456" in result

    def test_preserves_job_specific_params(self):
        url = "https://indeed.com/viewjob?jk=abc123&from=web"
        result = normalize_url(url)
        assert "jk=abc123" in result

    def test_no_query_params(self):
        url = "https://example.com/jobs/backend-engineer"
        assert normalize_url(url) == "https://example.com/jobs/backend-engineer"

    def test_identical_urls_normalize_same(self):
        url1 = "https://Example.COM/jobs/123/"
        url2 = "https://example.com/jobs/123"
        assert normalize_url(url1) == normalize_url(url2)

    def test_different_tracking_params_normalize_same(self):
        url1 = "https://example.com/job?id=42&utm_source=email"
        url2 = "https://example.com/job?id=42&utm_source=twitter"
        assert normalize_url(url1) == normalize_url(url2)


class TestResolveCompanyName:
    def test_exact_match(self):
        match, confidence = resolve_company_name("Supabase", ["Supabase", "Adyen"])
        assert match == "Supabase"
        assert confidence == 100.0

    def test_case_insensitive_exact(self):
        match, confidence = resolve_company_name("supabase", ["Supabase", "Adyen"])
        assert match == "Supabase"
        assert confidence == 100.0

    def test_suffix_variation(self):
        match, confidence = resolve_company_name("Amazon.com", ["Amazon", "Google"])
        assert match == "Amazon"
        assert confidence >= 85

    def test_subset_match_via_token_set(self):
        match, confidence = resolve_company_name("Meta", ["Meta Platforms", "Google"])
        assert match == "Meta Platforms"
        assert confidence >= 90

    def test_no_false_positive_stripe_strike(self):
        match, _ = resolve_company_name("Strike", ["Stripe", "Google"])
        if match == "Stripe":
            pytest.fail("False positive: 'Strike' should not match 'Stripe'")

    def test_no_false_positive_notion_motion(self):
        match, _ = resolve_company_name("Motion", ["Notion", "Google"])
        if match == "Notion":
            pytest.fail("False positive: 'Motion' should not match 'Notion'")

    def test_empty_known_list(self):
        match, confidence = resolve_company_name("Supabase", [])
        assert match is None
        assert confidence == 0.0

    def test_empty_raw_name(self):
        match, confidence = resolve_company_name("", ["Supabase"])
        assert match is None
        assert confidence == 0.0

    def test_no_match_found(self):
        match, confidence = resolve_company_name("Acme Corp", ["Supabase", "Adyen"])
        assert match is None
        assert confidence == 0.0

    def test_company_with_inc_suffix(self):
        match, confidence = resolve_company_name("Anthropic", ["Anthropic, Inc.", "Google"])
        assert match == "Anthropic, Inc."
        assert confidence >= 85


class TestParseJobBodyDate:
    def test_extracts_old_date(self):
        body = "Job posted on\n\nMay 04, 2023\n\nEmployee Type"
        result = parse_job_body_date(body)
        assert result == date(2023, 5, 4)

    def test_extracts_recent_date(self):
        body = "Job posted on\n\nMarch 12, 2026\n\nEmployee Type"
        result = parse_job_body_date(body)
        assert result == date(2026, 3, 12)

    def test_returns_none_when_no_pattern(self):
        body = "Posted on: November 23, 2024\nSome job description here."
        result = parse_job_body_date(body)
        assert result is None

    def test_returns_none_empty_string(self):
        assert parse_job_body_date("") is None

    def test_handles_inline_format(self):
        body = "Job posted on March 01, 2026 in Singapore"
        result = parse_job_body_date(body)
        assert result == date(2026, 3, 1)


class TestParseJobBodyCompany:
    def test_all_caps_about(self):
        body = "ABOUT JANIO\n\nJanio is a logistics company"
        result = parse_job_body_company(body)
        assert result == "JANIO"

    def test_title_case_about(self):
        body = "About Darwinbox\n\nDarwinbox is an HR SaaS"
        result = parse_job_body_company(body)
        assert result == "Darwinbox"

    def test_stops_at_and(self):
        body = "About Ask & Embla and Ambi\n\nWe are a jewelry brand"
        result = parse_job_body_company(body)
        assert result is not None
        assert "Ambi" not in result
        assert "Ask" in result

    def test_returns_none_when_no_pattern(self):
        body = "Introduction\n\nThe Growth Marketing Manager owns the full customer lifecycle."
        result = parse_job_body_company(body)
        assert result is None

    def test_returns_none_empty_string(self):
        assert parse_job_body_company("") is None
