"""Eval: anti-fabrication validation catches fabricated claims.

These tests verify that validate_tailored_output() correctly:
- Detects FABRICATED claims (certifications or skills not in source)
- Returns parse_failed=True when the API returns invalid JSON
- Does NOT block UNCERTAIN claims (only surfaces them silently)
- Returns empty fabricated list when all claims are CONFIRMED

The Anthropic client is mocked — no live API calls.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.preparer import validate_tailored_output


# Minimal inputs used across tests
RESUME_BASE = "# Alex Rivera\n\n## Skills\n- Marketing automation (HubSpot)\n- B2B demand generation\n"
PROFILE_DICT = {
    "name": "Alex Rivera",
    "certifications": ["HubSpot Marketing Certified"],
    "key_skills": ["B2B demand generation", "Marketing automation (HubSpot)"],
}
TAILORED_RESUME = "# Alex Rivera\n\n## Skills\n- Marketing automation (HubSpot)\n- B2B demand generation\n"
TAILORED_COVER_LETTER = "Dear Hiring Manager,\n\nI bring strong HubSpot expertise.\n"


def _make_mock_client(response_text: str) -> MagicMock:
    """Build a mock Anthropic client that returns response_text."""
    mock_content = MagicMock()
    mock_content.text = response_text

    mock_response = MagicMock()
    mock_response.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


class TestFabricatedClaimsDetected:
    """validate_tailored_output returns FABRICATED claims when they exist."""

    def test_fabricated_certification_is_flagged(self):
        """When the API returns a fabricated certification, it must appear in fabricated list."""
        fabricated_response = json.dumps({
            "fabricated": [
                {
                    "claim": "Google Analytics Certified",
                    "location": "resume",
                    "reason": "Not listed in profile certifications — only HubSpot Marketing Certified appears"
                }
            ],
            "uncertain": [],
            "summary": "1 fabricated claim found: certification not in source profile."
        })
        client = _make_mock_client(fabricated_response)

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert "fabricated" in result
        assert len(result["fabricated"]) == 1
        assert result["fabricated"][0]["claim"] == "Google Analytics Certified"
        assert "parse_failed" not in result

    def test_fabricated_metric_is_flagged(self):
        """Embellished metrics that can't be traced to source must be flagged."""
        fabricated_response = json.dumps({
            "fabricated": [
                {
                    "claim": "increased pipeline by 300%",
                    "location": "cover_letter",
                    "reason": "No specific pipeline percentage appears in base resume"
                }
            ],
            "uncertain": [],
            "summary": "1 fabricated metric found."
        })
        client = _make_mock_client(fabricated_response)

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert len(result["fabricated"]) == 1
        assert result["fabricated"][0]["location"] == "cover_letter"

    def test_multiple_fabrications_all_returned(self):
        fabricated_response = json.dumps({
            "fabricated": [
                {"claim": "Salesforce Certified", "location": "resume", "reason": "Not in profile"},
                {"claim": "led team of 20", "location": "cover_letter", "reason": "No team size in source"},
            ],
            "uncertain": [],
            "summary": "2 fabricated claims found."
        })
        client = _make_mock_client(fabricated_response)

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert len(result["fabricated"]) == 2


class TestUncertainClaimsNotBlocked:
    """UNCERTAIN claims must be returned but must NOT appear in fabricated list."""

    def test_uncertain_not_in_fabricated(self):
        """Uncertain claims are surfaced separately — they don't block document save."""
        response = json.dumps({
            "fabricated": [],
            "uncertain": [
                {
                    "claim": "strong analytical mindset",
                    "location": "resume",
                    "note": "Paraphrase of 'data-driven approach' in source — plausible but not verbatim"
                }
            ],
            "summary": "No fabricated claims. 1 uncertain phrasing noted."
        })
        client = _make_mock_client(response)

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert result["fabricated"] == []
        assert len(result["uncertain"]) == 1
        assert "parse_failed" not in result


class TestCleanResumePassesValidation:
    """When all claims are CONFIRMED, fabricated list must be empty."""

    def test_all_confirmed_returns_empty_fabricated(self):
        response = json.dumps({
            "fabricated": [],
            "uncertain": [],
            "summary": "All claims confirmed. No issues found."
        })
        client = _make_mock_client(response)

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert result["fabricated"] == []
        assert result["uncertain"] == []
        assert "parse_failed" not in result


class TestParseFailureSafety:
    """When API returns invalid JSON, validate_tailored_output must not crash."""

    def test_invalid_json_returns_parse_failed(self):
        """Malformed JSON response must return parse_failed=True, not raise an exception."""
        client = _make_mock_client("This is not JSON at all — the model returned prose.")

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert result.get("parse_failed") is True
        assert result["fabricated"] == []
        assert result["uncertain"] == []

    def test_empty_response_returns_parse_failed(self):
        client = _make_mock_client("")

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert result.get("parse_failed") is True

    def test_partial_json_returns_parse_failed(self):
        client = _make_mock_client('{"fabricated": [{"claim": "incomplete')

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert result.get("parse_failed") is True

    def test_api_error_returns_parse_failed(self):
        """APIError from Anthropic must be caught and return parse_failed gracefully."""
        import anthropic

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="Service unavailable", request=MagicMock(), body=None
        )

        result = validate_tailored_output(
            mock_client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert result.get("parse_failed") is True

    def test_parse_failed_result_has_all_keys(self):
        """parse_failed response must still have the standard keys."""
        client = _make_mock_client("not json")

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert "fabricated" in result
        assert "uncertain" in result
        assert "summary" in result
        assert "parse_failed" in result


class TestCodeFencedJsonResponse:
    """API may return JSON wrapped in markdown code fences — must be stripped."""

    def test_code_fenced_json_parsed_correctly(self):
        response_with_fences = (
            "```json\n"
            + json.dumps({"fabricated": [], "uncertain": [], "summary": "All confirmed."})
            + "\n```"
        )
        client = _make_mock_client(response_with_fences)

        result = validate_tailored_output(
            client, TAILORED_RESUME, TAILORED_COVER_LETTER, RESUME_BASE, PROFILE_DICT
        )

        assert result["fabricated"] == []
        assert "parse_failed" not in result
