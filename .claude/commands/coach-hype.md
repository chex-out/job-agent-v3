# /coach-hype — Pre-Interview Confidence Brief

Generate a data-driven confidence brief for an interview that's happening today or tomorrow. This is not generic encouragement — every line is grounded in your actual coaching data, practice scores, and storybank.

Run this 10-30 minutes before an interview, or the night before.

---

## Prerequisite Check

1. Check that `config/profile.yaml` exists. If not: "Run `/setup` first."
2. Check that `coaching_state.md` exists. If not: "Run `/setup` first."

---

## Input

Ask: "Which company and role is this interview for? And what's the format — behavioral, technical screen, hiring manager, panel, final round?"

If they mention a specific interviewer name, note it — you'll reference it in the brief.

---

## Reading Coaching State (Silently)

Read `coaching_state.md` and extract:

**Storybank data:**
- `### Career Highlights` — the 2-3 strongest, most interview-ready stories
- `### Superpower` — the one-liner positioning anchor
- `### Known Concerns` — concerns + counter-narratives

**Score trajectory (from `## Coaching Notes` and `## Session Log`):**
- Has the candidate drilled recently? What dimension scores appeared?
- Is there evidence of improvement? (e.g., references to Structure or Credibility scores in notes)
- What has the coach specifically observed about their strengths? Pull direct quotes if present.

**Interview loop context:**
- Read `## Interview Loops` for this company. Has a prep brief been run (`/coach-prep`)? If so, note:
  - The interviewer name and likely focus area
  - The interview format
  - Questions prepared for this interviewer (if saved)
  - The top concern flagged for this specific role

**Data availability assessment (use to determine hype mode):**
- **Rich mode**: Storybank + session log with drill references + Interview Loop with prep brief → use all data
- **Partial mode**: Storybank present but no drill history → build from storybank + resume analysis
- **Sparse mode**: Coaching state exists but storybank is empty → build from `## Resume Analysis` section in coaching_state.md
- **Empty mode**: No coaching data at all → build from profile.yaml strengths, be explicit about the limitation

---

## Output

### 60-Second Hype Reel

Four lines. Every line must be grounded in real data — name actual stories, actual scores, actual moments from coaching. No generic praise.

```
## 60-Second Hype Reel

- [Grounded in score trajectory or storybank strength — e.g., "Your [Story Title] answer has been your most consistent 4-scorer. That story is ready."]
- [Specific evidence of capability — reference a skill with proof, e.g., "The [Company] example is the clearest proof of your [key skill]."]
- [Reference to a best story mapped to this interview — e.g., "Your [Story Title] is directly mapped to what [Company] will likely probe on."]
- [What makes this candidate different — pull from Superpower or positioning — e.g., "You're the candidate who [superpower one-liner]. That's what they don't see every day."]
```

**If operating in Sparse or Empty mode**, open with:
> "I don't have practice scores or storybank data to draw from yet — this brief is built from your resume and profile. It'll be sharper after a few `/coach-drill` sessions."

Then build from whatever is available — do not skip the hype reel, just label its source.

---

### Pre-Call 3x3

**3 Likely Concerns + Counters**

Pull from `### Known Concerns` in storybank if populated. If an Interview Loop entry exists for this company, prioritize the concern flagged there. Otherwise, infer from the role and the candidate's known profile gaps.

Format each as: **Concern** → **Counter (one sentence max)**

**3 Questions To Ask**

If questions were saved in the Interview Loop for this company (from a prior `/coach-prep` run), pull directly from there — do not regenerate. Consistency matters.

If no prior questions exist, generate 3 using this criteria:
- One question that demonstrates you've done your homework on the company specifically
- One question about what success looks like in the first 90 days
- One question for this interviewer specifically, based on their likely focus area or background

```
## Pre-Call 3x3

### Likely Concerns + Counters
1. [Concern] → [One-sentence counter]
2. [Concern] → [One-sentence counter]
3. [Concern] → [One-sentence counter]

### Questions To Ask
1. [Question — label: homework / success criteria / interviewer-specific]
2.
3.
```

---

### Focus Cue

One thing. The single most important thing to keep in mind in the room — specific to this company, this role, and this candidate's coaching history.

Not "be confident." Something actionable and grounded:
- A delivery reminder based on what coaching has flagged (e.g., "State your result in sentence 1 — don't bury it.")
- A positioning note (e.g., "Open every answer by anchoring to your superpower — they need to leave knowing you're [one-liner].")
- A format reminder if this is a specific interview type

```
## Focus Cue
[One specific, actionable thing for this interview]
```

---

### 10-Minute Warmup Routine

Always include this section verbatim, with their specific content filled in:

```
## 10-Minute Warmup

1. Read this hype reel out loud once. Not in your head — out loud.
2. Deliver [their strongest mapped story] out loud in 60 seconds. Don't aim for perfect — aim for natural.
3. Read the 3x3 above. Don't memorize it — just refresh it.
4. Physical reset: [walk, stretch, breathe — whatever your routine is]. Arrive physiologically calm, not cognitively loaded.
5. Reframe: "This is a conversation to see if there's mutual fit. I'm also interviewing them."
```

---

### If You Bomb an Answer Mid-Interview

Always include this section:

```
## If You Bomb an Answer

That answer is done. The interviewer has already moved on — you should too.

Script: "That answer wasn't my best. I'm going to give this next one my full attention."

Don't over-apologize. Don't go back to fix it unless the interviewer invites you to. Channel your attention forward.
```

---

### If You Get a Question You Have No Story For

Always include this section, with their specific gap patterns filled in if known from coaching:

```
## If You Don't Have a Story for It

"I haven't faced that exact situation, but the closest I've come is [adjacent experience].
Here's what I learned that I'd apply to [the scenario]..."

This is Pattern 1: Adjacent Bridge. It works because it's honest and demonstrates judgment.

Avoid: saying "I haven't done that" and stopping. Always bridge to what you *can* offer.
```

If a relevant concern is known from coaching (e.g., a specific competency the candidate has flagged as a gap), name the adjacent bridge for that specific competency.

---

### If You Have Back-to-Back Interviews

Only include this section if the user mentions multiple interviews or a full panel day:

```
## Back-to-Back Reset Protocol

Between interviews:
- 5-minute physical reset. Stand up, walk, get water. Don't review notes.
- Mental reset: "That interview is done. I can't change it. This one starts fresh."
- Don't carry energy from the previous interview — good or bad. Each interviewer meets you for the first time.
- If the last one went poorly: "That conversation is over. This interviewer doesn't know and doesn't care."
- Glance at the Day-Of Cheat Sheet for the next interviewer only if they're different.
```

---

## Closing

After delivering the brief:

> "You're ready. Go get it.
>
> After the interview, run `/coach-drill` to debrief while it's fresh — or just note what questions came up so we can work on them next session."
