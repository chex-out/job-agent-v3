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

    def send(self, html: str, subject: str, attachments: list[dict] | None = None) -> bool:
        """Send an email via Resend API (optionally with attachments). Returns True on success."""
        api_key = os.environ.get("RESEND_API_KEY")
        to_email = os.environ.get("DIGEST_TO_EMAIL")
        from_email = os.environ.get("DIGEST_FROM_EMAIL", "onboarding@resend.dev")

        if not api_key or not to_email:
            logger.error("RESEND_API_KEY and DIGEST_TO_EMAIL must be set in .env")
            return False

        resend.api_key = api_key

        payload = {
            "from": f"Job Agent <{from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
        if attachments:
            payload["attachments"] = attachments

        try:
            result = retry_with_backoff(
                fn=lambda: resend.Emails.send(payload),
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


DOCS_EMAIL_TEMPLATE = """\
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
            Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a1a2e;">Your tailored documents: {company} — {role}</h2>
  <p>Attached are your tailored resume, cover letter, and preparation notes.</p>
  <p><strong>Before you submit:</strong> open the notes file and check the
  "Verify Before Submitting" section — it lists the claims worth
  double-checking and the concerns an interviewer may push on.</p>
  <p style="color: #888; font-size: 13px;">Every claim was checked against
  your source resume; anything unverifiable was removed and is listed in the
  notes under "Fabrication Flags".</p>
</div>
"""


class DocumentDelivery:
    """Email tier: send prepared documents as attachments for selected listings."""

    def __init__(self, digest: "Digest"):
        self.digest = digest
        self.data_dir = digest.data_dir

    def pending_listings(self, data: dict) -> list[dict]:
        return [l for l in data.get("listings", []) if l.get("docs_pending")]

    def build_attachments(self, listing: dict) -> list[dict]:
        """Read the prepared files for a listing and return resend attachments."""
        import base64

        from src.preparer import slugify

        company_slug = slugify(listing.get("company_name", "unknown"))
        role_slug = slugify(listing.get("role_title", "unknown"))
        prepared_dir = self.data_dir / "prepared" / company_slug / role_slug

        attachments = []
        for fname in ("resume.md", "cover_letter.md", "notes.md"):
            path = prepared_dir / fname
            if not path.exists():
                logger.warning(f"Prepared file missing, skipping attachment: {path}")
                continue
            content = base64.b64encode(path.read_bytes()).decode("ascii")
            attachments.append({
                "filename": f"{company_slug}-{fname}",
                "content": content,
            })
        return attachments

    def run(self) -> int:
        """Send docs for every docs_pending listing. Returns count delivered."""
        output_path = self.data_dir / "processed_listings.yaml"
        data = load_yaml(output_path)
        pending = self.pending_listings(data)
        if not pending:
            logger.info("No prepared documents awaiting delivery")
            return 0

        delivered = 0
        for listing in pending:
            company = listing.get("company_name", "Unknown")
            role = listing.get("role_title", "Unknown")
            attachments = self.build_attachments(listing)
            if not attachments:
                logger.error(f"No files found to deliver for {company} — {role}")
                continue

            html = DOCS_EMAIL_TEMPLATE.format(company=company, role=role)
            subject = f"Your tailored documents: {company} — {role}"
            if self.digest.send(html, subject, attachments=attachments):
                listing["docs_pending"] = False
                delivered += 1

        if delivered:
            save_yaml(output_path, data)
        logger.info(f"Delivered documents for {delivered}/{len(pending)} listing(s)")
        return delivered


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
    parser.add_argument(
        "--send-docs", action="store_true",
        help="Email prepared documents for PREPARE-selected listings (email tier)",
    )
    args = parser.parse_args()

    d = Digest()

    if args.send_docs:
        DocumentDelivery(d).run()
        return

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

    # Number every listing and persist the number->URL map so a PREPARE reply
    # ("PREPARE 2 5") can be resolved next feedback run. Numbers continue from
    # previous digests (merge, never overwrite) so a reply to an OLD digest
    # email still resolves to the right listings.
    map_path = d.data_dir / "last_digest_map.yaml"
    digest_map: dict = load_yaml(map_path) or {}
    ref = max((int(k) for k in digest_map.keys()), default=0)
    for tier_name in ("top_fit", "watchlist", "passed"):
        for listing in tiers[tier_name]:
            ref += 1
            listing["ref"] = ref
            digest_map[str(ref)] = listing.get("url", "")
    save_yaml(map_path, digest_map)

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
