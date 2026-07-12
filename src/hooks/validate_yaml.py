"""PostToolUse hook: validate YAML files after writes to config/ or data/.

Tiered error handling:
- Soft failure (non-YAML file written, minor issues): log silently.
- Hard failure (profile.yaml or processed_listings.yaml is now malformed):
  log AND print a visible plain-English warning the user can act on.

Failure policy: ALWAYS exit 0. All exceptions caught. Never blocks workflow.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

import yaml


HARD_FAILURE_FILES = {"profile.yaml", "processed_listings.yaml"}


def check_yaml_file(path: Path) -> str | None:
    """Return an error message if the file is malformed YAML, else None."""
    try:
        with open(path, "r", encoding="utf-8", newline="\n") as f:
            data = yaml.safe_load(f)
        if data is None:
            return "File is empty"
        return None
    except yaml.YAMLError as e:
        return str(e)
    except Exception as e:
        return str(e)


# Files larger than this are skipped — parsing a multi-MB pipeline file on
# every tool use adds unbounded latency (CLAUDE.md rule 14 territory).
MAX_VALIDATE_BYTES = 1_000_000


def main() -> None:
    # Windows consoles default to cp1252; the warning text below contains
    # emoji. Without this, print() raises UnicodeEncodeError and the warning
    # is silently swallowed by the outer handler — on the exact platform
    # these warnings matter most.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    repo_root = Path(__file__).resolve().parent.parent.parent
    error_log = repo_root / "data" / "hook_errors.log"

    # Check YAML files in config/ and data/
    yaml_files = list((repo_root / "config").glob("*.yaml")) + \
                 list((repo_root / "data").glob("*.yaml"))

    for yaml_path in yaml_files:
        if yaml_path.stat().st_size > MAX_VALIDATE_BYTES:
            continue
        error = check_yaml_file(yaml_path)
        if error is None:
            continue

        is_hard_failure = yaml_path.name in HARD_FAILURE_FILES

        # Log to error log
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a", encoding="utf-8", newline="\n") as f:
            f.write(
                f"[{datetime.now().isoformat()}] YAML issue in {yaml_path.name}: {error}\n"
            )

        # Hard failure: emit visible warning
        if is_hard_failure:
            if yaml_path.name == "profile.yaml":
                print(
                    "\n⚠️  Your profile file may have been saved incorrectly after the "
                    "last update. Run /setup to check and repair it.\n"
                )
            else:
                print(
                    f"\n⚠️  Your job pipeline file ({yaml_path.name}) may have a "
                    "formatting issue. Run /queue-digest to verify your pipeline is intact.\n"
                )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # The error-log write itself must never break the exit-0 guarantee
        # (read-only checkout, locked file, full disk).
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent
            error_log = repo_root / "data" / "hook_errors.log"
            error_log.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log, "a", encoding="utf-8", newline="\n") as f:
                f.write(f"[{datetime.now().isoformat()}] validate_yaml hook error:\n")
                f.write(traceback.format_exc())
                f.write("\n")
        except Exception:
            pass
    sys.exit(0)
