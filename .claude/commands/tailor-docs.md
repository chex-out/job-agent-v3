# /tailor-docs — Generate Tailored Resume + Cover Letter

Generate a tailored resume and cover letter for a specific job listing. Includes an anti-fabrication validation pass before saving.

---

## Prerequisite Check

1. Check `config/profile.yaml` — must have non-empty `name`. If not: run `/setup` first.
2. Check `config/resume_base.md` — must exist. If not: run `/setup` to add your resume.
3. Check `config/cover_letter_base.md` — must exist. If not: run `/setup` to add your cover letter.
4. Check `data/processed_listings.yaml` — must have at least one scored listing.

---

## Target Listing Selection

If the user specifies a company or URL, find the matching listing in `data/processed_listings.yaml`.

If no listing is specified, show listings that are scored and above `scoring.threshold_for_preparation` in `profile.yaml` but not yet prepared:

```
You have [N] listing(s) ready for tailoring:
1. [Company] — [Role] (Skills: [X]/10, Pref: [Y]/10)
2. ...

Which would you like to prepare? (Reply with number or company name)
```

If the user wants to tailor a listing below threshold, confirm: "This listing scored [X]/10 on skills fit — below your preparation threshold of [T]. Want to prepare it anyway?"

---

## Tailoring

Using the loaded profile, resume base, and cover letter base, generate tailored documents for the target listing.

**CRITICAL CONSTRAINT — applies to every tailored output:**
- Do NOT fabricate, invent, or embellish any experience, skill, certification, metric, or accomplishment that does not appear in the source resume
- Do NOT claim certifications not listed in `profile.yaml`'s `certifications:` field
- You MAY: reorder sections, adjust emphasis, reframe using JD language, write a tailored summary from existing content, replace [ROLE]/[COMPANY] placeholders
- If the candidate lacks a required skill, leave the gap visible — do not invent it

Extract the Agent Instructions section from `cover_letter_base.md` (the section after `## Agent Instructions`) — use it to guide tone and emphasis, but do NOT include it in the tailored output.

**Cover letter structural constraint — Pyramid Principle:**
- The first 2 sentences of the cover letter must state the conclusion: why this candidate is the right person for this specific role. No warm-up, no "I am writing to express my interest in..." preamble.
- Start right at the highest-tension moment: lead with the strongest signal, not a formality.
- Example of what NOT to write: *"I was excited to see the Marketing Manager role at Acme AI posted on LinkedIn..."*
- Example of the right approach: *"I've spent 7 years building demand gen from zero at Series B SaaS companies — exactly the motion [Company] is describing for this role."*

---

## Anti-Fabrication Validation Pass

After generating tailored documents, run a validation pass **before saving**:

Say: "Checking your draft for accuracy..."

Send the tailored output + source resume + certifications list to Claude for a second-pass check. Classify each claim as:
- **CONFIRMED** — traceable to source
- **UNCERTAIN** — plausible synthesis (log silently, don't surface)
- **FABRICATED** — not traceable to any source

Apply stricter thresholds to cover letter claims than resume claims.

**If no FABRICATED claims found:**
→ Save immediately, no interruption.

**If FABRICATED claims found:**
Surface to user before saving:
```
I found [N] claim(s) I can't verify against your resume:

1. [Location: resume/cover letter] "[exact claim]" — [why it can't be verified]
2. ...

Options:
- Reply with numbers to confirm they're accurate (e.g., "1, 3 are correct")
- Say "remove them" to edit them out
- Say "confirm all" to save as-is (adds a note that you confirmed)
```

If user removes them: apply targeted surgical edits — only edit the flagged sections, do not regenerate the whole document.
If user confirms individually or all: save with a note in notes.md: "User confirmed [claim] on [date]."

**If validation API call fails:**
Save with a visible warning: "⚠️ The accuracy check couldn't run — please review the documents carefully before submitting."

---

## Saving

Save to `data/prepared/{company_slug}/{role_slug}/`:
- `resume.md` — tailored resume
- `cover_letter.md` — tailored cover letter
- `notes.md` — tailoring notes with these sections:
  - `## What Changed` — 3-5 specific changes made
  - `## Cover Letter Focus` — angle/story emphasised
  - `## Verify Before Submitting` — items to double-check
  - `## Watch Out For` — concerns visible despite tailoring
  - `## Validation Notes` — uncertain claims flagged for review (if any)

Update `data/processed_listings.yaml`: set `prepared: true`, `status: prepared`.

Confirm:
```
✓ Documents saved to data/prepared/[company]/[role]/
✓ Updated pipeline status → prepared
```

---

## Closing

After saving:
> "Your documents are ready. Before submitting:
> - Review `notes.md` → Verify Before Submitting section
> - Check any Watch Out For items — these are concerns the interviewer may raise
>
> When you've applied, run `/track-application` to update your status.
> Run `/coach-prep [company]` to start interview preparation."
