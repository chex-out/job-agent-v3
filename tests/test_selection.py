"""Tests for the email tier's selection protocol and sender security."""

import base64

from src.digest import Digest, DocumentDelivery
from src.feedback import apply_selections, parse_prepare_selections, strip_quoted_lines
from src.utils import authorized_sender, save_yaml, sender_matches

DIGEST_MAP = {
    "1": "https://a.com/job1",
    "2": "https://b.com/job2",
    "3": "https://c.com/job3",
}


class TestParsePrepareSelections:
    def test_single_number(self):
        urls = parse_prepare_selections("Re: Digest", "PREPARE 2", DIGEST_MAP)
        assert urls == ["https://b.com/job2"]

    def test_multiple_numbers_spaces(self):
        urls = parse_prepare_selections("Re: Digest", "PREPARE 1 3", DIGEST_MAP)
        assert urls == ["https://a.com/job1", "https://c.com/job3"]

    def test_multiple_numbers_commas(self):
        urls = parse_prepare_selections("Re: Digest", "prepare 1,2", DIGEST_MAP)
        assert urls == ["https://a.com/job1", "https://b.com/job2"]

    def test_direct_url(self):
        urls = parse_prepare_selections(
            "Re: Digest", "PREPARE https://d.com/job4", DIGEST_MAP
        )
        assert urls == ["https://d.com/job4"]

    def test_unknown_number_skipped(self):
        urls = parse_prepare_selections("Re: Digest", "PREPARE 9", DIGEST_MAP)
        assert urls == []

    def test_in_subject(self):
        urls = parse_prepare_selections("PREPARE 3", "thanks!", DIGEST_MAP)
        assert urls == ["https://c.com/job3"]

    def test_no_command(self):
        urls = parse_prepare_selections(
            "Re: Digest", "these look great, will apply myself", DIGEST_MAP
        )
        assert urls == []

    def test_reply_quote_does_not_false_positive(self):
        """The digest's quoted instructions ("e.g. PREPARE 2 5") must not
        auto-select listings — quoted lines are stripped before parsing."""
        reply = (
            "PREPARE 1\n"
            "\n"
            "> Reply to this email with PREPARE and the listing numbers\n"
            "> e.g. PREPARE 2 5\n"
        )
        body = strip_quoted_lines(reply)
        urls = parse_prepare_selections("Re: Digest", body, DIGEST_MAP)
        assert urls == ["https://a.com/job1"]


class TestApplySelections:
    def _listings(self):
        return {
            "listings": [
                {"url": "https://a.com/job1", "company_name": "A", "role_title": "R"},
                {
                    "url": "https://b.com/job2?utm_source=x",
                    "company_name": "B",
                    "role_title": "R",
                },
                {
                    "url": "https://c.com/job3",
                    "company_name": "C",
                    "role_title": "R",
                    "prepared": True,
                },
            ]
        }

    def test_marks_selected(self):
        data = self._listings()
        assert apply_selections(["https://a.com/job1"], data) == 1
        assert data["listings"][0]["selected_for_prep"] is True

    def test_normalizes_tracking_params(self):
        data = self._listings()
        assert apply_selections(["https://b.com/job2"], data) == 1
        assert data["listings"][1]["selected_for_prep"] is True

    def test_already_prepared_not_reselected(self):
        data = self._listings()
        assert apply_selections(["https://c.com/job3"], data) == 0
        assert "selected_for_prep" not in data["listings"][2]

    def test_unknown_url_ignored(self):
        data = self._listings()
        assert apply_selections(["https://nowhere.com/x"], data) == 0


class TestSenderSecurity:
    def test_matches_bare_address(self):
        assert sender_matches("friend@example.com", "friend@example.com")

    def test_matches_display_name_format(self):
        assert sender_matches("Friend Name <Friend@Example.com>", "friend@example.com")

    def test_rejects_other_sender(self):
        assert not sender_matches("attacker@evil.com", "friend@example.com")

    def test_rejects_lookalike_display_name(self):
        """Display name spoofing the allowed address must not pass."""
        assert not sender_matches(
            "friend@example.com <attacker@evil.com>", "friend@example.com"
        )

    def test_rejects_when_no_allowed_configured(self):
        assert not sender_matches("anyone@example.com", "")

    def test_authorized_sender_env_priority(self, monkeypatch):
        monkeypatch.setenv("AUTHORIZED_SENDER", "Friend@Example.com ")
        monkeypatch.setenv("GMAIL_ADDRESS", "agent@example.com")
        assert authorized_sender() == "friend@example.com"

    def test_authorized_sender_falls_back_to_gmail(self, monkeypatch):
        monkeypatch.delenv("AUTHORIZED_SENDER", raising=False)
        monkeypatch.setenv("GMAIL_ADDRESS", "agent@example.com")
        assert authorized_sender() == "agent@example.com"


class TestDocumentDelivery:
    def _setup(self, tmp_path, docs_pending=True, with_files=True):
        data_dir = tmp_path / "data"
        listing = {
            "url": "https://a.com/job1",
            "company_name": "Loopwork",
            "role_title": "Senior Manager",
            "prepared": True,
            "docs_pending": docs_pending,
        }
        save_yaml(data_dir / "processed_listings.yaml", {"listings": [listing]})

        if with_files:
            prepared = data_dir / "prepared" / "loopwork" / "senior-manager"
            prepared.mkdir(parents=True)
            (prepared / "resume.md").write_text("# Resume", encoding="utf-8")
            (prepared / "cover_letter.md").write_text("Dear...", encoding="utf-8")
            (prepared / "notes.md").write_text("## What Changed", encoding="utf-8")

        return DocumentDelivery(Digest(data_dir=data_dir))

    def test_builds_three_attachments(self, tmp_path):
        delivery = self._setup(tmp_path)
        listing = {"company_name": "Loopwork", "role_title": "Senior Manager"}
        attachments = delivery.build_attachments(listing)
        assert [a["filename"] for a in attachments] == [
            "loopwork-resume.md",
            "loopwork-cover_letter.md",
            "loopwork-notes.md",
        ]
        decoded = base64.b64decode(attachments[0]["content"]).decode()
        assert decoded == "# Resume"

    def test_run_sends_and_clears_flag(self, tmp_path, monkeypatch):
        delivery = self._setup(tmp_path)
        sent = []
        monkeypatch.setattr(
            delivery.digest, "send",
            lambda html, subject, attachments=None: sent.append(subject) or True,
        )
        assert delivery.run() == 1
        assert "Loopwork" in sent[0]

        from src.utils import load_yaml

        data = load_yaml(delivery.data_dir / "processed_listings.yaml")
        assert data["listings"][0]["docs_pending"] is False

    def test_run_nothing_pending(self, tmp_path):
        delivery = self._setup(tmp_path, docs_pending=False)
        assert delivery.run() == 0

    def test_missing_files_not_delivered(self, tmp_path, monkeypatch):
        delivery = self._setup(tmp_path, with_files=False)
        monkeypatch.setattr(
            delivery.digest, "send", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
        )
        assert delivery.run() == 0
