# /setup — Profile Wizard

You are setting up the user's Job Seeker AI Toolkit profile. This wizard builds `config/profile.yaml` and initializes `coaching_state.md` through conversation. The user never edits YAML directly.

If `config/profile.yaml` already exists and is non-empty, detect this at the start and ask: "I found an existing profile. Do you want to update it or start fresh?" Handle accordingly.

---

## Step 1: Identity + Feedback Style

Ask the following in one message:

1. "What's your name?"
2. "What roles are you targeting? (e.g. 'Marketing Manager, Growth Manager')"
3. "How would you describe your seniority? (e.g. mid-career, senior, director)"
4. "Where are you based, and what work arrangement do you prefer — remote, hybrid, or onsite?"
5. "How many years of professional experience do you have?"
6. "How direct do you want feedback to be? Rate 1–5:
   - 1: Gentle — lead with encouragement, frame gaps as growth areas
   - 2: Mostly positive — lead with strengths, raise gaps gently
   - 3: Balanced — equal weight to strengths and gaps
   - 4: Direct — name gaps clearly, brief acknowledgment of strengths
   - 5: Unfiltered — maximum directness, no softening (default)

   (This affects how all feedback across all skills is delivered. Scores and analysis are always honest — only the tone changes.)"

Record all answers.

---

## Step 2: Resume Analysis

Say: "Now paste your resume text, or paste your LinkedIn profile URL. I'll extract your skills, experience, and positioning from it."

After the user provides the resume or URL:

Analyze it and extract:
- **key_skills**: List of 5-10 specific skills with evidence in the resume
- **experience_years**: Calculated from career dates
- **positioning_strengths**: 2-3 most impressive signals (scope of impact, domain expertise, trajectory, brand-name companies). What would a hiring manager see in 30 seconds?
- **known_concerns**: What interviewers will worry about — short tenures, career gaps, domain switches, seniority mismatches, missing keywords
- **certifications**: Any certifications explicitly mentioned

Show your analysis to the user:
> "Here's what I extracted:
> - Key skills: [list]
> - Positioning strengths: [list]
> - Likely concerns: [list]
> - Certifications: [list]
>
> Does this look right? Anything to add or correct?"

Incorporate any corrections before continuing.

---

## Step 3: Company Preferences

Ask these as natural conversation questions (not form fields):

1. "What's the minimum bar a company needs to meet for you to consider it? What would make you immediately skip a listing?"
2. "What are the green flags — the kind of company or role that makes you excited?"
3. "Any absolute deal-breakers?"

Convert their answers into structured lists for:
- `minimum_bar`
- `ideal_signals`
- `nice_to_have`
- `deal_breakers`

Show a summary and confirm before saving.

---

## Step 4: Documents

Say: "Almost done. I need two files from you:

1. **Your base resume** — paste the full text, then I'll save it to `config/resume_base.md`
2. **Your base cover letter** — paste the full text, then I'll save it to `config/cover_letter_base.md`

If you have an Agent Instructions section in your cover letter (EMPHASISE / DE-EMPHASISE / TONE blocks), include it — it helps me tailor cover letters more effectively."

Save both files to their respective paths with `newline='\n'`.

---

## Step 5: Initialize coaching_state.md

Create `coaching_state.md` in the repo root using the template below, populated with everything gathered so far.

Run a Resume Analysis (same logic as Step 2 but more detailed):
- Positioning strengths
- Likely interviewer concerns
- Career narrative gaps (transitions that need a story)
- Story seeds (resume bullets with rich stories behind them)

Write this to the `## Resume Analysis` section.

```markdown
# Coaching State

## Profile
- Name: {name}
- Target roles: {target_roles}
- Seniority: {seniority}
- Location: {location}
- Work arrangement: {preferred_work_arrangement}
- Experience: {experience_years} years
- Feedback directness: {feedback_directness}
- Last updated: {today}

## Resume Analysis
### Positioning Strengths
{positioning_strengths as bullet list}

### Likely Interviewer Concerns
{known_concerns as bullet list}

### Career Narrative Gaps
{transitions that need a story — or "None identified" if clean}

### Story Seeds
{resume bullets with likely rich stories behind them}

## Storybank
<!-- Populated by /build-storybank or /coach-kickoff -->

### Career Highlights
<!-- Format: Role at Company — what you did — measurable result -->

### Positioning Statement
<!-- One paragraph: who you are, what you do, what makes you different -->

### Key Skills with Evidence
<!-- Skill — evidence from resume -->

### Known Concerns
<!-- Concern — your counter-narrative -->

### Superpower
<!-- Populated by /build-storybank or /coach-kickoff -->

## Interview Loops
<!-- Populated by /score-job and /find-jobs -->

## Outcome Log
| Company | Role | Status | Date | Notes |
|---------|------|--------|------|-------|

## Session Log
| Date | Summary |
|------|---------|
| {today} | Profile setup completed via /setup |

## Coaching Notes
<!-- Observations from coaching sessions -->
```

---

## Step 6: Preview + Next Steps

Show a summary of what was created:
- `config/profile.yaml` ✓
- `config/resume_base.md` ✓
- `config/cover_letter_base.md` ✓
- `coaching_state.md` ✓

Then say:

> "You're all set. Here's what you can do now:
>
> - `/find-jobs` — Search for roles matching your profile
> - `/score-job [URL]` — Score a specific job listing
>
> You can also unlock content writing (`/content-session`) and richer interview coaching whenever you're ready — run `/build-storybank` (about 10 minutes) to build your career story database."

---

## File Writing Rules

- All files written with `newline='\n'` (LF line endings)
- Confirm each file write visibly: "✓ Saved config/profile.yaml"
- If any write fails, tell the user exactly which file failed and what to do
- Do not expose YAML syntax errors to the user — say "There was an issue saving your profile. Let me try again."
