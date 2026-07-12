"""PostToolUse hook: validate coaching_state.md section structure after writes.

Tiered error handling:
- Soft failure (file not found, empty file): log silently, say nothing.
- Hard failure (required section headers missing or broken): log AND print
  a plain-English warning the user can act on.

Failure policy: ALWAYS exit 0. All exceptions caught. Never blocks workflow.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path


# Required top-level section headers in coaching_state.md
REQUIRED_SECTIONS = [
    "## Profile",
    "## Resume Analysis",
    "## Storybank",
    "## Interview Loops",
    "## Outcome Log",
    "## Session Log",
]


def check_coaching_state(path: Path) -> list[str]:
    """Return list of missing required sections. Empty list = file is valid."""
    try:
        with open(path, "r", encoding="utf-8", newline="\n") as f:
            text = f.read()
    except Exception as e:
        return [f"Could not read file: {e}"]

    if not text.strip():
        return []  # Empty template is fine (pre-setup)

    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    return missing


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent
    state_path = repo_root / "coaching_state.md"
    error_log = repo_root / "data" / "hook_errors.log"

    if not state_path.exists():
        return  # Soft failure: file not yet created

    missing = check_coaching_state(state_path)

    if not missing:
        return

    # Log the issue
    error_log.parent.mkdir(parents=True, exist_ok=True)
    with open(error_log, "a", encoding="utf-8", newline="\n") as f:
        f.write(
            f"[{datetime.now().isoformat()}] coaching_state.md missing sections: "
            f"{', '.join(missing)}\n"
        )

    # Hard failure: emit visible warning (stdout reconfigured for Windows
    # cp1252 consoles — emoji would otherwise raise and be swallowed)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(
        "\n⚠️  Your coaching state file may have a structure issue. "
        "Run /coach-kickoff to verify your coaching state is intact.\n"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # The error-log write must never break the exit-0 guarantee.
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent
            error_log = repo_root / "data" / "hook_errors.log"
            error_log.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log, "a", encoding="utf-8", newline="\n") as f:
                f.write(f"[{datetime.now().isoformat()}] check_coaching_state hook error:\n")
                f.write(traceback.format_exc())
                f.write("\n")
        except Exception:
            pass
    sys.exit(0)
