"""Tests for the session hooks — YAML validation, coaching-state checks, exit-0 policy.

The hooks run on every session via .claude/settings.json and are designed to
exit 0 unconditionally (silent failures beat blocking the user's workflow).
Because failures are silent by design, these tests are the only way to know
the hooks actually work.
"""

import subprocess
import sys
from pathlib import Path

from src.hooks.check_coaching_state import REQUIRED_SECTIONS, check_coaching_state
from src.hooks.validate_yaml import check_yaml_file

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestCheckYamlFile:
    def test_valid_yaml_returns_none(self, tmp_path):
        p = tmp_path / "good.yaml"
        p.write_text("name: Maya\nroles:\n  - Manager\n", encoding="utf-8")
        assert check_yaml_file(p) is None

    def test_malformed_yaml_returns_error(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("{{{unterminated: [", encoding="utf-8")
        assert check_yaml_file(p) is not None

    def test_empty_file_returns_error(self, tmp_path):
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        assert check_yaml_file(p) == "File is empty"

    def test_missing_file_returns_error_not_raises(self, tmp_path):
        # check_yaml_file must never raise — the hook's exit-0 policy depends on it
        assert check_yaml_file(tmp_path / "nonexistent.yaml") is not None


class TestCheckCoachingState:
    def test_complete_state_has_no_missing_sections(self, tmp_path):
        p = tmp_path / "coaching_state.md"
        p.write_text("\n".join(REQUIRED_SECTIONS), encoding="utf-8")
        assert check_coaching_state(p) == []

    def test_reports_missing_sections(self, tmp_path):
        p = tmp_path / "coaching_state.md"
        p.write_text(REQUIRED_SECTIONS[0], encoding="utf-8")
        missing = check_coaching_state(p)
        assert missing == REQUIRED_SECTIONS[1:]


class TestExitZeroPolicy:
    """Every hook must exit 0 no matter what — a non-zero exit blocks the user."""

    def _run(self, script: str) -> int:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "src" / "hooks" / script)],
            cwd=REPO_ROOT,
            capture_output=True,
            timeout=60,
        )
        return result.returncode

    def test_validate_yaml_exits_zero(self):
        assert self._run("validate_yaml.py") == 0

    def test_check_coaching_state_exits_zero(self):
        assert self._run("check_coaching_state.py") == 0

    def test_session_log_exits_zero(self):
        assert self._run("session_log.py") == 0
