"""Resume and cover letter tailoring agent: customises base documents per listing."""

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import anthropic
from dotenv import load_dotenv


from src.file_writer import update_section
from src.profile import ProfileError, load_profile
from src.utils import load_yaml, retry_with_backoff, save_yaml, setup_logging

logger = setup_logging("preparer")

TAILORING_PROMPT = """\
You are a resume and cover letter tailoring expert. Your job is to customise the \
candidate's base documents to best match a specific job listing.

## Base Resume
{resume}

## Base Cover Letter (content only — agent instructions removed)
{cover_letter}

## Agent Instructions (from the cover letter author)
{agent_instructions}

## Target Job Listing
Company: {company_name}
Role: {role_title}
Location: {location}
Key Requirements: {requirements}
Nice-to-Haves: {nice_to_haves}

## CRITICAL CONSTRAINT
You MUST NOT fabricate, invent, or embellish any experience, skill, certification, \
metric, or accomplishment that does not appear in the base documents. You may ONLY:
- Reorder sections to lead with the most relevant experience
- Adjust emphasis (expand relevant bullets, compress less relevant ones)
- Reframe existing experience using the listing's language and terminology
- Write a tailored professional summary drawing ONLY from existing content
- Adjust tone per the Agent Instructions above
- For the cover letter: replace [ROLE] and [COMPANY] placeholders with the actual values
- For the cover letter: adjust which achievements are highlighted based on the listing

If the candidate lacks a required skill, DO NOT add it. Leave the gap visible.

## Output Format
Return the tailored documents in this exact format:

===RESUME===
[Full tailored resume in markdown]
===END_RESUME===

===COVER_LETTER===
[Full tailored cover letter in markdown — do NOT include the Agent Instructions section]
===END_COVER_LETTER===

===NOTES===
[Tailoring notes in this exact format:

## What Changed
- [3-5 specific changes made to the resume — name the change, e.g. "Moved analytics certification to top of skills to match requirement" not just "resume was tailored"]

## Cover Letter Focus
[1-2 sentences: what angle/story was emphasised and why it fits this role]

## Verify Before Submitting
- [2-4 items to double-check: claims that rely on recency, metrics to confirm, gaps that may be probed]

## Watch Out For
- [1-2 concerns that remain visible despite tailoring — what the interviewer may push on]
]
===END_NOTES===
"""

VALIDATION_PROMPT = """\
You are a resume accuracy checker. Your job is to verify that every claim in the \
tailored output can be traced to the source documents.

## Source: Base Resume
{resume}

## Source: Candidate Profile (certifications are explicitly listed here)
{profile}

## Tailored Output to Verify
{tailored_output}

## Instructions
Check every technology, tool, skill, certification, title, and quantified result \
in the tailored output. Classify each claim as one of:
- CONFIRMED: present verbatim or by clear equivalence in source documents
- UNCERTAIN: plausible synthesis or phrasing change from source — could be real
- FABRICATED: not traceable to any source document

Apply STRICTER thresholds for cover letters than resumes — a claim that is only \
borderline for a resume should be FABRICATED for a cover letter.

Return a JSON object with this exact structure:
{{
  "fabricated": [
    {{
      "claim": "exact quote of the unverifiable claim",
      "location": "resume or cover_letter",
      "reason": "why this cannot be verified from source"
    }}
  ],
  "uncertain": [
    {{
      "claim": "exact quote",
      "location": "resume or cover_letter",
      "note": "what makes this uncertain"
    }}
  ],
  "summary": "one sentence summary of validation result"
}}

Return ONLY the JSON object, no other text.
"""

TARGETED_EDIT_PROMPT = """\
You are a precise document editor. You must remove or rewrite ONLY the flagged \
claims from the tailored documents. Everything else must remain IDENTICAL.

## Original Tailored Resume
{tailored_resume}

## Original Tailored Cover Letter
{tailored_cover_letter}

## Claims to Remove or Rewrite
{flagged_claims}

## Instructions
For each flagged claim:
- If it's a certification or specific skill not in the source: REMOVE it entirely
- If it's an embellished metric: REPLACE with "contributed to" or remove the specific number
- Do not change any text surrounding the flagged claim
- Do not regenerate — only edit the specific flagged text

Return the edited documents in this exact format:

===RESUME===
[Full edited resume]
===END_RESUME===

===COVER_LETTER===
[Full edited cover letter]
===END_COVER_LETTER===
"""


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-") or "unknown"


