# /score-job — Score a Job Listing

Score a single job listing against your profile. Paste a URL or paste the job description text directly.

---

## Prerequisite Check

1. Check that `config/profile.yaml` exists and has a non-empty `name` field. If not: "Your profile hasn't been set up yet. Run `/setup` to get started."
2. Check that `config/resume_base.md` exists. If not: "Your resume hasn't been added yet. Run `/setup` to add it."

---

## Input Handling

Accept any of the following:
- A URL (fetch and score)
- Pasted job description text (score directly, no fetch needed)
- A company name + role title (ask for URL or JD text)

If only a URL is given, say: "Fetching and scoring…" then proceed.
If only text is pasted, score it directly.

---

## Scoring

Load from `config/profile.yaml`:
- `key_skills` — what the candidate brings
- `positioning_strengths` — top signals
- `known_concerns` — likely gaps
- `company_preferences` — minimum_bar, ideal_signals, nice_to_have, deal_breakers
- `scoring.dimensions` — the rubric for skills_fit and preference_fit
- `scoring.threshold_for_preparation` — dual-axis threshold (`skills_fit_min` + `preference_fit_min`) for recommending /tailor-docs

Score the listing on two dimensions (0-10 each):

**skills_fit** — how well can this candidate do this job?
- Role match to target_roles and seniority
- Skills alignment with key_skills
- Location/remote fit
- Apply deal_breakers from scoring.dimensions.skills_fit.deal_breakers

**preference_fit** — how well does this match what the candidate wants?
- Company matches ideal_signals and clears minimum_bar
- No deal_breakers from company_preferences.deal_breakers
- Role scope and autonomy signals

Apply the `feedback_directness` setting from profile.yaml when framing concerns:
- 1-2: lead with strengths, frame concerns gently
- 3: balanced
- 4-5: name concerns directly

---

## Output Format

```
## Score: [Company] — [Role]

**Skills Fit: [X]/10** | **Preference Fit: [Y]/10** | [Assessment label]

**Assessment labels:**
- 9-10: Exceptional Match
- 7-8: Strong Match
- 5-6: Moderate Match
- 3-4: Weak Match
- 0-2: Not a Fit

### Why this works for you
- [2-3 specific strengths referencing JD language]

### Concerns
- [1-3 honest gaps or risks — reference actual JD requirements]

### Company fit
[1-2 sentences on preference_fit reasoning — AI seriousness, scope, culture signals]

### Posting Legitimacy
**Confidence: [High | Proceed with Caution | Suspicious]**
- [Signal checked, e.g. "Company named: ✓", "Description is specific: ✓", "Posted <30 days: ✓", "Apply link goes to company domain: ✓"]
- [Flag if any signal is missing or suspicious]
```

**Legitimacy signals to check:**
- Company is named (not "Confidential Employer" or unnamed recruiter posting)
- Job description is specific — job-specific duties, not a generic template
- Posting is recent (within `search.max_age_days` from profile.yaml — default 30 days)
- Apply link resolves to the company's own domain or a named ATS (Greenhouse, Lever, Ashby, Workday) — not just an aggregator

Confidence levels:
- **High** — all signals clear
- **Proceed with Caution** — 1-2 signals missing or unclear; note which ones
- **Suspicious** — unnamed company, generic description, or apply link leads nowhere

If skills_fit >= `scoring.threshold_for_preparation.skills_fit_min` AND preference_fit >= `scoring.threshold_for_preparation.preference_fit_min`:
> → Run `/tailor-docs` to prepare your application documents.

If either axis is below its threshold:
> → This listing is below your preparation threshold ([which axis] fell short). You can still apply manually, but it's unlikely to be the best use of your time.

---

## Saving the Score

After scoring, save to `data/processed_listings.yaml`:

```yaml
listings:
  - url: [url or "pasted-jd"]
    source: [indeed/linkedin/careers_page/ats/other]
    date_added: [today]
    date_scored: [today]
    company_name: [name]
    role_title: [title]
    location: [location or null]
    skills_fit: [score]
    preference_fit: [score]
    skills_reasoning: [brief]
    preference_reasoning: [brief]
    concerns: [list]
    strengths: [list]
    status: scored
    prepared: false
    digested: false
```

Also write to `coaching_state.md` Interview Loops if skills_fit >= `scoring.threshold_for_coaching.skills_fit_min` AND preference_fit >= `scoring.threshold_for_coaching.preference_fit_min` — using `update_section()` from `src/file_writer.py`:
- Add or update an entry under `## Interview Loops`
- Status: Researched (via Job Agent)
- Include scores and key signals

Confirm: `✓ Scored and saved.`

---

## Closing

After output, always suggest the next step:
- If strong match: `→ Run /tailor-docs to prepare your application.`
- If moderate match: `→ You could apply speculatively — run /tailor-docs if you want to try.`
- If weak: `→ Run /find-jobs to search for better-matched roles.`
