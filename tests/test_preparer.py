"""Tests for preparer.py — slugify, prompt construction, document parsing, validation."""

import pytest

from src.preparer import (
    build_tailoring_prompt,
    extract_agent_instructions,
    parse_tailored_output,
    slugify,
)


class TestSlugify:
    def test_basic(self):
        assert slugify("Supabase") == "supabase"

    def test_spaces(self):
        assert slugify("Product Marketing Manager") == "product-marketing-manager"

    def test_special_chars(self):
        assert slugify("Company, Inc.") == "company-inc"

    def test_multiple_spaces_and_hyphens(self):
        assert slugify("Some  --  Company") == "some-company"

    def test_empty(self):
        assert slugify("") == "unknown"

    def test_all_special_chars(self):
        assert slugify("+++") == "unknown"

    def test_all_spaces(self):
        assert slugify("   ") == "unknown"


class TestExtractAgentInstructions:
    def test_extracts_instructions(self):
        text = """Dear Hiring Manager,

I am writing to express...

Yours faithfully,
Maya Rodriguez

---

## Agent Instructions
# The following notes are for the preparer agent.

EMPHASISE:
- Campaign strategy and analytics depth

DE-EMPHASISE:
- Freelance photography experience

TONE:
- Formal and precise
"""
        clean, instructions = extract_agent_instructions(text)
        assert "Dear Hiring Manager" in clean
        assert "Agent Instructions" not in clean
        assert "EMPHASISE" in instructions
        assert "DE-EMPHASISE" in instructions
        assert "TONE" in instructions

    def test_no_instructions(self):
        text = "Dear Hiring Manager,\n\nI am writing...\n\nYours faithfully"
        clean, instructions = extract_agent_instructions(text)
        assert clean == text
        assert instructions == ""


class TestBuildTailoringPrompt:
    def test_includes_anti_fabrication(self):
        listing = {
            "company_name": "TestCo",
            "role_title": "Manager",
            "location": "Remote",
            "key_requirements": ["5+ years marketing"],
            "nice_to_haves": ["AI experience"],
        }
        prompt = build_tailoring_prompt(listing, "Resume content", "CL content", "Instructions")

        assert "MUST NOT fabricate" in prompt
        assert "TestCo" in prompt
        assert "Manager" in prompt
        assert "5+ years marketing" in prompt
        assert "Resume content" in prompt
        assert "CL content" in prompt
        assert "Instructions" in prompt

    def test_handles_empty_requirements(self):
        listing = {
            "company_name": "TestCo",
            "role_title": "Manager",
            "location": None,
            "key_requirements": [],
            "nice_to_haves": [],
        }
        prompt = build_tailoring_prompt(listing, "Resume", "CL", "")
        assert "Not specified" in prompt
        assert "None listed" in prompt


class TestParseTailoredOutput:
    def test_parses_correctly(self):
        response = """Here are the tailored documents:

===RESUME===
# Maya Rodriguez
Tailored resume content here.
===END_RESUME===

===COVER_LETTER===
Dear Hiring Manager,
Tailored cover letter content here.
===END_COVER_LETTER===
"""
        resume, cover_letter, notes = parse_tailored_output(response)
        assert "Maya Rodriguez" in resume
        assert "Tailored resume content" in resume
        assert "Dear Hiring Manager" in cover_letter
        assert "Tailored cover letter content" in cover_letter
        assert notes == ""

    def test_parses_with_notes(self):
        response = """===RESUME===
Resume content.
===END_RESUME===

===COVER_LETTER===
Cover letter content.
===END_COVER_LETTER===

===NOTES===
## What Changed
- Moved skills to top
===END_NOTES===
"""
        resume, cover_letter, notes = parse_tailored_output(response)
        assert "Resume content" in resume
        assert "Cover letter content" in cover_letter
        assert "What Changed" in notes

    def test_raises_on_missing_sections(self):
        with pytest.raises(ValueError, match="Could not parse"):
            parse_tailored_output("Some random text without delimiters")

    def test_raises_on_partial_sections(self):
        response = "===RESUME===\nContent\n===END_RESUME==="
        with pytest.raises(ValueError, match="Could not parse"):
            parse_tailored_output(response)