def load_base_documents(config_dir: Path, profile_dict: dict) -> tuple[str, str]:
    """Load resume and cover letter base files."""
    resume_path = config_dir.parent / profile_dict.get("resume_path", "config/resume_base.md")
    cover_letter_path = config_dir.parent / profile_dict.get("cover_letter_path", "config/cover_letter_base.md")

    if not resume_path.exists():
        raise FileNotFoundError(f"Resume base not found: {resume_path}")
    if not cover_letter_path.exists():
        raise FileNotFoundError(f"Cover letter base not found: {cover_letter_path}")

    resume = resume_path.read_text(encoding="utf-8")
    cover_letter = cover_letter_path.read_text(encoding="utf-8")
    return resume, cover_letter


def extract_agent_instructions(cover_letter_text: str) -> tuple[str, str]:
    """Extract the Agent Instructions section from cover letter base.

    Returns (clean_cover_letter, agent_instructions).
    """
    pattern = r"(?:^|\n)##\s*Agent Instructions.*"
    match = re.search(pattern, cover_letter_text, re.IGNORECASE)

    if match:
        clean = cover_letter_text[:match.start()].rstrip()
        instructions = cover_letter_text[match.start():].strip()
        return clean, instructions

    return cover_letter_text, ""


def build_tailoring_prompt(
    listing: dict, resume: str, cover_letter: str, instructions: str
) -> str:
    """Build the Claude prompt for tailoring."""
    requirements = listing.get("key_requirements", [])
    nice_to_haves = listing.get("nice_to_haves", [])

    return TAILORING_PROMPT.format(
        resume=resume,
        cover_letter=cover_letter,
        agent_instructions=instructions or "No specific instructions provided.",
        company_name=listing.get("company_name", "Unknown"),
        role_title=listing.get("role_title", "Unknown"),
        location=listing.get("location", "Not specified"),
        requirements="\n".join(f"- {r}" for r in requirements) if requirements else "Not specified",
        nice_to_haves="\n".join(f"- {n}" for n in nice_to_haves) if nice_to_haves else "None listed",
    )


def parse_tailored_output(response_text: str) -> tuple[str, str, str]:
    """Parse the Claude response into resume, cover letter, and notes sections."""
    resume_match = re.search(
        r"===RESUME===(.*?)===END_RESUME===", response_text, re.DOTALL
    )
    cover_letter_match = re.search(
        r"===COVER_LETTER===(.*?)===END_COVER_LETTER===", response_text, re.DOTALL
    )

    if not resume_match or not cover_letter_match:
        raise ValueError(
            "Could not parse tailored output — expected ===RESUME=== and ===COVER_LETTER=== sections"
        )

    notes_match = re.search(
        r"===NOTES===(.*?)===END_NOTES===", response_text, re.DOTALL
    )
    notes = notes_match.group(1).strip() if notes_match else ""
    return resume_match.group(1).strip(), cover_letter_match.group(1).strip(), notes


def validate_tailored_output(
    client: anthropic.Anthropic,
    tailored_resume: str,
    tailored_cover_letter: str,
    resume_base: str,
    profile_dict: dict,
) -> dict:
    """Run anti-fabrication validation pass on tailored documents.

    Returns dict with 'fabricated', 'uncertain', and 'summary' keys.
    On parse failure, returns {'fabricated': [], 'uncertain': [], 'summary': 'Validation parse failed — saved with warning.', 'parse_failed': True}
    """
    import yaml

    combined_output = (
        f"## RESUME\n{tailored_resume}\n\n"
        f"## COVER LETTER\n{tailored_cover_letter}"
    )

    prompt = VALIDATION_PROMPT.format(
        resume=resume_base,
        profile=yaml.dump(profile_dict, default_flow_style=False),
        tailored_output=combined_output,
    )

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

        result = json.loads(content)
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Validation response parse failed: {e}")
        return {
            "fabricated": [],
            "uncertain": [],
            "summary": "Validation parse failed — saved with warning.",
            "parse_failed": True,
        }
    except anthropic.APIError as e:
        logger.error(f"Validation API error: {e}")
        return {
            "fabricated": [],
            "uncertain": [],
            "summary": "Validation API call failed — saved with warning.",
            "parse_failed": True,
        }


