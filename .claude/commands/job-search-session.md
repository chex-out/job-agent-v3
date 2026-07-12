# /job-search-session — Start a Job Search Session

Initialize a focused job search and application session. This skill reads your current pipeline state and tells you exactly where you left off — no scrolling required.

Run this at the start of any session where you want to find jobs, score listings, prepare documents, or track applications.

---

## On Open — Read State Silently

Before saying anything, read the following (do not show raw file contents):

**1. Check for recent session notes:**
Look in `data/session_notes/` for any `.md` files dated within the last 7 days.
If found: note the most recent file's date — you will offer a recap first.

**2. Check profile:**
Read `config/profile.yaml`. If it doesn't exist or has an empty `name` field:
> "Your profile hasn't been set up yet. Run `/setup` to get started — it takes about 10 minutes."
Stop here if profile is missing.

**3. Check pipeline:**
**Never read `data/processed_listings.yaml` in full** (CLAUDE.md rule 14) — `Grep` for `status:`, `prepared:`, `skills_fit:`, and `preference_fit:` fields with line numbers to count and classify, then `Read` with `offset`/`limit` only for the few listings you need to name. Identify:
- Listings with `status: scored` and `prepared: false` where skills_fit >= `scoring.threshold_for_preparation.skills_fit_min` AND preference_fit >= `scoring.threshold_for_preparation.preference_fit_min` — these are **ready for docs**
- Listings with `status: prepared` and `prepared: true` — **ready to apply**
- Listings with `status: interviewing` or `status: applied` — **active**
- Listings with `status: offer` — **offers pending**

If file doesn't exist or is empty: pipeline is empty.

---

## Opening Output

**If recent session notes exist (within 7 days), say this first:**
> "I found notes from your last session on [date]. Want me to recap where you left off before we start?"
Wait for their answer. If yes, read the file and summarize the Next Actions section. Then continue.

**Then print the status header:**

```
## Job Search — [name from profile.yaml]
Targeting: [target_roles joined] in [location]

Pipeline: [N] scored | [N] prepared | [N] applied | [N] interviewing[  | [N] offer]

[If listings ready for docs:]
Ready for docs: [Company] ([skills_fit]/10), [Company] ([skills_fit]/10)

[If listings prepared but not applied:]
Ready to apply: [Company — role]

[If active interviews:]
Active: [Company — status]

[If offer:]
Offer pending: [Company]
```

If the pipeline is completely empty:
> "Your pipeline is empty — no listings scored yet."

---

## Scope Statement

After the header, always say:

> "This is your job search session. I'll focus on: `/find-jobs`, `/score-job`, `/tailor-docs`, `/track-application`, `/queue-digest`.
>
> For interview coaching and storybank work, start a fresh session with `/coaching-session`."

---

## Suggested Next Action

Pick **one** based on current state (priority order):

| State | Suggestion |
|---|---|
| No profile | Already handled above — stop |
| Pipeline empty | `→ Run /find-jobs to search for roles matching your profile.` |
| Offers pending | `→ You have an offer from [Company]. Review it carefully before responding.` |
| Listings ready for docs | `→ Run /tailor-docs to prepare your application for [top company] ([skills_fit]/10).` |
| Prepared but not applied | `→ Documents are ready for [Company]. Apply when ready, then run /track-application to update your status.` |
| Active interviews | `→ Run /coach-prep [Company] to prepare for your upcoming interview — or open a coaching session with /coaching-session.` |
| All closed/skipped | `→ Run /find-jobs to search for new roles.` |
| Scored below threshold only | `→ Run /find-jobs to search for better-matched roles, or run /score-job [URL] to score a specific listing.` |

---

## End-of-Session Reminder

Embed this note at the bottom of your opening message, in a smaller note format:

> *When this session gets long, run `/compact` to save your progress, then `/clear` to clear context. Your pipeline and scores are always preserved in files.*
