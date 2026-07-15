# Job Seeker AI Toolkit — Claude Context

## What This Project Is

A collection of Claude Code skills that turn any job seeker into a power user. Non-technical users clone this repo, run `/setup`, and get a complete AI-powered job search assistant — no YAML editing, no Python, no configuration files.

**The differentiating factor:** Deep personalization. Every output (scored jobs, tailored resumes, interview prep) is anchored to a rich user profile and storybank. Generic tools produce generic outputs; this toolkit produces outputs indistinguishable from a human career coach who knows everything about the user.

**Who uses it:** Non-technical job seekers who want AI help finding, applying to, and preparing for jobs — but don't want to code.

---

## Tech Stack

- **Claude Code skills** — `.claude/commands/*.md` — the primary user interface
- **Python 3.11+** — heavy logic (scoring, tailoring, coaching)
- **Pydantic v2** — data models (`src/models.py`)
- **PyYAML** — all state files
- **rapidfuzz** — fuzzy company name matching
- **trafilatura + BeautifulSoup4** — web page fetching and parsing
- **Indeed MCP** — job search (primary search mode)

---

## Shared State Architecture

Three files users never edit directly:

| File | Purpose | Owner |
|---|---|---|
| `config/profile.yaml` | Canonical user profile, skills, preferences, scoring config | `/setup` |
| `coaching_state.md` | Job search record, storybank, interview loops, coaching notes | All skills |
| `data/processed_listings.yaml` | Pipeline state: scores, statuses, prepared flags | Python modules |

**Never write raw YAML directly to these files.** Skills use `src/file_writer.py` `update_section()` for `coaching_state.md`. Python modules use `save_yaml()` from `src/utils.py` with `newline='\n'` always.

---

## Skills Reference

### Suite A — Setup & Session Management
| Skill | Purpose |
|---|---|
| `/try-it` | Zero-setup taster — paste resume + one job, get a scored match report; nothing saved |
| `/setup` | 6-step onboarding wizard — creates profile, initializes coaching state |
| `/build-storybank` | 10-min session to build career highlights, positioning, skills evidence |
| `/job-search-session` | Start a focused job search session — reads pipeline state, tells you where you left off |
| `/coaching-session` | Start a focused coaching session — reads storybank + interview loops, tells you where you left off |
| `/compact` | Writes structured handoff note before clearing context with /clear |
| `/reset` | Wipes all state cleanly with confirmation — preserves resume + cover letter |

### Suite B — Job Discovery & Pipeline
| Skill | Purpose |
|---|---|
| `/find-jobs` | Multi-mode search: Indeed MCP + career pages + Glassdoor enrichment |
| `/score-job [URL]` | Score a single job listing against your profile |
| `/queue-digest` | Show pipeline status — what's scored, prepared, applied |
| `/tailor-docs` | Generate tailored resume + cover letter with anti-fabrication validation |
| `/track-application` | Update job status via conversation |

### Suite C — Interview Coaching
| Skill | Purpose |
|---|---|
| `/coach-kickoff` | Full coaching intake — storybank, positioning, concerns, interview stories |
| `/coach-prep` | Prep brief for a specific company/role |
| `/coach-drill` | Practice a question type with feedback |
| `/coach-hype` | Pre-interview confidence brief — data-driven hype reel, 3x3, warmup routine |

### Suite D — Personal Brand
| Skill | Purpose |
|---|---|
| `/content-session` | Draft, edit, and manage content across platforms (LinkedIn, Substack, blog, newsletter, X) — persistent voice guide, platform-specific guidance, storybank as source material |

### Backlog (see BACKLOG.md for specs)
v1.1: `/coach-debrief`, `/coach-concerns`, `/analyze-offer`, `/rejection-analysis`, `/outreach-draft` · v1.2: `/linkedin-optimizer`, `/career-gaps`

---

## Behavioral Rules for Claude

### Session Management

1. **At the very start of every session, before doing anything else**, check whether `config/profile.yaml` exists and has a non-empty `name` field.

   **If the profile is missing or empty (first-time user):** Respond to the user's first message — whatever it is — with:
   > "Welcome to the Job Seeker AI Toolkit.
   >
   > Two ways to start:
   > - **`/try-it`** — 2 minutes. Paste your resume and one job listing, get a scored match report. Nothing is saved.
   > - **`/setup`** — about 10 minutes. Builds your full profile and unlocks everything: job pipeline, tailored documents, interview coaching.
   >
   > Most people start with `/try-it`."
   Do not attempt any other task until `/setup` has been run — **with one exception: `/try-it` runs without a profile by design and is always allowed.**

   **If the profile exists:** Continue normally — proceed to check for session notes (rule 2) and respond to whatever the user asked.

2. **At the start of every session** (returning users), check if `data/session_notes/` contains any `.md` files. If recent notes exist (within 7 days), proactively say: *"I found notes from your last session on [date]. Want me to recap where you left off?"* — then read the file and summarize if they say yes.

3. **Proactively suggest `/compact`** when a session is getting long (many file writes, long conversation, approaching context limits). Say: *"This session is getting long — want to run `/compact` before we continue? It saves your progress so you can safely clear context with /clear."*

4. **After completing significant work** (scoring jobs, tailoring docs, coaching session), suggest the next logical skill. Never leave the user without a clear next step.

### Error Messages

5. **Hook warnings must use plain English** — never expose technical errors to users. Examples:
   - ❌ `YAML parse error: mapping values not allowed (line 12)`
   - ✅ `Your profile file may have been saved incorrectly. Run /setup to check and repair it.`

6. **File errors must name the fix**, not the failure:
   - ❌ `FileNotFoundError: config/profile.yaml`
   - ✅ `Your profile hasn't been set up yet. Run /setup to get started.`

