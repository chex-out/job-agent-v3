"""Tests for ingestor.py — Gmail URL extraction and dedup logic."""

import pytest

from src.ingestor import Ingestor
from src.utils import load_yaml, save_yaml


@pytest.fixture
def ingestor(tmp_path):
    """Create an Ingestor with a temporary data directory."""
    return Ingestor(data_dir=tmp_path)


@pytest.fixture
def empty_input_listings(ingestor):
    """Create an empty input_listings.yaml."""
    save_yaml(ingestor.data_dir / "input_listings.yaml", {"listings": []})
    return ingestor.data_dir / "input_listings.yaml"


@pytest.fixture
def existing_listings(ingestor):
    """Create input_listings.yaml with one existing URL and processed_listings.yaml with one scored."""
    save_yaml(ingestor.data_dir / "input_listings.yaml", {
        "listings": [
            {"url": "https://example.com/existing", "source": "other", "status": "queued"}
        ]
    })
    save_yaml(ingestor.data_dir / "processed_listings.yaml", {
        "listings": [
            {"url": "https://example.com/scored", "source": "other", "status": "scored"}
        ]
    })
    return ingestor


class TestAppendToInputListings:
    def test_adds_new_urls(self, ingestor, empty_input_listings):
        urls = ["https://example.com/job1", "https://example.com/job2"]
        added = ingestor.append_to_input_listings(urls)

        assert added == 2
        data = load_yaml(ingestor.data_dir / "input_listings.yaml")
        assert len(data["listings"]) == 2
        assert data["listings"][0]["url"] == "https://example.com/job1"
        assert data["listings"][0]["status"] == "queued"

    def test_dedup_against_input_listings(self, existing_listings):
        urls = ["https://example.com/existing", "https://example.com/new"]
        added = existing_listings.append_to_input_listings(urls)

        assert added == 1
        data = load_yaml(existing_listings.data_dir / "input_listings.yaml")
        assert len(data["listings"]) == 2  # original + 1 new

    def test_dedup_against_processed_listings(self, existing_listings):
        urls = ["https://example.com/scored", "https://example.com/fresh"]
        added = existing_listings.append_to_input_listings(urls)

        assert added == 1
        data = load_yaml(existing_listings.data_dir / "input_listings.yaml")
        new_urls = [l["url"] for l in data["listings"]]
        assert "https://example.com/fresh" in new_urls
        assert "https://example.com/scored" not in new_urls

    def test_no_new_urls(self, existing_listings):
        urls = ["https://example.com/existing"]
        added = existing_listings.append_to_input_listings(urls)
        assert added == 0


class TestProcessedIds:
    def test_load_empty(self, ingestor):
        ids = ingestor.load_processed_ids()
        assert ids["ingestor_ids"] == set()
        assert ids["feedback_ids"] == set()

    def test_round_trip(self, ingestor):
        ids = {
            "ingestor_ids": {"123", "456"},
            "feedback_ids": {"789"},
        }
        ingestor.save_processed_ids(ids)
        loaded = ingestor.load_processed_ids()
        assert loaded["ingestor_ids"] == {"123", "456"}
        assert loaded["feedback_ids"] == {"789"}


class TestGetEmailBody:
    def test_plain_text(self):
        from email.mime.text import MIMEText
        from src.utils import get_email_body

        msg = MIMEText("Check out https://example.com/job1")
        body = get_email_body(msg)
        assert "https://example.com/job1" in body

    def test_multipart(self):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from src.utils import get_email_body

        msg = MIMEMultipart()
        msg.attach(MIMEText("Plain text with https://example.com/job2"))
        msg.attach(MIMEText("<html><body>HTML version</body></html>", "html"))

        body = get_email_body(msg)
        assert "https://example.com/job2" in body
