# Deep Audit Report — Job Seeker AI Toolkit

**Date:** 2026-07-12 · **Baseline:** commit `a0866bf`, 209/209 tests passing · **Method:** 5 parallel read-only audit lanes (Python/Windows, skill cross-consistency, docs accuracy, security/privacy, test coverage), findings deduplicated and Critical/High citations re-verified by the coordinating reviewer.

**Report only — no fixes applied.** Each finding has a one-line fix direction; decide what gets fixed and in what order.

---

## Resolution status (updated 2026-07-12, post-remediation)

All findings fixed across 6 commits (`04d6ee5`, `464b01f`, `2552efa`, `6131f34`, `475dba2`, `e8a0f11`) — 243 tests passing — **except**:

- **AUD-L9** (path/username residue in old `settings.local.json` history blobs) — accepted as low sensitivity; a further filter-repo pass is available if wanted
- **AUD-L12's coach-prep ↔ coach-drill data-flow gap** (coach-drill expects prep briefs that no skill persists) — a design change, deferred to backlog rather than patched
- **M2 note**: `score_single_url` still calls `load_profile` per listing (minor inefficiency, correct behavior)

---

## Executive Summary

| Severity | Count | Themes |
|---|---|---|
| **Critical** | 3 | A live crash in batch document prep; silent data loss in coaching-state writes; onboarding Step 8 installs a package that doesn't exist |
| **High** | 12 | Anti-fabrication remediation unwired; corrupt-YAML data loss; dual-axis threshold migration incomplete across 4 skills; false privacy claims; workflows publish personal data; broken workflow YAML; wrong context-clear instruction everywhere |
| **Medium** | 17 | Rule 7/14 violations across skills; hardcoded thresholds contradicting docs; prompt-injection surface; missing tests for core modules; stale doc claims |
| **Low** | 12 | Dedup inconsistencies, dead references, edge-case exit paths, residual path metadata in history |

**Systemic patterns behind the individual findings:**
1. **The dual-axis threshold migration (single int → `{skills_fit_min, preference_fit_min}`) was never finished.** It landed in `models.py`, `scout.py`, `find-jobs.md`, and `tailor-docs.md:30` — and missed `preparer.py` (crash), `digest.py`, `score-job.md`, `queue-digest.md`, `job-search-session.md`, and even `tailor-docs.md:20`. One migration, six stragglers.
2. **CLAUDE.md rules 7 and 14 are aspirational, not enforced.** Most skills that touch `coaching_state.md` or `processed_listings.yaml` don't reference `update_section()` or targeted reads; only `find-jobs.md` models both correctly.
3. **No CI.** 209 tests exist and never run automatically, which is why the Critical crash shipped.
4. **Privacy documentation lags the integrations.** README's "nothing is sent anywhere except Anthropic" predates Firecrawl, Apify, Resend, and Gmail.

---

## Critical

### AUD-C1 · Batch document prep crashes with TypeError *(re-verified by coordinator)*
**File:** `src/preparer.py:473` · **Lanes:** A + E (independent)
Single-arg call `rubric.is_above_prep_threshold(l.get("skills_fit", 0))` against the two-arg dual-axis signature (`src/models.py:167`). Any batch run of `Preparer.run()` — the default `/tailor-docs` batch path and the `job_digest.yml` pipeline — raises an unhandled TypeError before any tailoring happens. `tests/test_preparer.py` covers only pure helpers, which is why the refactor missed this call site.
**Fix direction:** pass both scores; add a batch-filter test.

### AUD-C2 · `update_section()` silently deletes the following h2 section *(re-verified by coordinator)*
**File:** `src/file_writer.py:153` · **Lane:** A
The section-end lookahead `(?=\n###[^#]|\Z)` for an h3 heading only stops at another h3 — a following `## ` heading fails the three-`#` match, contradicting the docstring ("same or higher"). In the shipped `coaching_state.md`, `### Superpowe` is immediately followed by `## Interview Loops`: updating the superpower section (a `/build-storybank` step) consumes and deletes the entire Interview Loops section. Silent data loss in the file this module exists to protect.
**Fix direction:** lookahead `(?=\n#{1,level}\s|\Z)`; add a regression test with an h3-then-h2 layout.

### AUD-C3 · Onboarding Step 8 installs a nonexistent package *(verified via npm registry 404 + control)*
**File:** `README.md:118` (also 194, 270) · **Lane:** C
`claude mcp add @anthropic-ai/mcp-server-indeed` — the npm registry returns 404 for this package (control check on `@anthropic-ai/claude-code` succeeded, so the check is sound). The one-arg form is also invalid `claude mcp add` syntax (requires `<name> <commandOrUrl>`). Every new user dead-ends at Step 8 in all three OS sections; `/find-jobs` Mode 1 then silently returns nothing.
**Fix direction:** replace with a real, working Indeed/job-search MCP (correct name + syntax), or rewrite Mode 1's default source; update the three README sections and the troubleshooting cross-reference together.