### Writing to Files

7. **Always use `update_section()` from `src/file_writer.py`** for any write to `coaching_state.md` or `data/prepared/*/notes.md`. Never use raw string appends to these files.

8. **Confirm every file write visibly**: `✓ Saved config/profile.yaml` — users need to know what changed.

9. **Read-before-write for reasoning sections**: If a section already exists, overwrite it — don't append. The current reasoning is the only reasoning. Append only to `## Change Log`.

### Anti-Fabrication

10. **/tailor-docs always runs a validation pass** before saving. Never silently save a document that contains unverified claims. If the validation pass cannot run (API error, parse failure), save with a visible warning — not silently.

11. **Certifications are anti-fabrication anchors** — only claim certifications explicitly listed in `profile.yaml`'s `certifications:` field. If a JD mentions a certification the user doesn't have, flag it in Watch Out For, never add it to the resume.

### Profile and Storybank

12. **Check for required profile fields** before running any skill that needs them. If missing: *"Your profile is missing [field]. Run `/setup` to add it."*

13. **Check for storybank content** (not just the section header) before running Suite D skills. A `### Career Highlights` section with no bullets is treated as missing.

### Performance & File Safety

14. **Never read `data/processed_listings.yaml` in full.** It grows large in active use and will exceed context limits. Always use targeted access:
    - Use `Grep` with a pattern and line numbers to locate a specific listing, status, or company name
    - Use `Read` with `offset` and `limit` to read only the relevant section
    - `/queue-digest` in particular must load status counts by grepping for `status:` fields — never by reading the whole file

---

## File Writing Rules

All Python file I/O:
- `open(path, 'w', newline='\n')` — always explicit LF line endings (prevents CRLF corruption on Windows)
- YAML files: always use `save_yaml()` from `src/utils.py` — never raw `yaml.dump()` directly

`src/file_writer.py` `update_section()`:
- Pass `SECTION_KEYS` constants — never freeform strings
- Section content is overwritten, not appended
- Appends one line to `## Change Log` when overwriting existing content
- Change Log capped at 20 entries (oldest dropped on overflow)

---

## Architecture Decisions Log

| Decision | Why | Date |
|---|---|---|
| Skills-based architecture (.md commands) | No-code interface for non-technical users | 2026-03 |
| `coaching_state.md` as plain Markdown | Human-readable, Claude-native, easy to reason about | 2026-03 |
| `profile.yaml` as canonical config | Single source of truth for all personalization | 2026-03 |
| Dual-score model (skills_fit + preference_fit) | Separates capability match from desire match | 2026-03 |
| Anti-fabrication second-pass validator | Prompt constraints alone are not enforcement | 2026-03 |
| `/build-storybank` decoupled from `/coach-kickoff` | Suite D shouldn't require full coaching intake | 2026-03 |
| `file_writer.py` named-section read-before-write | Prevents contradictions when reasoning is updated | 2026-03 |
| Hooks exit 0 always | Silent hook failures beat blocking user workflow | 2026-03 |
| LinkedIn/Chrome as Mode 4 opt-in | TOS risk; default path uses Indeed MCP | 2026-03 |
| `schema_version` in profile.yaml | Enable forward migration without silent failures | 2026-03 |
| Firecrawl as Mode 2 career page fetcher | trafilatura can't render JS-heavy SPAs (Ashby, Lever, Workday); Firecrawl handles rendering + structured extraction; falls back to trafilatura if unconfigured | 2026-04 |
| Apify as Mode 5 opt-in (`--apify`) | Authenticated LinkedIn search via `curious_coder/linkedin-jobs-search-scraper`; uses LinkedIn session cookies + user agent from profile.yaml; returns skills/applicant insights unavailable without auth; lower TOS risk than browser automation | 2026-04 |
| Dual-axis ScoringThreshold (skills_fit_min + preference_fit_min) | Single-int threshold conflated capability match with preference match; dual axis separates them — a weak-preference strong-skills listing should score differently from the reverse | 2026-04 |
| Email tier on GitHub Actions (docs/EMAIL_TIER.md) | Serve friends/family without Claude Code: private repo per person = auth (secrets) + state (commits) + scheduler; email is the interface (JOB: links in, scored digest out, PREPARE reply → tailored docs as attachments). Custom chat harness rejected — would rebuild Claude Code and own its security/UX. Automated discovery deliberately excluded (no reliable headless search engine worth maintaining) | 2026-07 |

---

## Critical Bugs Fixed During Port

| Bug | Original Location | Fix Applied |
|---|---|---|
| `DEFAULT_STATE_PATH` hardcoded to `../../coaching_state.md` | `coach_bridge.py` ~line 17 | Read from `COACHING_STATE_PATH` env var, fallback to `Path.cwd() / "coaching_state.md"` |
| `CONFIG_DIR` / `DATA_DIR` derived from `__file__` | `scout.py`, `preparer.py` | Accept as constructor params |
| `get_email_body()` duplicated | `ingestor.py` + `feedback.py` | Moved to `utils.py`, imported from there |
| Hardcoded thresholds `>= 7` | `scout.py`, `digest.py` | Route through `ScoringRubric.is_above_prep_threshold()` |

---

## Source Project Reference

Original system: `interview-coach-skill-main/job-agent/` (~3,600 LOC). All Python logic ported; architecture rebuilt from scratch as skills-based toolkit.

Critical reference files during port:
- `src/models.py` → Foundation data models
- `src/coach_bridge.py` → State management (path bug fixed)
- `src/scout.py` → Scoring prompt + profile injection
- `src/preparer.py` → Anti-fabrication constraints (preserve exactly)
- `references/commands/kickoff.md` → `/coach-kickoff` skill
