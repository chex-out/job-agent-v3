"""Scout agent: fetches job listing pages and scores them against the user profile."""

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env", override=True)

from src.coach_bridge import CoachBridge
from src.models import ListingInput, ListingSource, ListingStatus, ScoredListing
from src.profile import ProfileError, load_profile
from src.utils import (
    detect_source,
    fetch_page_text,
    load_yaml,
    resolve_company_name,
    retry_with_backoff,
    save_yaml,
    setup_logging,
)

logger = setup_logging("scout")

SCORING_PROMPT = """\
You are a job listing evaluator. Score this listing against the candidate's profile using two separate scores.

## Candidate Profile
{profile_yaml}

## Scoring Rubric
{rubric_yaml}

## Job Listing Content
{listing_text}

## Instructions
Analyze the job listing and score it against the candidate's profile. Return a JSON object with exactly these fields:

{{
  "company_name": "string — the company name",
  "role_title": "string — the job title",
  "location": "string or null — job location",
  "job_type": "string or null — full-time, part-time, contract, etc.",
  "key_requirements": ["list of key requirements from the listing"],
  "nice_to_haves": ["list of nice-to-have qualifications"],
  "salary_range": "string or null — if mentioned",
  "skills_fit": integer 0-10,
  "skills_reasoning": "2-3 sentences: which skills matched, seniority fit, location fit, any deal-breaker applied",
  "preference_fit": integer 0-10,
  "preference_reasoning": "2-3 sentences: evidence from JD for preference fit, role scope match, company fit, any deal-breaker applied",
  "concerns": ["list of specific mismatches or risks for this candidate"],
  "strengths": ["list of specific strong matches between candidate and listing"]
}}

Scoring guidelines:
- Score skills_fit using the skills_fit criteria in the rubric. Apply deal-breakers as instructed.
- Score preference_fit using the preference_fit criteria in the rubric. Apply deal-breakers as instructed.
- skills_fit 7+: candidate could perform this role well.
- preference_fit 6+: this aligns with what the candidate wants.
- Be specific in reasoning — reference actual JD language as evidence.
- Be honest about mismatches — don't inflate scores.

Do NOT include the following as concerns — they are not scoring criteria:
- Whether the role is IC vs manager, team management scope, headcount, or leadership trajectory
- Management growth path or promotion trajectory
Only list concerns that directly map to the rubric dimensions (skills mismatch, location, scope mismatch, deal-breaker conditions).

Return ONLY the JSON object, no other text.
"""


def build_scoring_prompt(listing_text: str, profile_dict: dict, rubric_dict: dict) -> str:
    """Build the Claude scoring prompt with injected context."""
    import yaml

    return SCORING_PROMPT.format(
        profile_yaml=yaml.dump(profile_dict, default_flow_style=False),
        rubric_yaml=yaml.dump(rubric_dict, default_flow_style=False),
        listing_text=listing_text[:8000],
    )


def score_listing(
    client: anthropic.Anthropic, listing_text: str, profile_dict: dict, rubric_dict: dict
) -> dict | None:
    """Send listing text to Claude for scoring. Returns parsed JSON dict or None."""
    prompt = build_scoring_prompt(listing_text, profile_dict, rubric_dict)

    try:
        response = retry_with_backoff(
            fn=lambda: client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            ),
            max_retries=2,
            base_delay=3.0,
            retryable_exceptions=(anthropic.APIError,),
            logger=logger,
        )
        content = response.content[0].text.strip()

        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        return json.loads(content)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        return None
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error after retries: {e}")
        return None


