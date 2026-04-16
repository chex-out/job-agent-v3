"""Reply processor: reads Gmail replies with status keywords and updates listings + coaching state."""

import argparse
import imaplib
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env", override=True)

from src.coach_bridge import CoachBridge
from src.utils import get_email_body, load_yaml, resolve_company_name, retry_with_backoff, save_yaml, setup_logging

logger = setup_logging("feedback")

GMAIL_HOST = "imap.gmail.com"
GMAIL_PORT = 993

STATUS_KEYWORDS = {"applied", "skip", "interviewed", "rejected", "offer", "review"}

STATUS_PATTERN = re.compile(
    r"\b(applied|skip|interviewed|rejected|offer|review)\s+(.+?)(?:\s*$|\s*[,;.\n])",
    re.IGNORECASE | re.MULTILINE,
)


class FeedbackProcessor:
    """Gmail reply processor with configurable data directory."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or (Path.cwd() / "data")

    def connect_gmail(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP using env vars."""
        address = os.environ.get("GMAIL_ADDRESS")
        password = os.environ.get("GMAIL_APP_PASSWORD")

        if not address or not password:
            raise RuntimeError(
                "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env"
            )

        conn = imaplib.IMAP4_SSL(GMAIL_HOST, GMAIL_PORT)
        conn.login(address, password)
        logger.info(f"Connected to Gmail as {address}")
        return conn

    def load_processed_ids(self) -> dict[str, set[str]]:
        """Load processed email IDs from YAML."""
        data = load_yaml(self.data_dir / "processed_reply_ids.yaml")
        return {
            "ingestor_ids": set(data.get("ingestor_ids", [])),
            "feedback_ids": set(data.get("feedback_ids", [])),
        }

    def save_processed_ids(self, all_ids: dict[str, set[str]]) -> None:
        """Save processed email IDs back to YAML."""
        data = {
            "ingestor_ids": sorted(all_ids.get("ingestor_ids", set())),
            "feedback_ids": sorted(all_ids.get("feedback_ids", set())),
        }
        save_yaml(self.data_dir / "processed_reply_ids.yaml", data)

    def fetch_feedback_emails(
        self,
        conn: imaplib.IMAP4_SSL,
        processed_ids: set[str],
    ) -> list[dict]:
        """Fetch emails containing status keywords."""
        import email as email_lib

        address = os.environ.get("GMAIL_ADDRESS", "")
        conn.select("INBOX")

        results = []
        for keyword in STATUS_KEYWORDS:
            search_criteria = f'(FROM "{address}" SUBJECT "{keyword}")'
            status, data = conn.uid("search", None, search_criteria)

            if status != "OK" or not data[0]:
                continue

            uids = data[0].decode().split()
            for uid in uids:
                if uid in processed_ids:
                    continue

                status, msg_data = conn.uid("fetch", uid, "(RFC822)")
                if status != "OK" or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw_email)
                subject = msg.get("Subject", "")
                body = get_email_body(msg)

                results.append({"uid": uid, "subject": subject, "body": body})

        seen = set()
        deduped = []
        for r in results:
            if r["uid"] not in seen:
                seen.add(r["uid"])
                deduped.append(r)

        return deduped

    def run(self) -> int:
        """Run the full feedback flow. Returns count of status updates applied."""
        try:
            conn = retry_with_backoff(
                fn=self.connect_gmail,
                max_retries=2,
                base_delay=3.0,
                retryable_exceptions=(imaplib.IMAP4.error, OSError),
                logger=logger,
            )
        except Exception as e:
            logger.error(f"Gmail connection failed after retries: {e}")
            return 0

        try:
            all_ids = self.load_processed_ids()
            emails = self.fetch_feedback_emails(conn, all_ids["feedback_ids"])

            if not emails:
                logger.info("No new feedback emails to process")
                return 0

            listings_data = load_yaml(self.data_dir / "processed_listings.yaml")
            if not listings_data or "listings" not in listings_data:
                logger.info("No processed listings to match against")
                return 0

            known_companies = [
                l.get("company_name") for l in listings_data["listings"]
                if l.get("company_name")
            ]

            bridge = CoachBridge()
            total_updates = 0
            new_uids = set()

            for em in emails:
                updates = parse_status_update(em["subject"], em["body"], known_companies)
                has_ambiguous = any(u.get("ambiguous") for u in updates)

                for update in updates:
                    if update.get("ambiguous"):
                        continue
                    if apply_status_update(update, bridge, listings_data):
                        total_updates += 1

                if not has_ambiguous:
                    new_uids.add(em["uid"])
                else:
                    logger.info(
                        f"Email '{em['subject']}' has ambiguous matches — will retry next run"
                    )

            if total_updates > 0:
                save_yaml(self.data_dir / "processed_listings.yaml", listings_data)

            all_ids["feedback_ids"].update(new_uids)
            self.save_processed_ids(all_ids)

            logger.info(
                f"Processed {len(emails)} email(s), applied {total_updates} status update(s)"
            )
            return total_updates
        finally:
            conn.logout()


