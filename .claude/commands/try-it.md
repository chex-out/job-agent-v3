# /try-it — Score a Job Against Your Resume (No Setup)

A zero-setup taster of what this toolkit does. Paste your resume and one job listing — get a scored match report with strengths, gaps, and a sample tailored pitch. Takes about 2 minutes. **Nothing is saved to disk.**

<!-- Score card format: the canonical shape lives in score-job.md's Output Format block. Keep this file, docs/walkthrough.md, and docs/demo.html in sync with it. -->

---

## Prerequisite Check (inverted)

This skill has **no prerequisites** — it is the designated entry point for users without a profile.

If `config/profile.yaml` exists with a non-empty `name`: say *"You're already set up — `/score-job` gives you this plus pipeline tracking and saved history. Want the quick taster anyway?"* Proceed if yes.

---

## Intake — one message, everything at once

Ask for everything in a single message (no multi-step wizard — that's what `/setup` is for later):

> "Two things, pasted right here:
>
> 1. **Your resume** — paste the text (or a LinkedIn profile URL)
> 2. **A job you're eyeing** — paste the listing URL or the job description text
>
> Optional, one line: anything that would make you skip a company, and anything that gets you excited about one?"

If a URL is given for the job, fetch it. If a LinkedIn URL is given for the resume, fetch what's publicly available and note any thin sections.

---

## Inline Profile Synthesis

From the pasted resume, silently extract (do NOT echo a long analysis — go straight to scoring):
- **key_skills** — 5-10 specific skills with evidence in the resume
- **positioning_strengths** — top 2-3 signals a hiring manager sees in 30 seconds
- **known_concerns** — what interviewers will worry about (gaps, tenures, switches)
- **certifications** — only what is explicitly listed (anti-fabrication anchor)

Hold all of this in conversation only.

---

## Scoring — embedded generic rubric

Score with the same component math as the full toolkit (see `config/profile.yaml.example`), so this taster score is directly comparable to a real `/score-job` score later:

**skills_fit (0-10):**
- role_match (0-4): does the role match the function and seniority the resume implies?
- skills_alignment (0-4): how many of the extracted key_skills appear in the JD requirements?
- location_fit (0-2): does the listing's location/remote policy plausibly match the resume's location?

**preference_fit (0-10) — two paths:**
- **If the optional preference one-liner was answered:** score it — deal-breaker check (0 = instant fail signal present), green-flag match, role scope signal. Label the score **"(provisional — based on one question; `/setup` builds your full preference model)"**.
- **If skipped:** render the axis as `**Preference Fit: 🔒 unlocked by /setup**` with one sentence: *"Preference matching scores how much you'd actually want this job — company type, culture signals, scope. It needs the preference profile `/setup` builds."*

---

## Output Format

Use `/score-job`'s exact card shape (it is the canonical format):

```
## Score: [Company] — [Role]

**Skills Fit: [X]/10** | **Preference Fit: [Y]/10 (provisional)** [or 🔒 unlocked by /setup] | [Assessment label]

**Assessment labels:** 9-10 Exceptional Match · 7-8 Strong Match · 5-6 Moderate Match · 3-4 Weak Match · 0-2 Not a Fit

### Why this works for you
- [2-3 specific strengths referencing actual JD language]

### Concerns
- [1-3 honest gaps — reference actual JD requirements; leave real gaps visible]

### Posting Legitimacy
**Confidence: [High | Proceed with Caution | Suspicious]**
- [Company named ✓/✗ · Description specific ✓/✗ · Recent posting ✓/✗ · Apply link resolves to company domain or named ATS ✓/✗]

### Sample cover letter opening
[2-3 sentences. Pyramid Principle: state the conclusion first — why this candidate
is right for this specific role. No "I am writing to express..." preamble.
CRITICAL: do NOT fabricate, invent, or embellish any experience, skill,
certification, metric, or accomplishment that does not appear in the pasted
resume. If the candidate lacks a required skill, do not paper over it.]
```

---

## Hard No-Write Rule

**Do NOT write anything to disk.** No `data/processed_listings.yaml`, no `coaching_state.md`, no `config/` files, no session notes. This skill produces conversation output only. If the user wants the score saved, that's what `/setup` + `/score-job` are for.

---

## Closing Pitch

After the card, close with (adjust the bracketed bits to the actual result):

> "That's the taster. The full toolkit does this for every job you're considering — plus:
> - **`/find-jobs`** — searches Indeed and career pages for you, scores everything against your profile automatically
> - **`/tailor-docs`** — full tailored resume + cover letter for any listing, with an anti-fabrication check before anything is saved
> - **Preference matching** — scores how much you'd *want* each job, not just whether you can do it
> - **Interview coaching** — prep briefs, practice drills, and a story bank built from your actual career
>
> Setting that up takes about 10 minutes: run `/setup`. Nothing from this taster was saved — your resume stays with you until you decide."
