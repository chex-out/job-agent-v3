"""Coach Bridge: reads and writes coaching_state.md for job agent integration.

This module handles surgical insertion/update of the Interview Loops and
Outcome Log sections in coaching_state.md. It preserves all other sections
written by the skills layer.
"""

import os
import re
from datetime import date
from pathlib import Path

from src.utils import resolve_company_name, setup_logging

logger = setup_logging("coach_bridge")


def _default_state_path() -> Path:
    """Resolve the default coaching_state.md path.

    Checks COACHING_STATE_PATH env var first; falls back to cwd/coaching_state.md.
    This fixes the original bug where the path was hardcoded relative to __file__.
    """
    env_path = os.environ.get("COACHING_STATE_PATH")
    if env_path:
        return Path(env_path)
    return Path.cwd() / "coaching_state.md"


class CoachBridge:
    """Read/write interface to coaching_state.md for the job agent."""

    def __init__(self, state_path: str | Path | None = None):
        self.state_path = Path(state_path) if state_path else _default_state_path()

    def _read_file(self) -> str:
        """Read the full coaching_state.md content."""
        if not self.state_path.exists():
            logger.warning(f"coaching_state.md not found at {self.state_path}")
            return ""
        return self.state_path.read_text(encoding="utf-8")

    def _write_file(self, content: str) -> None:
        """Write content back to coaching_state.md with LF line endings."""
        self.state_path.write_text(content, encoding="utf-8", newline="\n")

    def _find_section(self, content: str, heading: str, level: int = 2) -> tuple[int, int]:
        """Find start and end positions of a section by heading.

        Returns (start, end) where start is the position after the heading line
        and end is the position before the next same-level heading (or EOF).
        """
        prefix = "#" * level
        pattern = re.compile(
            rf"^{prefix}\s+{re.escape(heading)}\s*$", re.MULTILINE
        )
        match = pattern.search(content)
        if not match:
            return (-1, -1)

        start = match.end()

        next_heading = re.compile(rf"^#{{{1},{level}}}\s+", re.MULTILINE)
        next_match = next_heading.search(content, start)
        end = next_match.start() if next_match else len(content)

        return (start, end)

    def get_interview_loops(self) -> dict[str, dict]:
        """Read all Interview Loop entries.

        Returns dict mapping company name (lowercase) to its entry data.
        """
        content = self._read_file()
        if not content:
            return {}

        start, end = self._find_section(content, "Interview Loops")
        if start == -1:
            return {}

        section = content[start:end]
        loops = {}

        entries = re.split(r"^###\s+", section, flags=re.MULTILINE)
        for entry in entries:
            entry = entry.strip()
            if not entry or entry.startswith("[") or entry.startswith("<!--"):
                continue

            lines = entry.split("\n")
            company = lines[0].strip()

            data = {"raw": entry, "company": company}
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                    if ":" in line:
                        key, val = line.split(":", 1)
                        data[key.strip().lower()] = val.strip()

            loops[company.lower()] = data

        return loops

    def _resolve_loop_company(self, company_name: str) -> str | None:
        """Resolve a company name against existing Interview Loop headings.

        Returns the canonical (first-seen) company name if found, else None.
        """
        loops = self.get_interview_loops()
        if not loops:
            return None

        if company_name.lower() in loops:
            return loops[company_name.lower()]["company"]

        known = [v["company"] for v in loops.values()]
        matched, confidence = resolve_company_name(company_name, known)
        if matched and confidence >= 95:
            if matched != company_name:
                logger.info(
                    f"Resolved company name: '{company_name}' -> '{matched}' "
                    f"(confidence: {confidence:.0f}%)"
                )
            return matched
        return None

    def company_exists(self, company_name: str) -> bool:
        """Check if a company already has an Interview Loop entry."""
        return self._resolve_loop_company(company_name) is not None

    def get_company_status(self, company_name: str) -> str | None:
        """Get the current status of a company's Interview Loop entry."""
        canonical = self._resolve_loop_company(company_name)
        if not canonical:
            return None
        loops = self.get_interview_loops()
        entry = loops.get(canonical.lower())
        if entry:
            return entry.get("status")
        return None

    def write_research_entry(
        self,
        company_name: str,
        fit_assessment: str,
        key_signals: str,
        entry_date: str | None = None,
        skills_fit: int | None = None,
        preference_fit: int | None = None,
    ) -> bool:
        """Add or update a lightweight Interview Loop entry.

        Returns True if written, False if skipped (e.g., company at higher status).
        """
        if entry_date is None:
            entry_date = date.today().isoformat()

        content = self._read_file()
        if not content:
            logger.error("Cannot write: coaching_state.md not found or empty")
            return False

        canonical = self._resolve_loop_company(company_name)
        if canonical:
            company_name = canonical

        existing_status = self.get_company_status(company_name)
        if existing_status:
            non_downgrade = ["applied", "interviewing", "offer", "closed"]
            if any(s in existing_status.lower() for s in non_downgrade):
                logger.info(f"Skipping {company_name}: already at '{existing_status}'")
                return False

            return self._update_research_entry(
                content, company_name, fit_assessment, key_signals, entry_date,
                skills_fit=skills_fit, preference_fit=preference_fit,
            )

        score_lines = ""
        if skills_fit is not None:
            score_lines += f"- Skills Fit: {skills_fit}/10\n"
        if preference_fit is not None:
            score_lines += f"- Preference Fit: {preference_fit}/10\n"

        entry_block = (
            f"\n### {company_name}\n"
            f"- Status: Researched (via Job Agent)\n"
            f"{score_lines}"
            f"- Fit assessment: {fit_assessment}\n"
            f"- Key signals: {key_signals}\n"
            f"- Date researched: {entry_date}\n"
        )

        start, end = self._find_section(content, "Interview Loops")
        if start == -1:
            logger.error("Interview Loops section not found in coaching_state.md")
            return False

        section = content[start:end]

        if re.match(r"\s*(?:<!--.*?-->\s*|\[.*?\]\s*)*$", section.strip(), re.DOTALL):
            new_content = content[:start] + entry_block + "\n" + content[end:]
        else:
            new_content = content[:end] + entry_block + "\n" + content[end:]

        self._write_file(new_content)
        logger.info(f"Added Interview Loop entry for {company_name} ({fit_assessment})")
        return True

    def _update_research_entry(
        self,
        content: str,
        company_name: str,
        fit_assessment: str,
        key_signals: str,
        entry_date: str,
        skills_fit: int | None = None,
        preference_fit: int | None = None,
    ) -> bool:
        """Update an existing Researched entry with fresh data."""
        pattern = re.compile(
            rf"^###\s+{re.escape(company_name)}\s*$", re.MULTILINE
        )
        match = pattern.search(content)
        if not match:
            logger.warning(f"Could not find H3 heading for {company_name}")
            return False

        entry_start = match.start()
        next_heading = re.compile(r"^##", re.MULTILINE)
        next_match = next_heading.search(content, match.end())
        entry_end = next_match.start() if next_match else len(content)

        score_lines = ""
        if skills_fit is not None:
            score_lines += f"- Skills Fit: {skills_fit}/10\n"
        if preference_fit is not None:
            score_lines += f"- Preference Fit: {preference_fit}/10\n"

        replacement = (
            f"### {company_name}\n"
            f"- Status: Researched (via Job Agent)\n"
            f"{score_lines}"
            f"- Fit assessment: {fit_assessment}\n"
            f"- Key signals: {key_signals}\n"
            f"- Date researched: {entry_date}\n"
        )

        new_content = content[:entry_start] + replacement + "\n" + content[entry_end:]
        self._write_file(new_content)
        logger.info(f"Updated Interview Loop entry for {company_name}")
        return True

    def update_loop_status(self, company_name: str, new_status: str) -> bool:
        """Update the Status field of an existing Interview Loop entry."""
        content = self._read_file()
        if not content:
            return False

        canonical = self._resolve_loop_company(company_name)
        if canonical:
            company_name = canonical

        pattern = re.compile(
            rf"^###\s+{re.escape(company_name)}\s*$", re.MULTILINE
        )
        match = pattern.search(content)
        if not match:
            logger.warning(f"No Interview Loop entry found for {company_name}")
            return False

        next_heading = re.compile(r"^##", re.MULTILINE)
        next_match = next_heading.search(content, match.end())
        entry_end = next_match.start() if next_match else len(content)
        entry_text = content[match.end():entry_end]

        status_pattern = re.compile(r"^- Status:.*$", re.MULTILINE)
        status_match = status_pattern.search(entry_text)
        if not status_match:
            logger.warning(f"No Status line found for {company_name}")
            return False

        abs_start = match.end() + status_match.start()
        abs_end = match.end() + status_match.end()

        new_content = content[:abs_start] + f"- Status: {new_status}" + content[abs_end:]
        self._write_file(new_content)
        logger.info(f"Updated {company_name} status to: {new_status}")
        return True

    def add_outcome(
        self,
        company: str,
        role: str,
        round_name: str,
        result: str,
        notes: str = "",
        entry_date: str | None = None,
    ) -> bool:
        """Add a row to the Outcome Log table."""
        if entry_date is None:
            entry_date = date.today().isoformat()

        content = self._read_file()
        if not content:
            return False

        start, end = self._find_section(content, "Outcome Log")
        if start == -1:
            logger.error("Outcome Log section not found")
            return False

        section = content[start:end]
        new_row = f"| {company} | {role} | {result} | {entry_date} | {notes} |"

        clean_section = re.sub(r"^\[Empty[^\]]*\]\s*$", "", section, flags=re.MULTILINE).strip()

        if not clean_section or not clean_section.startswith("|"):
            table = (
                "\n| Company | Role | Status | Date | Notes |\n"
                "|---------|------|--------|------|-------|\n"
                f"{new_row}\n"
            )
            new_content = content[:start] + table + "\n" + content[end:]
        else:
            new_section = f"\n{clean_section}\n{new_row}\n"
            new_content = content[:start] + new_section + "\n" + content[end:]

        self._write_file(new_content)
        logger.info(f"Added outcome: {company} — {role} — {result}")
        return True

    def add_session_log_entry(
        self,
        summary: str,
        entry_date: str | None = None,
    ) -> bool:
        """Add a row to the Session Log table."""
        if entry_date is None:
            entry_date = date.today().isoformat()

        content = self._read_file()
        if not content:
            return False

        start, end = self._find_section(content, "Session Log")
        if start == -1:
            logger.warning("Session Log section not found")
            return False

        section = content[start:end]
        new_row = f"| {entry_date} | {summary} |"

        last_row = None
        for m in re.finditer(r"^\|.*\|$", section, re.MULTILINE):
            last_row = m

        if last_row:
            insert_pos = start + last_row.end()
            new_content = content[:insert_pos] + "\n" + new_row + content[insert_pos:]
            self._write_file(new_content)
            logger.info(f"Added session log entry: {summary}")
            return True

        # No table yet — create one
        table = f"\n| Date | Summary |\n|------|----------|\n{new_row}\n"
        new_content = content[:start] + table + content[end:]
        self._write_file(new_content)
        return True