---

## High

### AUD-H1 · Anti-fabrication remediation is dead code — fabricated docs still ship
**File:** `src/preparer.py:302, 529-540` · **Lane:** A
`apply_targeted_edit()` is never called. When validation finds FABRICATED claims, the pipeline still writes resume/cover letter to disk, marks the listing `prepared=True`, and only appends a note to notes.md. A user who sends resume.md without reading notes.md ships fabricated claims — undermining CLAUDE.md rule 10 and the toolkit's core differentiator.
**Fix direction:** wire the remediation before save, or quarantine (no `prepared=True`) while fabrications remain.

### AUD-H2 · Corrupt YAML is silently overwritten with empty data
**File:** `src/utils.py:42` + `src/scout.py:244-282` · **Lane:** A
`load_yaml` swallows YAMLError and returns `{}`; `run_batch` then initializes empty and saves — permanently erasing a recoverable `processed_listings.yaml` after one transient corruption.
**Fix direction:** distinguish missing from corrupt; never save over a file that failed to parse; back up first.

### AUD-H3 · Hook warnings never render on Windows
**File:** `src/hooks/validate_yaml.py:61`, `check_coaching_state.py:65` · **Lane:** A
`print()` of emoji to piped stdout under cp1252 raises UnicodeEncodeError, which the outer try/except swallows into the error log with exit 0. The user-facing "profile may be corrupt" warning never appears on the platform this repo primarily targets.
**Fix direction:** `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at hook start, or drop emoji.

### AUD-H4 · Dual-axis leftovers in /score-job (3 sites)
**File:** `.claude/commands/score-job.md:34, 96, 128` · **Lane:** B
Compares `skills_fit` alone against `scoring.threshold_for_preparation` / `threshold_for_coaching`, which are now dicts. Line 128 directly contradicts `find-jobs.md:139` — the same listing enters coaching state via one skill but not the other.
**Fix direction:** mirror the dual-axis condition and `update_section()` reference from find-jobs.md.

### AUD-H5 · Dual-axis leftovers in queue-digest, job-search-session, tailor-docs:20
**Files:** `queue-digest.md:63,72` · `job-search-session.md:24,88` · `tailor-docs.md:20` · **Lane:** B
Same class as H4: scalar comparisons against dict thresholds; "ready for docs" buckets drop the preference axis. tailor-docs is internally inconsistent (line 20 scalar, line 30 correct).
**Fix direction:** one sweep applying the same dual-axis wording everywhere; consider a single canonical phrasing in CLAUDE.md.

### AUD-H6 · Rule 14 violations at session start and pipeline view
**Files:** `queue-digest.md:15` · `job-search-session.md:23` · **Lane:** B
Both instruct full reads of `processed_listings.yaml`. CLAUDE.md rule 14 names `/queue-digest` explicitly as grep-only. job-search-session does the full read at the start of every session — the worst possible place.
**Fix direction:** grep `status:` fields + targeted offset/limit reads.

### AUD-H7 · "Ctrl+L to clear context" is wrong — everywhere
**Files:** `README.md:341,407,431` · `CLAUDE.md:49,99` · `compact.md`, `coaching-session.md`, `job-search-session.md`, `content-session.md` · **Lane:** C (verified against official docs)
Ctrl+L redraws the screen and keeps history; `/clear` clears context. The entire `/compact` workflow is anchored on the wrong key: users following it never actually clear context.
**Fix direction:** replace every Ctrl+L reference with `/clear` (9 sites across 7 files).

### AUD-H8 · `/setup --migrate` is a documented dead end
**Files:** `README.md:415` · `src/profile.py:74` · **Lane:** C
Both direct users to `/setup --migrate`; setup.md has zero migrate handling and the only migration module raises NotImplementedError.
**Fix direction:** point to `/reset` + `/setup` until migration exists, or implement the flag.

### AUD-H9 · Both scheduled workflows have invalid YAML *(re-verified by coordinator)*
**Files:** `.github/workflows/job_digest.yml:4` · `collect_feedback.yml:4` · **Lane:** C
Cron removal left a dangling empty `schedule:` key (null value). GitHub Actions requires a sequence there; the invalid file also breaks the `workflow_dispatch` manual trigger.
**Fix direction:** delete the empty `schedule:` keys.

### AUD-H10 · Workflows force-publish personal career data
**Files:** `job_digest.yml:51` · `collect_feedback.yml:34` · **Lane:** D
`git add -f` on gitignored `coaching_state.md` and pipeline YAMLs, then push. A non-technical user enabling the digest on a public fork publishes their coaching history and resume-derived data. The `.gitignore` protection is deliberately defeated.
**Fix direction:** private artifact/branch for workflow state, or a loud gate requiring the user to confirm the repo is private.

### AUD-H11 · Privacy section is false
**File:** `README.md:395,425` · **Lanes:** C + D
"Nothing is sent anywhere except to the Anthropic API" — contradicted by the README's own integrations: Firecrawl (career page URLs), Apify (LinkedIn session cookies), Resend (scored listings emailed), Gmail IMAP. Also an unverifiable retention guarantee about Anthropic's servers.
**Fix direction:** rewrite Privacy to enumerate each optional integration and exactly what leaves the machine when enabled.

### AUD-H12 · LinkedIn session cookies: no sensitivity warning
**File:** `.claude/commands/find-jobs.md:74` · **Lane:** D
Mode 5 has users export full session cookies (plaintext at rest, sent to a third-party-authored Apify actor) with only a ToS note. No warning that cookies grant complete account access nor how to revoke (log out / change password).
**Fix direction:** explicit consent prompt on first Mode 5 run covering access scope, third-party handling, and revocation.

### AUD-H13 · Core scorer untested + no CI
**Files:** `src/scout.py` (no test file) · `.github/workflows/` (no pytest) · **Lane:** E
scout.py (328 LOC, the scoring engine) has zero tests; no workflow runs the 209 existing tests, so regressions like AUD-C1 land silently. All eval tests are mocked and CI-safe already.
**Fix direction:** add `test.yml` running pytest on push/PR; add test_scout.py.

---

## Medium

| ID | Location | Finding | Fix direction |
|---|---|---|---|
| AUD-M1 | `src/digest.py:112` + `CLAUDE.md:183` | `group_by_tier` hardcodes tier thresholds, ignoring profile config — and CLAUDE.md's "Critical Bugs Fixed" table falsely claims this was fixed. `models.py:78` `derive_fit_assessment` hardcodes the same numbers. Found independently by 3 lanes. | Route through ScoringRubric; correct the CLAUDE.md table |
| AUD-M2 | `src/scout.py:281` | Batch scoring saves nothing until the whole batch completes — a crash on listing N loses N−1 paid API results | Save incrementally inside the loop |
| AUD-M3 | `src/preparer.py:66` vs `file_writer.py:28` | All four notes.md headings emitted by the tailoring prompt diverge from SECTION_KEYS ("What Changed" vs "What Changed from Base Resume" etc.) — `read_section()` on prepared notes always returns None | Interpolate SECTION_KEYS constants into the prompt |
| AUD-M4 | `src/preparer.py:535` | Fabrication flags written via raw string append, violating rule 7; heading isn't a SECTION_KEYS constant | Add `fabrication_flags` key; use update_section() |
| AUD-M5 | `src/scout.py:222` + module tops | Scout instantiates `CoachBridge()` resolving to cwd despite configurable dirs; five modules run `load_dotenv(Path.cwd()/'.env')` at import time | Pass state_path through; move dotenv into main() |
| AUD-M6 | `src/hooks/validate_yaml.py:41` | PostToolUse hook re-parses every YAML in config/ + data/ on every tool use — including the file rule 14 says grows huge; unbounded per-turn latency | Validate only the file that was written; size cap |
| AUD-M7 | `score-job.md:128`, `track-application.md:49`, `coach-drill.md:167` | Rule 7 violations: coaching_state.md writes without update_section()/SECTION_KEYS ("add a row" = raw append) | Name update_section() + keys in each skill |
| AUD-M8 | `track-application.md:24`, `tailor-docs.md:12,18` | Rule 14 gaps: company fuzzy-match and prerequisite checks imply full reads of processed_listings.yaml | Grep-first patterns as in find-jobs.md:28 |
| AUD-M9 | `build-storybank.md:142` | Closing advertises `/profile-optimizer` (matches nothing; backlog name is /linkedin-optimizer) and `/career-gaps` (backlog) as "now unlocked" | Drop or relabel "coming in v1.1" |
| AUD-M10 | `src/scout.py:30` + skills | Prompt injection surface: fetched listing text embedded in prompts with no untrusted-content delimiters; skill flows feed fetched content into a session holding file-write tools | Wrap in untrusted tags + CLAUDE.md rule; applies to Modes 2/3 too |
| AUD-M11 | `.env.example:40` vs `src/ingestor.py:40` | .env.example documents OAuth vars (GMAIL_CREDENTIALS_PATH/TOKEN) no code uses; real vars are GMAIL_ADDRESS/GMAIL_APP_PASSWORD (full-mailbox scope, undisclosed) | Fix .env.example; state the scope |
| AUD-M12 | `README.md:382` | Digest section wrong on 4 counts: "daily" (workflow says weekly, now unscheduled), "see workflow for instructions" (none), ".env" (workflow reads GitHub secrets), incomplete secret list | Rewrite section |
| AUD-M13 | `README.md:428` | Cost estimates unverifiable and inconsistent with subscription auth flow described in Step 6 | Label as rough API-billing examples or generalize |
| AUD-M14 | `README.md:288` | "/build-storybank unlocks LinkedIn optimizer" — skill doesn't exist (v1.2 backlog) | Point at /content-session |
| AUD-M15 | `src/hooks/*` (3 modules, 226 LOC) | Zero tests for hooks wired into every session; exit-0 design makes failures silent — tests are the only detection | Add test_hooks.py |
| AUD-M16 | `tests/` | Zero `pytest.raises` in test_coach_bridge/digest/feedback/ingestor — error paths untested (test_profile.py is the model to copy) | Add malformed-input cases |
| AUD-M17 | `src/models.py:179` | No test_models.py; `is_above_coaching_threshold` boundaries never asserted anywhere | Add boundary tests both thresholds |

---

## Low

| ID | Location | Finding |
|---|---|---|
| AUD-L1 | `src/scout.py:305` | Single-URL path appends with no dedup; batch dedupes raw URL while ingestor dedupes normalized URL — same job passes one gate, not the other |
| AUD-L2 | `src/profile.py:70` | Non-numeric schema_version raises raw ValueError (not ProfileError); newer major versions pass silently |
| AUD-L3 | `src/hooks/*` exit paths | The except block's own error-log write is unguarded — if it raises, hooks exit non-zero, violating the exit-0 policy |
| AUD-L4 | `src/utils.py:191` | `fetch_page_text` has no retry despite `retry_with_backoff` existing in the same module; failed listings become status=error permanently. Ingestor never marks no-URL emails processed (re-fetched forever) |
| AUD-L5 | `coach-kickoff.md:146` | "Append to Coaching Notes" contradicts update_section() overwrite semantics (rule 9 permits appends only to Change Log) |
| AUD-L6 | `linkedin-session.md` | 5-line redirect stub registers as a live command but is absent from all skill tables — delete for public release (no legacy users) |
| AUD-L7 | `README.md:411` | Troubleshooting references section "Setting Up Job Search" which no longer exists (removed in Step 8 consolidation) |
| AUD-L8 | `CLAUDE.md:75` vs `BACKLOG.md` | v1.1/v1.2 labeling inconsistency for /linkedin-optimizer and /career-gaps |
| AUD-L9 | git history | `.claude/settings.local.json` add/delete commits expose local username, machine paths, and a prior project folder name. No secrets. One more filter-repo pass if it matters |
| AUD-L10 | `src/migrations/v1_to_v2.py:18` | Docstring references a "migration registry in src/profile.py" that doesn't exist; placeholder untested |
| AUD-L11 | `tests/test_profile.py:92` | Wrong-type threshold values (string, list, out-of-range) silently fall back to defaults — behavior unpinned by tests |
| AUD-L12 | `track-application.md:95`, `setup.md:177`, `find-jobs.md:169`, `coach-prep.md↔coach-drill.md` | Sub-threshold notes: v1.1 skill leaking into user-facing text; setup promises backlog features; hardcoded result tiers ignore config; coach-drill expects prep-brief data no skill ever persists |

---

## What checked out clean

- **Encoding hygiene:** all 28 I/O call sites across src/ use `encoding="utf-8"`; all writes use `newline='\n'` — zero findings
- **Secrets:** `.mcp.json` uses `${VAR}` refs; no literal tokens anywhere including git history
- **`.gitignore`:** every write path in skills and Python is covered (the only leak vector is the workflows' deliberate `git add -f`, AUD-H10)
- **Privacy scrub:** zero real identifiers in all git history; fixture verifiably fictional
- **Test count:** 209 collected — the claim is accurate; the fabrication-detection eval suite is genuinely strong
- **`/try-it` integration:** no contradictions — Rule 1 carve-out, no-write rule, and skill-table listings all consistent

## Suggested fix order

1. **AUD-C1, C2, C3** — two crashes/data-loss bugs + broken onboarding (small, surgical fixes)
2. **AUD-H9, H10, H11, H12** — workflow YAML + privacy/disclosure batch (protects your friends first)
3. **AUD-H4, H5, H6 + M7, M8** — one consistent sweep over the skill files (dual-axis + rules 7/14)
4. **AUD-H13 + M15-M17** — CI workflow + test backfill (prevents recurrence)
5. **AUD-H1, H2, H3 + remaining Medium** — Python robustness batch
6. **Low** — fold into the above where files overlap
