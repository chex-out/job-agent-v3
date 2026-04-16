"""Stop hook: append a one-line activity summary to data/session_log.md.

Fires at the end of every Claude turn. Detects whether any state files
were modified recently and logs a summary line.

Failure policy: ALWAYS exit 0. All exceptions are caught and logged to
data/hook_errors.log. This hook must never block the user's workflow.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent
    log_path = repo_root / "data" / "session_log.md"
    error_log = repo_root / "data" / "hook_errors.log"

    # State files we watch for activity
    watched = [
        repo_root / "config" / "profile.yaml",
        repo_root / "data" / "processed_listings.yaml",
        repo_root / "data" / "input_listings.yaml",
        repo_root / "coaching_state.md",
    ]

    # Find files modified in the last 5 minutes
    cutoff = datetime.now().timestamp() - 300
    modified = []
    for path in watched:
        try:
            if path.exists() and path.stat().st_mtime > cutoff:
                modified.append(path.name)
        except Exception:
            pass

    if not modified:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"- [{timestamp}] Modified: {', '.join(modified)}\n"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(entry)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        repo_root = Path(__file__).resolve().parent.parent.parent
        error_log = repo_root / "data" / "hook_errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"[{datetime.now().isoformat()}] session_log hook error:\n")
            f.write(traceback.format_exc())
            f.write("\n")
    sys.exit(0)
