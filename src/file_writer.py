"""Read-before-write utility for reasoning files.

All skills that write reasoning to markdown files must use update_section()
rather than raw file appends. This prevents contradictions when reasoning
is updated mid-session.

Rules:
- Named sections are identified by strict key constants (SECTION_KEYS).
  Never pass freeform heading strings — use the constants.
- If a section exists: overwrite its content, append one line to Change Log.
- If a section is new: create it.
- Change Log is append-only, capped at CHANGE_LOG_MAX_ENTRIES.
- All writes use LF line endings (newline='\\n') to prevent CRLF issues on Windows.

Concurrent writes: not protected by file locking. This toolkit is designed for
single-user, single-session use. Document this limitation if extending to
multi-session or multi-user contexts.
"""

import re
from datetime import date
from pathlib import Path

# Strict section key constants. Skills pass these constants, not freeform strings.
# Adding a new section? Add it here first.
SECTION_KEYS = {
    # Tailoring notes (data/prepared/{company}/{role}/notes.md)
    "positioning_focus": "## Positioning Focus",
    "what_changed": "## What Changed from Base Resume",
    "watch_outs": "## Watch Outs",
    "verify_checklist": "## Verify Before Sending",
    "change_log": "## Change Log",
    # Storybank sections (coaching_state.md ## Storybank)
    "career_highlights": "### Career Highlights",
    "positioning_statement": "### Positioning Statement",
    "key_skills_evidence": "### Key Skills with Evidence",
    "known_concerns_bank": "### Known Concerns",
    "superpower": "### Superpower",
    "interview_stories": "### Interview Stories",
    "competency_map": "### Competency Map",
    # Session notes (data/session_notes/{date}.md)
    "session_summary": "## Session Summary",
    "decisions_made": "## Decisions Made",
    "next_actions": "## Next Actions",
    "mid_session_instructions": "## Instructions for Next Session",
}

# Change Log entries per file (oldest dropped when cap is reached)
CHANGE_LOG_MAX_ENTRIES = 20


def update_section(
    file_path: str | Path,
    section_key: str,
    new_content: str,
    reason: str | None = None,
) -> None:
    """Read the file, locate section_key, overwrite its content.

    If the section doesn't exist, it is created at the end of the file.
    If overwriting existing content and reason is provided, one line is
    appended to the Change Log.

    Args:
        file_path: Path to the markdown file.
        section_key: Must be a key in SECTION_KEYS. Raises ValueError otherwise.
        new_content: The replacement content for the section body.
        reason: Optional one-sentence reason for the change (logged to Change Log).

    Raises:
        ValueError: If section_key is not in SECTION_KEYS.
    """
    if section_key not in SECTION_KEYS:
        raise ValueError(
            f"Unknown section key: {section_key!r}. "
            f"Add it to SECTION_KEYS in file_writer.py first."
        )

    heading = SECTION_KEYS[section_key]
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content
    existing_text = ""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8", newline="\n") as f:
            existing_text = f.read()

    # Find whether section exists
    section_existed = _section_exists(existing_text, heading)

    # Build new file content
    if section_existed:
        updated = _replace_section(existing_text, heading, new_content)
        if reason:
            updated = _append_change_log(updated, heading, reason)
    else:
        # Append new section at end
        sep = "\n\n" if existing_text and not existing_text.endswith("\n\n") else ""
        updated = existing_text + sep + heading + "\n" + new_content

    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)


def read_section(file_path: str | Path, section_key: str) -> str | None:
    """Read and return the content of a named section.

    Returns None if the file doesn't exist or the section isn't found.

    Args:
        file_path: Path to the markdown file.
        section_key: Must be a key in SECTION_KEYS.
    """
    if section_key not in SECTION_KEYS:
        raise ValueError(f"Unknown section key: {section_key!r}.")

    heading = SECTION_KEYS[section_key]
    file_path = Path(file_path)

    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8", newline="\n") as f:
        text = f.read()

    return _extract_section(text, heading)


def section_is_populated(file_path: str | Path, section_key: str) -> bool:
    """Return True if the section exists and has non-whitespace content.

    Used by Suite D skills to check storybank dependency without crashing.
    """
    content = read_section(file_path, section_key)
    return bool(content and content.strip())


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_heading_level(heading: str) -> int:
    """Return the heading level (number of # characters)."""
    return len(heading) - len(heading.lstrip("#"))


def _section_pattern(heading: str) -> re.Pattern:
    """Build a regex that matches a section from its heading to the next same-or-higher heading."""
    level = _get_heading_level(heading)
    escaped = re.escape(heading)
    # Match from this heading to the next heading of the same or higher level, or end of string
    stops = "#" * level
    return re.compile(
        rf"({escaped}\n)(.*?)(?=\n{stops}[^#]|\Z)",
        re.DOTALL,
    )


def _section_exists(text: str, heading: str) -> bool:
    return heading in text


def _extract_section(text: str, heading: str) -> str | None:
    """Extract the body content of a section (excluding the heading line)."""
    pattern = _section_pattern(heading)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(2).strip()


def _replace_section(text: str, heading: str, new_content: str) -> str:
    """Replace the body of an existing section with new_content."""
    pattern = _section_pattern(heading)

    def replacement(m):
        return m.group(1) + new_content + "\n"

    result, count = pattern.subn(replacement, text)
    if count == 0:
        # Section heading exists but pattern didn't match (edge case) — append
        sep = "\n\n" if not text.endswith("\n\n") else ""
        return text + sep + heading + "\n" + new_content
    return result


def _append_change_log(text: str, changed_heading: str, reason: str) -> str:
    """Append one entry to the ## Change Log section, respecting the cap."""
    log_heading = SECTION_KEYS["change_log"]
    today = date.today().isoformat()
    new_entry = f"- [{today}] Changed {changed_heading} — {reason}"

    if log_heading in text:
        # Read existing entries
        existing_body = _extract_section(text, log_heading) or ""
        entries = [line for line in existing_body.strip().splitlines() if line.strip()]

        # Append and trim to cap
        entries.append(new_entry)
        if len(entries) > CHANGE_LOG_MAX_ENTRIES:
            entries = entries[-CHANGE_LOG_MAX_ENTRIES:]

        new_body = "\n".join(entries)
        return _replace_section(text, log_heading, new_body)
    else:
        # Create Change Log section
        sep = "\n\n" if not text.endswith("\n\n") else ""
        return text + sep + log_heading + "\n" + new_entry + "\n"