class Scout:
    """Stateful scorer with configurable paths."""

    def __init__(
        self,
        config_dir: Path | None = None,
        data_dir: Path | None = None,
    ):
        self.config_dir = config_dir or (Path.cwd() / "config")
        self.data_dir = data_dir or (Path.cwd() / "data")

    def _load_profile_and_rubric(self) -> tuple[dict, dict] | tuple[None, None]:
        """Load profile.yaml and return (profile_dict, rubric_dict) or (None, None)."""
        try:
            profile, rubric = load_profile(self.config_dir)
        except ProfileError as e:
            logger.error(str(e))
            return None, None

        profile_dict = profile.model_dump()
        rubric_dict = {
            "threshold_for_preparation": rubric.threshold_for_preparation,
            "threshold_for_coaching": rubric.threshold_for_coaching,
            "dimensions": rubric.dimensions,
        }
        return profile_dict, rubric_dict

    def score_single_url(
        self,
        url: str,
        source: str = "other",
        prefetched_text: str | None = None,
    ) -> "ScoredListing | None":
        """Fetch and score a single URL. Returns a ScoredListing or None."""
        profile_dict, rubric_dict = self._load_profile_and_rubric()
        if profile_dict is None:
            return None

        if prefetched_text:
            text = prefetched_text
            logger.info(f"Using prefetched text ({len(text)} chars) for {url}")
        else:
            logger.info(f"Fetching: {url}")
            text = fetch_page_text(url)
            if not text:
                logger.error(f"Could not extract text from {url}")
                return None

        logger.info(f"Scoring against profile ({len(text)} chars extracted)...")
        client = anthropic.Anthropic()
        result = score_listing(client, text, profile_dict, rubric_dict)
        if not result:
            return None

        # Normalize company name against existing processed listings
        raw_company = result.get("company_name", "Unknown")
        output_path = self.data_dir / "processed_listings.yaml"
        processed_data = load_yaml(output_path)
        if processed_data and "listings" in processed_data:
            known_companies = [
                l.get("company_name") for l in processed_data["listings"]
                if l.get("company_name")
            ]
            canonical, confidence = resolve_company_name(raw_company, known_companies)
            if canonical and confidence >= 95:
                if canonical != raw_company:
                    logger.info(
                        f"Normalized company name: '{raw_company}' -> '{canonical}' "
                        f"(confidence: {confidence:.0f}%)"
                    )
                raw_company = canonical

        scored = ScoredListing(
            url=url,
            source=ListingSource(source),
            date_added=date.today(),
            date_scored=date.today(),
            company_name=raw_company,
            role_title=result.get("role_title", "Unknown"),
            location=result.get("location"),
            job_type=result.get("job_type"),
            key_requirements=result.get("key_requirements", []),
            nice_to_haves=result.get("nice_to_haves", []),
            salary_range=result.get("salary_range"),
            skills_fit=result.get("skills_fit", 0),
            preference_fit=result.get("preference_fit", 0),
            skills_reasoning=result.get("skills_reasoning", ""),
            preference_reasoning=result.get("preference_reasoning", ""),
            concerns=result.get("concerns", []),
            strengths=result.get("strengths", []),
        )

        logger.info(
            f"Scored: {scored.company_name} — {scored.role_title} — "
            f"Skills: {scored.skills_fit}/10, Pref: {scored.preference_fit}/10 ({scored.fit_assessment})"
        )

        # Write to coaching_state.md if above coaching threshold
        profile, rubric = load_profile(self.config_dir)
        if rubric.is_above_coaching_threshold(scored.skills_fit, scored.preference_fit):
            bridge = CoachBridge()
            signals = scored.skills_reasoning[:200]
            bridge.write_research_entry(
                company_name=scored.company_name,
                fit_assessment=scored.fit_assessment,
                key_signals=signals,
                skills_fit=scored.skills_fit,
                preference_fit=scored.preference_fit,
            )

        return scored

    def run_batch(self) -> list["ScoredListing"]:
        """Score all queued listings from input_listings.yaml."""
        input_path = self.data_dir / "input_listings.yaml"
        output_path = self.data_dir / "processed_listings.yaml"

        listings_data = load_yaml(input_path)
        if not listings_data or "listings" not in listings_data:
            logger.info("No queued listings found")
            return []

        processed_data = load_yaml(output_path)
        if not processed_data or "listings" not in processed_data:
            processed_data = {"listings": []}

        processed_urls = {l["url"] for l in processed_data["listings"]}

        queued = [
            l for l in listings_data["listings"]
            if l.get("status") == "queued" and l.get("url") not in processed_urls
        ]

        if not queued:
            logger.info("No new queued listings to score")
            return []

        logger.info(f"Scoring {len(queued)} queued listings...")
        scored_listings = []

        for i, listing in enumerate(queued):
            url = listing["url"]
            source = listing.get("source", detect_source(url))
            prefetched_text = listing.get("prefetched_text")

            scored = self.score_single_url(url, source, prefetched_text=prefetched_text)
            if scored:
                scored_listings.append(scored)
                processed_data["listings"].append(scored.model_dump(mode="json"))
                listing["status"] = "scored"
                listing["company_name"] = scored.company_name
                listing["role_title"] = scored.role_title
            else:
                listing["status"] = "error"
                logger.warning(f"Failed to score: {url}")

            if i < len(queued) - 1:
                time.sleep(2)

        save_yaml(input_path, listings_data)
        save_yaml(output_path, processed_data)

        _, rubric = load_profile(self.config_dir)
        above = [s for s in scored_listings if rubric.is_above_prep_threshold(s.skills_fit, s.preference_fit)]
        logger.info(f"Done: {len(scored_listings)} scored, {len(above)} above threshold")
        return scored_listings


def main():
    parser = argparse.ArgumentParser(description="Scout: fetch and score job listings")
    parser.add_argument("--url", help="Score a single URL")
    parser.add_argument("--source", default="other", help="Listing source")
    parser.add_argument("--text-file", help="Path to pre-fetched listing text")
    args = parser.parse_args()

    scout = Scout()

    if args.url:
        prefetched = None
        if args.text_file:
            prefetched = Path(args.text_file).read_text(encoding="utf-8")
        scored = scout.score_single_url(args.url, args.source, prefetched_text=prefetched)
        if scored:
            output_path = Path.cwd() / "data" / "processed_listings.yaml"
            processed_data = load_yaml(output_path)
            if not processed_data or "listings" not in processed_data:
                processed_data = {"listings": []}
            processed_data["listings"].append(scored.model_dump(mode="json"))
            save_yaml(output_path, processed_data)
            logger.info(f"Saved to {output_path}")
        else:
            logger.error("Failed to score listing")
            sys.exit(1)
    else:
        results = scout.run_batch()
        input_data = load_yaml(Path.cwd() / "data" / "input_listings.yaml")
        queued = [
            l for l in (input_data.get("listings") or [])
            if l.get("status") == "queued"
        ]
        if queued and not results:
            logger.error(f"All {len(queued)} queued listings failed to score")
            sys.exit(1)


if __name__ == "__main__":
    main()