def apply_targeted_edit(
    client: anthropic.Anthropic,
    tailored_resume: str,
    tailored_cover_letter: str,
    flagged_claims: list[dict],
) -> tuple[str, str]:
    """Apply targeted surgical edits to remove only flagged claims.

    Returns (edited_resume, edited_cover_letter). On failure, returns originals.
    """
    claims_text = "\n".join(
        f"- [{c['location']}] {c['claim']} — {c['reason']}"
        for c in flagged_claims
    )

    prompt = TARGETED_EDIT_PROMPT.format(
        tailored_resume=tailored_resume,
        tailored_cover_letter=tailored_cover_letter,
        flagged_claims=claims_text,
    )

    try:
        response = retry_with_backoff(
            fn=lambda: client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            ),
            max_retries=2,
            base_delay=3.0,
            retryable_exceptions=(anthropic.APIError,),
            logger=logger,
        )
        response_text = response.content[0].text
        edited_resume, edited_cover_letter, _ = parse_tailored_output(response_text)
        return edited_resume, edited_cover_letter

    except (ValueError, anthropic.APIError) as e:
        logger.error(f"Targeted edit failed: {e} — returning originals")
        return tailored_resume, tailored_cover_letter


def tailor_listing(
    client: anthropic.Anthropic,
    listing: dict,
    resume: str,
    cover_letter: str,
    instructions: str,
) -> tuple[str, str, str]:
    """Send to Claude for tailoring. Returns (tailored_resume, tailored_cover_letter, notes)."""
    prompt = build_tailoring_prompt(listing, resume, cover_letter, instructions)

    response = retry_with_backoff(
        fn=lambda: client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        ),
        max_retries=2,
        base_delay=3.0,
        retryable_exceptions=(anthropic.APIError,),
        logger=logger,
    )

    response_text = response.content[0].text
    return parse_tailored_output(response_text)


def save_prepared_documents(
    data_dir: Path,
    company: str,
    role: str,
    resume: str,
    cover_letter: str,
    notes: str = "",
    validation_notes: str = "",
) -> Path:
    """Save tailored docs to data/prepared/{company_slug}/{role_slug}/."""
    output_dir = data_dir / "prepared" / slugify(company) / slugify(role)
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "resume.md").write_text(resume, encoding="utf-8", newline="\n")
    (output_dir / "cover_letter.md").write_text(cover_letter, encoding="utf-8", newline="\n")

    combined_notes = notes
    if validation_notes:
        combined_notes += f"\n\n## Validation Notes\n{validation_notes}"

    if combined_notes:
        (output_dir / "notes.md").write_text(combined_notes, encoding="utf-8", newline="\n")

    logger.info(f"Saved tailored documents to {output_dir}")
    return output_dir


def mark_prepared(data_dir: Path, listing_url: str) -> None:
    """Set prepared=True for listing in processed_listings.yaml.

    Email tier: if the listing was selected via a PREPARE reply, clear the
    selection flag and queue the documents for email delivery (docs_pending).
    """
    output_path = data_dir / "processed_listings.yaml"
    data = load_yaml(output_path)
    if not data or "listings" not in data:
        return

    for listing in data["listings"]:
        if listing.get("url") == listing_url:
            listing["prepared"] = True
            listing["status"] = "prepared"
            if listing.get("selected_for_prep"):
                listing["selected_for_prep"] = False
                listing["docs_pending"] = True
            break

    save_yaml(output_path, data)


def mark_error(data_dir: Path, listing_url: str) -> None:
    """Set status=error for listing in processed_listings.yaml."""
    output_path = data_dir / "processed_listings.yaml"
    data = load_yaml(output_path)
    if not data or "listings" not in data:
        return

    for listing in data["listings"]:
        if listing.get("url") == listing_url:
            listing["status"] = "error"
            break

    save_yaml(output_path, data)