def parse_status_update(
    subject: str, body: str, known_companies: list[str]
) -> list[dict]:
    """Extract status updates from email content.

    Returns list of {company, status, raw_company, ambiguous} dicts.
    """
    updates = []
    text = f"{subject}\n{body}"
    matches = STATUS_PATTERN.findall(text)

    for keyword, raw_company in matches:
        raw_company = raw_company.strip()
        if not raw_company:
            continue

        matched, confidence = resolve_company_name(raw_company, known_companies)

        if matched is None:
            logger.warning(f"No matching company found for '{raw_company}'. Skipping.")
            continue

        if confidence < 95:
            logger.warning(
                f"Fuzzy match '{raw_company}' -> '{matched}' (confidence: {confidence:.0f}%). "
                f"Will retry next run — send exact company name to confirm."
            )
            updates.append({
                "company": raw_company,
                "status": keyword.lower(),
                "raw_company": raw_company,
                "ambiguous": True,
            })
            continue

        updates.append({
            "company": matched,
            "status": keyword.lower(),
            "raw_company": raw_company,
            "ambiguous": False,
        })

    return updates


def apply_status_update(
    update: dict, bridge: CoachBridge, listings_data: dict
) -> bool:
    """Apply a single status update to listings and coaching_state.md.

    Returns True if update was applied.
    """
    company = update["company"]
    status = update["status"]

    listing = None
    for l in listings_data.get("listings", []):
        if l.get("company_name", "").lower() == company.lower():
            listing = l
            break

    if not listing:
        logger.warning(f"No listing found for company '{company}' in processed data")
        return False

    role = listing.get("role_title", "Unknown")

    if status == "applied":
        listing["status"] = "applied"
        bridge.update_loop_status(company, "Applied")
        logger.info(f"Updated {company} to Applied")

    elif status == "skip":
        listing["status"] = "skipped"
        logger.info(f"Updated {company} to Skipped")

    elif status == "interviewed":
        listing["status"] = "interviewing"
        bridge.update_loop_status(company, "Interviewing")
        logger.info(f"Updated {company} to Interviewing")

    elif status == "rejected":
        listing["status"] = "rejected"
        bridge.add_outcome(company, role, "Unknown", "rejected")
        logger.info(f"Updated {company} to Rejected + added outcome")

    elif status == "offer":
        listing["status"] = "offer"
        bridge.add_outcome(company, role, "Unknown", "offer")
        logger.info(f"Updated {company} to Offer + added outcome")

    elif status == "review":
        listing["status"] = "under_review"
        logger.info(f"Updated {company} to Under Review")

    else:
        logger.warning(f"Unknown status keyword: {status}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Feedback: process email replies to update listing statuses"
    )
    parser.parse_args()

    processor = FeedbackProcessor()
    try:
        processor.run()
    except Exception as e:
        logger.error(f"Feedback processor failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
