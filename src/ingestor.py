"""Gmail URL collector: fetches self-sent JOB: emails and extracts listing URLs."""

import argparse
import imaplib
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


from src.utils import (
    detect_source,
    extract_urls,
    get_email_body,
    load_yaml,
    normalize_url,
    retry_with_backoff,
    save_yaml,
    setup_logging,
)

logger = setup_logging("ingestor")

GMAIL_HOST = "imap.gmail.com"
GMAIL_PORT = 993
SUBJECT_PREFIX = "JOB:"


class Ingestor:
    """Gmail URL ingestor with configurable data directory."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or (Path.cwd() / "data")

    def connect_gmail(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP using env vars."""
        address = os.environ.get("GMAIL_ADDRESS")
        password = os.environ.get("GMAIL_APP_PASSWORD")

        if not address or not password:
            raise RuntimeError(
                "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env. "
                "Gmail App Passwords require 2FA enabled — see https://myaccount.google.com/apppasswords"
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

    def fetch_job_emails(
        self,
        conn: imaplib.IMAP4_SSL,
        processed_ids: set[str],
    ) -> list[dict]:
        """Search for unprocessed JOB: emails. Returns list of {uid, subject, urls}."""
        import email as email_lib

        address = os.environ.get("GMAIL_ADDRESS", "")
        conn.select("INBOX")

        search_criteria = f'(FROM "{address}" TO "{address}" SUBJECT "{SUBJECT_PREFIX}")'
        status, data = conn.uid("search", None, search_criteria)

        if status != "OK" or not data[0]:
            logger.info("No JOB: emails found")
            return []

        uids = data[0].decode().split()
        new_emails = []

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

            urls = extract_urls(body)
            if urls:
                logger.info(f"Found {len(urls)} URL(s) in email: {subject}")
            else:
                logger.warning(f"No URLs found in email: {subject}")
            # Record no-URL emails too (empty urls list) — otherwise their UID
            # is never saved to processed_reply_ids and they are re-fetched on
            # every future run forever
            new_emails.append({"uid": uid, "subject": subject, "urls": urls})

            conn.uid("store", uid, "+FLAGS", "\\Seen")

        return new_emails

    def append_to_input_listings(self, new_urls: list[str]) -> int:
        """Append new URLs to input_listings.yaml, deduping against existing data.

        Returns count of URLs added.
        """
        input_path = self.data_dir / "input_listings.yaml"
        processed_path = self.data_dir / "processed_listings.yaml"

        input_data = load_yaml(input_path)
        if not input_data or "listings" not in input_data:
            input_data = {"listings": []}

        processed_data = load_yaml(processed_path)
        if not processed_data or "listings" not in processed_data:
            processed_data = {"listings": []}

        existing_urls = {normalize_url(l.get("url", "")) for l in input_data["listings"]}
        existing_urls.update(normalize_url(l.get("url", "")) for l in processed_data["listings"])

        added = 0
        for url in new_urls:
            normalized = normalize_url(url)
            if normalized in existing_urls:
                logger.debug(f"Skipping duplicate URL: {url}")
                continue

            input_data["listings"].append({
                "url": url,
                "source": detect_source(url),
                "date_added": str(date.today()),
                "status": "queued",
            })
            existing_urls.add(normalized)
            added += 1

        if added > 0:
            save_yaml(input_path, input_data)
            logger.info(f"Added {added} new URL(s) to input_listings.yaml")
        else:
            logger.info("No new URLs to add (all duplicates)")

        return added

    def run(self) -> int:
        """Run the full ingestor flow. Returns count of new listings added."""
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
            emails = self.fetch_job_emails(conn, all_ids["ingestor_ids"])

            if not emails:
                logger.info("No new JOB: emails to process")
                return 0

            all_urls = []
            new_uids = set()
            for em in emails:
                all_urls.extend(em["urls"])
                new_uids.add(em["uid"])

            added = self.append_to_input_listings(all_urls)

            all_ids["ingestor_ids"].update(new_uids)
            self.save_processed_ids(all_ids)

            logger.info(
                f"Processed {len(emails)} email(s), extracted {len(all_urls)} URL(s), "
                f"added {added} new listing(s)"
            )
            return added
        finally:
            conn.logout()


# Module-level convenience functions for backward compatibility with tests
def load_processed_ids() -> dict[str, set[str]]:
    return Ingestor().load_processed_ids()


def save_processed_ids(all_ids: dict[str, set[str]]) -> None:
    Ingestor().save_processed_ids(all_ids)


def append_to_input_listings(new_urls: list[str]) -> int:
    return Ingestor().append_to_input_listings(new_urls)


def fetch_job_emails(conn: imaplib.IMAP4_SSL, processed_ids: set[str]) -> list[dict]:
    return Ingestor().fetch_job_emails(conn, processed_ids)


def main():
    load_dotenv(Path.cwd() / ".env", override=True)

    parser = argparse.ArgumentParser(description="Ingestor: collect job URLs from Gmail")
    parser.parse_args()

    ingestor = Ingestor()
    try:
        ingestor.run()
    except Exception as e:
        logger.error(f"Ingestor failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
