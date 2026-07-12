"""Email digest builder: groups scored listings by tier and sends via Resend."""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

import resend
from jinja2 import Environment, FileSystemLoader

from src.models import ScoringRubric
from src.utils import load_yaml, retry_with_backoff, save_yaml, setup_logging

logger = setup_logging("digest")


class Digest:
    """Stateful digest builder with configurable paths."""

    def __init__(
        self,
        data_dir: Path | None = None,
        template_dir: Path | None = None,
    ):
        self.data_dir = data_dir or (Path.cwd() / "data")
        self.template_dir = template_dir or (Path.cwd() / "config" / "templates")

    def load_undigested_listings(self) -> list[dict]:
        """Load listings from processed_listings.yaml where digested=False."""
        data = load_yaml(self.data_dir / "processed_listings.yaml")
        if not data or "listings" not in data:
            return []
        return [l for l in data["listings"] if not l.get("digested", False)]

    def load_listing_by_url(self, url: str) -> list[dict]:
        """Load a specific listing by URL."""
        data = load_yaml(self.data_dir / "processed_listings.yaml")
        if not data or "listings" not in data:
            return []
        return [l for l in data["listings"] if l.get("url") == url]

    def mark_digested(self, listings: list[dict]) -> None:
        """Set digested=True for all sent listings in processed_listings.yaml."""
        output_path = self.data_dir / "processed_listings.yaml"
        data = load_yaml(output_path)
        if not data or "listings" not in data:
            return

        sent_urls = {l["url"] for l in listings}
        for listing in data["listings"]:
            if listing.get("url") in sent_urls:
                listing["digested"] = True

        save_yaml(output_path, data)
        logger.info(f"Marked {len(sent_urls)} listing(s) as digested")

    def render_html(self, tiers: dict, stats: dict) -> str:
        """Render the Jinja2 digest template with listing data."""
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
        )
        template = env.get_template("digest_email.html")
        return template.render(
            tiers=tiers,
            stats=stats,
            digest_date=str(date.today()),
        )

    def send(self, html: str, subject: str) -> bool:
        """Send digest email via Resend API. Returns True on success."""
        api_key = os.environ.get("RESEND_API_KEY")
        to_email = os.environ.get("DIGEST_TO_EMAIL")
        from_email = os.environ.get("DIGEST_FROM_EMAIL", "onboarding@resend.dev")

        if not api_key or not to_email:
            logger.error("RESEND_API_KEY and DIGEST_TO_EMAIL must be set in .env")
            return False

        resend.api_key = api_key

        try:
            result = retry_with_backoff(
                fn=lambda: resend.Emails.send({
                    "from": f"Job Agent <{from_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                }),
                max_retries=2,
                base_delay=3.0,
                retryable_exceptions=(Exception,),
                logger=logger,
            )
            logger.info(f"Digest sent successfully: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to send digest after retries: {e}")
            return False


def group_by_tier(
    listings: list[dict], rubric: "ScoringRubric | None" = None
) -> dict[str, list[dict]]:
    """Group listings into top_fit, watchlist, passed based on scores.

    top_fit uses the rubric's preparation threshold (both axes); watchlist is
    within 1 point of it on both axes. Falls back to default thresholds when
    no rubric is given.
    """
    if rubric is None:
        rubric = ScoringRubric()
    prep = rubric.threshold_for_preparation
    tiers: dict[str, list[dict]] = {"top_fit": [], "watchlist": [], "passed": []}
    for listing in listings:
        sf = listing.get("skills_fit", 0)
        pf = listing.get("preference_fit", 0)
        if rubric.is_above_prep_threshold(sf, pf):
            tiers["top_fit"].append(listing)
        elif sf >= prep.skills_fit_min - 1 and pf >= prep.preference_fit_min - 1:
            tiers["watchlist"].append(listing)
        else:
            tiers["passed"].append(listing)

    for key in tiers:
        tiers[key].sort(
            key=lambda l: (l.get("skills_fit", 0) + l.get("preference_fit", 0)),
            reverse=True,
        )

    return tiers


# Module-level convenience wrappers for backward compatibility with tests
def load_undigested_listings() -> list[dict]:
    return Digest().load_undigested_listings()


def mark_digested(listings: list[dict]) -> None:
    Digest().mark_digested(listings)


def render_digest_html(tiers: dict, stats: dict) -> str:
    return Digest().render_html(tiers, stats)


def main():
    load_dotenv(Path.cwd() / ".env", override=True)

    parser = argparse.ArgumentParser(description="Digest: build and send job search email digest")
    parser.add_argument("--dry-run", action="store_true", help="Render HTML but don't send email")
    parser.add_argument("--url", help="Send digest for a single listing by URL")
    args = parser.parse_args()

    d = Digest()

    # Tier with the user's configured thresholds when a profile is available
    try:
        from src.profile import load_profile

        _, rubric = load_profile(Path.cwd() / "config")
    except Exception:
        rubric = None

    if args.url:
        listings = d.load_listing_by_url(args.url)
        if not listings:
            logger.error(f"No listing found for URL: {args.url}")
            return
    else:
        listings = d.load_undigested_listings()
        if not listings:
            logger.info("No undigested listings to send")
            return

    tiers = group_by_tier(listings, rubric)
    stats = {
        "total": len(listings),
        "top_count": len(tiers["top_fit"]),
        "watch_count": len(tiers["watchlist"]),
        "pass_count": len(tiers["passed"]),
    }

    html = d.render_html(tiers, stats)

    if args.dry_run:
        preview_path = d.data_dir / "digest_preview.html"
        preview_path.write_text(html, encoding="utf-8", newline="\n")
        logger.info(f"Dry run: saved preview to {preview_path}")
        return

    if args.url:
        company = listings[0].get("company_name", "Unknown")
        role = listings[0].get("role_title", "Unknown")
        score = listings[0].get("skills_fit") or listings[0].get("fit_score", "?")
        subject = f"Job Agent: {company} — {role} (Score: {score}/10)"
    else:
        subject = f"Job Search Digest — {date.today()}"

    if d.send(html, subject):
        d.mark_digested(listings)
    else:
        logger.error("Digest not sent — listings remain undigested")
        sys.exit(1)


if __name__ == "__main__":
    main()
