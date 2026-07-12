# /coach-kickoff — Full Coaching Intake

Full coaching intake session. Builds your storybank, analyzes your positioning, maps concerns, and sets up your coaching strategy. Takes 30-60 minutes. Run once at the start of your job search, or when you want a complete coaching refresh.

If you've run `/build-storybank` already, `/coach-kickoff` extends it — it doesn't replace your existing highlights or positioning statement without asking.

---

## Prerequisite Check

1. Check `config/profile.yaml` — must have non-empty `name`. If not: run `/setup` first.
2. Check `config/resume_base.md` — must exist. If not: run `/setup` to add your resume.

If `coaching_state.md` doesn't exist: run `/setup` to initialize it.

---

## Step 1: Coaching Configuration

Ask in one message:

1. "What's your feedback style preference? (1=gentle, 5=unfiltered direct — your profile says [X], change it?)"
2. "Do you have any interviews scheduled? If yes, when? This shapes how we prioritize."
3. "What's your biggest concern going into this search?"
4. "Have you been interviewing already? How have they gone?" Use the answer to classify:
   - **First-time / rusty**: needs fundamentals — storybank building, structure, confidence
   - **Active but not advancing**: needs diagnosis — where are you getting stuck? First rounds or final rounds?
   - **Experienced, refreshing**: needs updating, not rebuilding — focus on recent experience and differentiation

Set the coaching mode based on interview timeline:
- **≤48 hours**: Triage — skip deep storybank, do prep + hype only
- **1-2 weeks**: Focused — prep + one targeted drill on weakest area
- **3+ weeks**: Full — build complete storybank, run progression drills, develop differentiation

---

## Step 2: Resume Deep Analysis

Analyze `config/resume_base.md`. Go deeper than `/setup` did:

1. **Positioning strengths** — What's the strongest narrative thread? What would a hiring manager see in 30 seconds? The 2-3 most impressive signals (scope of impact, domain expertise, trajectory, brand-name companies).

2. **Likely interviewer concerns** — What will interviewers worry about?
   - Career gaps or short tenures (< 1 year)
   - Lateral moves or title regressions
   - Domain switches
   - Seniority mismatches
   - Missing keywords for target roles
   - "Invisible" contributions that don't translate to bullets

3. **Career narrative gaps** — Where the story doesn't connect. Flag transitions that need a ready answer.

4. **Story seeds** — Resume bullets with likely rich stories behind them. Flag 3-6 seeds with: "This bullet about [X] — there's probably a strong story behind it. Let's capture it."

5. **Job search blockers diagnostic** — Identify which of these four blockers is most likely limiting this candidate:
   - **No advocate**: They're applying cold with no one at target companies who can advocate for them internally
   - **Role doesn't exist**: Their target role or seniority level doesn't exist at the companies they're targeting
   - **Not ready for the level**: They're applying to a level they haven't demonstrated yet — skills_fit scores will reflect this
   - **Gap they're not seeing**: A pattern in how they're presenting themselves that's hurting them — profile misread, wrong emphasis, weak resume framing
   Name the most likely blocker explicitly: "Based on what I'm seeing, the biggest barrier here is [X]. Here's what that means for how we prep."

---

## Step 3: Storybank Building

**If `### Career Highlights` in coaching_state.md is already populated (from /build-storybank):**

Show the existing highlights and say: "You already have a storybank from `/build-storybank`. I'll extend it rather than replace it. Let's add interview stories and map them to competencies."

**If storybank is empty:**

Say: "Let's build your storybank — the career story database that powers all interview prep. We need 3-5 core stories. For each one, tell me:
- The situation: what was the context and challenge?
- Your role: what were you specifically responsible for?
- The actions you took (focus on YOUR actions, not the team's)
- The results: numbers are best, but 'significantly improved X' works

These become the source material for every interview question I prep you for."

For each story:
- Ask follow-up questions to sharpen vague answers: "What was the scale?", "How did you measure success?", "What would have happened if you hadn't done this?"
- Identify the **earned secret** — the non-obvious insight the candidate gained from this experience
- Rate story strength (1-5): impact + clarity + differentiation

Also build:
- **Positioning statement** (if not already done by /build-storybank): one paragraph, first-person, opens with seniority + domain, names the specific value delivered, calls out 1-2 differentiators
- **Key skills with evidence** — for each skill in `profile.yaml` `key_skills`, capture the best specific example
- **Known concerns** (if not already done): for each concern in `profile.yaml` `known_concerns`, build a 1-2 sentence counter-narrative that reframes rather than defends

- **Superpower**: If `### Superpower` in coaching_state.md is already populated (from `/build-storybank`), show it and ask "Does this still feel right, or do you want to sharpen it?" If empty, establish it now: "Based on everything in your storybank — what's the ONE thing you want to be known for as a candidate? Not a list of strengths. One specific thing." Draft a candidate statement, refine until it feels specific and owned. Save to `superpower` section via `update_section()`.

---

## Step 4: Positioning + Differentiation

Based on the storybank and resume analysis:

1. What is the candidate's **superpower** — the one specific thing they should be known for in this search?
2. What makes them **non-generic** — what do they have that most candidates in this pool don't?
3. What is the **current biggest risk** going into interviews — the single most important thing to address?

Summarize as a "Readiness Assessment":
```
Current readiness: [not started / has foundation / strong base needs polish]
Biggest risk: [the single most important thing to address]
Biggest asset: [the single strongest thing to build on]
```

---

## Step 5: First Coaching Plan

Set a concrete plan adjusted to interview timeline and interview history:

```
### Immediate (this session or next)
1. [specific action with command]

### This week
2. [specific action with command]
3. [specific action with command]

### Before first interview (ongoing)
4. [specific action with command]
```

---

## Writing to coaching_state.md

After all steps, write to `coaching_state.md` using `src/file_writer.py` `update_section()`:

- `career_highlights` — formatted highlights from storybank
- `positioning_statement` — final version
- `key_skills_evidence` — evidence list
- `known_concerns_bank` — concerns + counter-narratives
- `superpower` — the one-line positioning anchor

**Merge rules** (when /build-storybank was run first):
- `career_highlights`: Skip-if-exists — prompt before any change
- `positioning_statement`: Skip-if-exists — show existing, ask "Refine it, or keep it?"
- `key_skills_evidence`: Merge — add new, never remove existing
- `known_concerns_bank`: Merge — add new, never remove existing
- `superpower`: Skip-if-exists — show existing, ask "Is this still your sharpest positioning anchor?"

Coaching Notes: via `update_section()` — read the existing notes, add key observations from this session (interview history type, emotional state, differentiators noted, coaching mode set), write the whole section back.

Session Log: via `update_section()` — read existing entries, add today's row, write the whole section back.

Confirm: `✓ Coaching state updated.`

---

## Closing

```
## Kickoff Summary
- Track: [Quick Prep / Full System]
- Interview history: [first-time / active but not advancing / experienced but rusty]
- Coaching mode: [triage / focused / full]
- Feedback directness: [1-5]
- Readiness: [assessment]
- Biggest risk: [risk]
- Biggest asset: [asset]

## First Plan
[from Step 5]

Next commands:
- /coach-prep [company] — prep brief for a specific role
- /coach-drill — practice answering questions with feedback
- /find-jobs — search for roles if pipeline is thin
```
