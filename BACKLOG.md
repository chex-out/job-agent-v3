# Backlog — Job Seeker AI Toolkit

Skills deferred to v1.1 and beyond. All are designed to slot cleanly into the existing architecture (profile.yaml + coaching_state.md + data/).

---

## v1.1 — Coaching Depth

### `/coach-debrief`
**Trigger:** After an interview.
**What it does:** Structured debrief session — what questions came up, how each answer landed, what to do differently next time. Writes observations to `coaching_state.md` coaching notes. Closes the loop on `/coach-prep`.

**Inputs needed:** Interview details (company, role, round, format), self-assessment of how it went.
**Outputs:** Debrief notes written to coaching state, updated Interview Loop status, priority adjustments for next round prep.

---

### `/coach-concerns`
**Trigger:** When the user wants to work on a specific worry before an interview.
**What it does:** Deep-dive on one concern at a time (career gap, seniority mismatch, domain switch). Builds a reframe, tests it through mock delivery, and saves the polished counter-narrative to storybank.

**Inputs needed:** The concern to work on (from `known_concerns` in profile or typed by user).
**Outputs:** Counter-narrative written to `### Known Concerns` in coaching_state.md storybank.

---

### `/analyze-offer`
**Trigger:** After receiving a job offer.
**What it does:** Structured offer analysis grounded in the research finding that the highest-leverage negotiation is almost never about compensation — it's about the conditions that determine whether you'll succeed.

**Structure (from Lenny's "Negotiating Offers" research, 35 leaders):**
- Step 1: Identify the **success factors** for this role — tech debt, budget, headcount, authority to make decisions, team quality. These are the real negotiation targets.
- Step 2: Evaluate whether those success factors are present in the offer as described. This is the real pass/fail question.
- Step 3: Compensation analysis last. Note: simply asking improves outcomes 87% of the time — the skill builds in this nudge.
- Step 4: Draft collaborative language with the user: *"Are you open to...?"* framing, not *"I need..."*
- Step 5: Prepare for a **live verbal conversation**, not email back-and-forth — coach the actual exchange.

**Inputs needed:** Offer details (base, equity, benefits, start date, role scope, team structure).
**Outputs:** Success factors assessment, negotiation priorities ranked, drafted talking points, coaching for live conversation. Offer summary written to Outcome Log in coaching_state.md.

---

## v1.1 — Job Discovery

### `/rejection-analysis`
**Trigger:** After a rejection or after applying to 10+ roles without interviews.
**What it does:** Pattern analysis across the pipeline — which roles convert, which don't, common concerns that appear across rejections. Produces a recalibration recommendation: adjust targeting, positioning, or prep approach.

**Inputs needed:** Pipeline data from `data/processed_listings.yaml` (Grep for status fields — never full read) + outcome log from coaching_state.md.
**Outputs:** Analysis written to Coaching Notes. Specific recommendations in one of three areas:
1. **Targeting** — are the roles scored too high / wrong archetype / wrong seniority?
2. **Positioning** — are the same concerns appearing across rejections that map to `known_concerns` in profile.yaml?
3. **Prep** — are rejections clustered at a specific stage (screen, hiring manager, technical)?

Surface top 2-3 patterns with suggested adjustments — not a comprehensive audit. Ask the user which pattern they want to act on first before writing to Coaching Notes.

**Dependency:** Requires at least 5 listings with `rejected` or `applied` status in the pipeline.

---

### `/outreach-draft`
**Trigger:** When the user wants to reach out to someone (warm intro request, cold outreach to hiring manager, thank-you note after interview).
**What it does:** Drafts a targeted outreach message using storybank content. Requires `/build-storybank` to have been run.

**Message architecture (from career-ops, adapted):**
- **Recruiter:** Direct fit signal → one screening data point → offer to share resume
- **Hiring Manager:** Name a team challenge → quantified proof point → propose a conversation
- **Peer / warm intro:** Acknowledge their work → name shared problem space → ask a specific question
- **Interviewer (thank-you):** Reference something specific from the conversation → connect it to your experience → express genuine interest

**Constraints:**
- LinkedIn messages: 300 characters maximum
- Email: 3-4 sentences; no preamble, no "I am writing to…"
- Proof points sourced only from storybank — no invented claims
- Never sends anything — Claude drafts, user sends

**Inputs needed:** Target person + context (who they are, relationship, purpose of outreach).
**Dependency:** Requires `### Positioning Statement` in storybank to be populated.

---

## v1.2 — Optimization

### `/linkedin-optimizer`
**Trigger:** When the user wants to update their LinkedIn profile.
**What it does:** Rewrites each LinkedIn section (headline, about, experience bullets) using storybank content and positioning. Outputs copy ready to paste into LinkedIn — does not automate any LinkedIn actions.

**Inputs needed:** Current LinkedIn profile text (paste or URL fetch).
**Outputs:** Rewritten sections for each profile block, optimized for discoverability and clarity.

**Dependency:** Requires `### Positioning Statement` and `### Career Highlights` in storybank.
**Note:** No browser automation — copy/paste only. LinkedIn automation is TOS risk.

---

### `/career-gaps`
**Trigger:** When the user has a career gap they need to address in interviews or on their resume.
**What it does:** Builds deployment-ready narratives for each gap — what to say when asked directly, how to reference it naturally in cover letters, and how to position the period as intentional (if true) or frame it neutrally.

**Inputs needed:** The gap(s) — dates, what happened, what the user did during (even informally).
**Outputs:** Gap narratives written to `### Known Concerns` section of storybank.

**Dependency:** Requires `/build-storybank` to have been run.

---

## Architecture Notes for Implementers

All v1.1 skills follow the same conventions as existing Suite C skills:

1. **Prerequisite check first** — profile.yaml + storybank content check before doing any work
2. **Write via `update_section()`** — never raw string appends to coaching_state.md
3. **Confirm every file write** — `✓ Saved [file]`
4. **Always end with a next step** — never leave the user without a clear action
5. **`feedback_directness` applies** — pull from profile.yaml for any feedback delivery

For skills that touch `processed_listings.yaml`, use `Digest` / `Scout` class-based API with `data_dir` constructor param — never module-level constants.