class Preparer:
    """Stateful preparer with configurable paths."""

    def __init__(
        self,
        config_dir: Path | None = None,
        data_dir: Path | None = None,
    ):
        self.config_dir = config_dir or (Path.cwd() / "config")
        self.data_dir = data_dir or (Path.cwd() / "data")

    def run(self, url: str | None = None, selected: bool = False) -> int:
        """Prepare documents.

        If url given, prepare that listing. If selected=True, prepare listings
        the user picked via a PREPARE reply (email tier). Otherwise, prepare
        everything above the dual-axis preparation threshold.

        Returns count of successfully prepared listings.
        """
        try:
            profile, rubric = load_profile(self.config_dir)
        except ProfileError as e:
            logger.error(str(e))
            return 0

        profile_dict = profile.model_dump()

        try:
            resume, cover_letter_raw = load_base_documents(self.config_dir, profile_dict)
        except FileNotFoundError as e:
            logger.error(str(e))
            return 0

        cover_letter, instructions = extract_agent_instructions(cover_letter_raw)

        data = load_yaml(self.data_dir / "processed_listings.yaml")
        if not data or "listings" not in data:
            logger.info("No processed listings found")
            return 0

        if url:
            listings = [l for l in data["listings"] if l.get("url") == url]
            if not listings:
                logger.error(f"No listing found for URL: {url}")
                return 0
        elif selected:
            # Email tier: only what the user explicitly picked — no threshold
            # gate (their choice overrides the recommendation)
            listings = [
                l for l in data["listings"]
                if l.get("selected_for_prep")
                and not l.get("prepared", False)
                and l.get("status") != "error"
            ]
        else:
            listings = [
                l for l in data["listings"]
                if rubric.is_above_prep_threshold(
                    l.get("skills_fit", 0), l.get("preference_fit", 0)
                )
                and not l.get("prepared", False)
                and l.get("status") != "error"
            ]

        if not listings:
            logger.info("No listings to prepare")
            return 0

        logger.info(f"Preparing {len(listings)} listing(s)...")
        client = anthropic.Anthropic()
        success_count = 0

        for i, listing in enumerate(listings):
            company = listing.get("company_name", "Unknown")
            role = listing.get("role_title", "Unknown")
            logger.info(f"Tailoring for {company} — {role}...")

            try:
                tailored_resume, tailored_cover_letter, tailoring_notes = tailor_listing(
                    client, listing, resume, cover_letter, instructions
                )

                # Anti-fabrication validation pass
                logger.info("Checking your draft for accuracy...")
                validation = validate_tailored_output(
                    client, tailored_resume, tailored_cover_letter, resume, profile_dict
                )

                validation_warning = ""
                if validation.get("parse_failed"):
                    validation_warning = f"⚠️ Validation check failed to run: {validation['summary']}"
                    logger.warning(validation_warning)
                elif validation.get("fabricated"):
                    # Surgically remove unverifiable claims before anything is saved.
                    logger.warning(
                        f"Found {len(validation['fabricated'])} unverifiable claim(s) "
                        f"in {company} documents — applying targeted edit"
                    )
                    tailored_resume, tailored_cover_letter = apply_targeted_edit(
                        client, tailored_resume, tailored_cover_letter,
                        validation["fabricated"],
                    )

                uncertain_notes = ""
                if validation.get("uncertain"):
                    uncertain_notes = "Uncertain claims (review before sending):\n" + "\n".join(
                        f"- [{c['location']}] {c['claim']}: {c['note']}"
                        for c in validation["uncertain"]
                    )

                combined_validation = "\n\n".join(filter(None, [validation_warning, uncertain_notes]))

                output_dir = save_prepared_documents(
                    self.data_dir, company, role,
                    tailored_resume, tailored_cover_letter,
                    tailoring_notes, combined_validation,
                )

                # Record what was flagged (and removed) in notes.md for user review
                if validation.get("fabricated"):
                    flags_body = (
                        "The following claims could not be verified against the source "
                        "resume and were removed by a targeted edit. Review the documents "
                        "before submitting.\n" + "\n".join(
                            f"- [{c['location']}] {c['claim']} — {c['reason']}"
                            for c in validation["fabricated"]
                        )
                    )
                    update_section(
                        output_dir / "notes.md", "fabrication_flags", flags_body
                    )

                mark_prepared(self.data_dir, listing["url"])
                success_count += 1
                logger.info(f"Prepared: {company} — {role}")

            except ValueError as e:
                logger.error(f"Parse error for {company} — {role}: {e}")
                mark_error(self.data_dir, listing["url"])
            except anthropic.APIError as e:
                logger.error(f"API error for {company} — {role}: {e}")
            except Exception as e:
                logger.error(f"Failed to prepare {company} — {role}: {e}")

            if i < len(listings) - 1:
                time.sleep(2)

        logger.info(f"Prepared {success_count}/{len(listings)} listing(s) successfully")
        return success_count


def main():
    load_dotenv(Path.cwd() / ".env", override=True)

    parser = argparse.ArgumentParser(description="Preparer: tailor resume and cover letter per listing")
    parser.add_argument("--url", help="Prepare a single listing by URL")
    parser.add_argument(
        "--selected", action="store_true",
        help="Prepare listings selected via PREPARE reply (email tier)",
    )
    args = parser.parse_args()

    preparer = Preparer()
    success = preparer.run(url=args.url, selected=args.selected)

    # In --selected mode, "nothing selected yet" is a normal scheduled-run
    # outcome, not a failure
    if success == 0 and not args.selected:
        sys.exit(1)


if __name__ == "__main__":
    main()
