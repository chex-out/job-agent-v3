# /build-storybank — Build Your Career Story Database

This skill builds the minimum viable storybank that unlocks Suite D skills (content creation, profile optimizer, career gap narratives, networking drafts). It takes about 10 minutes via conversation.

The storybank is stored in the `## Storybank` section of `coaching_state.md`. It can be expanded later by `/coach-kickoff` without conflict.

---

## Prerequisite Check

Before starting, verify:
1. `config/profile.yaml` exists and has a non-empty `name` field. If not: "Run `/setup` first to create your profile — it only takes 5 minutes."
2. `coaching_state.md` exists. If not: "Run `/setup` first to initialize your coaching state."

If `### Career Highlights` in `coaching_state.md` is already populated (non-empty), say:
> "You already have a storybank. Want to update it, or is it good as-is?"
> If updating: proceed and overwrite (add Change Log entry).
> If keeping: stop here.

---

## Step 1: Career Highlights

Say: "Let's build your storybank — the career story database I use to make every output specific to you.

First, tell me about 3–5 career highlights. For each one, give me:
- The role and company
- What you did (one sentence)
- A measurable result (numbers are best, but 'significantly improved X' works too)

These can be from any point in your career — pick the ones you're most proud of or that best represent your value."

Wait for the user's response. Ask follow-up questions to sharpen vague highlights:
- "What was the scale of that initiative?"
- "How did you measure success?"
- "What would have happened if you hadn't done this?"

Format each highlight as:
```
**[Role] at [Company]** — [what they did] — [measurable result]
```

---

## Step 2: Positioning Statement

Say: "Now let's write your positioning statement — a one-paragraph summary of who you are professionally that I'll use to open your LinkedIn summary, outreach messages, and cover letters.

Here's what I know from your profile and highlights:
- Target roles: {target_roles from profile.yaml}
- Strengths: {positioning_strengths from profile.yaml}
- Top highlights: {top 2 highlights from Step 1}

Let me draft a positioning statement for you."

Draft a 3-4 sentence positioning statement that:
- Opens with seniority + domain expertise
- Names the specific value they deliver
- Calls out 1-2 differentiators that make them unusual
- Is in first person, conversational, not buzzword-heavy

Show it to the user and ask: "Does this capture you well? What would you change?"

Revise until they're happy.

---

## Step 3: Key Skills with Evidence

Say: "Now let's anchor your key skills with evidence — specific examples that prove you have each skill. This makes the difference between a generic claim ('I'm good at X') and a credible one ('I did X at Company Y with result Z')."

Pull `key_skills` from `profile.yaml`. For each skill, ask for the best piece of evidence:
"What's the best example you have of [skill]? A specific project, result, or moment."

Keep this conversational — one skill per exchange. Cap at 6 skills (most important ones).

Format:
```
**[Skill]** — [evidence: project/result/moment]
```

---

## Step 4: Superpower

Say: "One more thing — the most useful positioning move you can make.

Based on your highlights, positioning statement, and skills, what's the **one thing** you want to be known for? Not a list of strengths — one specific thing that, when someone mentions your name in a hiring context, they immediately associate with you.

Examples:
- 'The marketer who builds demand gen from zero to $10M pipeline'
- 'The PM who ships fast in ambiguous, founder-led environments'
- 'The operator who turns chaos into process without losing the startup feel'

This becomes your positioning anchor — it sharpens your resume summary, your cover letter opening, and the answer to 'tell me about yourself.'"

Draft a superpower statement for the user based on their highlights and positioning, then ask: "Does this capture it? How would you put it in your own words?"

Refine until it feels specific and owned by the candidate — not generic.

---

## Step 5: Known Concerns + Counter-Narratives (Optional but Recommended)

Say: "Last step — this one is optional but makes a big difference. I know from your profile that interviewers may raise these concerns:

{known_concerns from profile.yaml}

For each one, let's build a 1-2 sentence response you can deploy in interviews or embed in outreach. The goal isn't to be defensive — it's to reframe the concern as something neutral or positive.

Want to work through these? (You can skip any you're not worried about.)"

For each concern the user wants to address:
- Suggest a reframe based on their highlights and positioning
- Ask: "Does this feel authentic? How would you naturally say it?"
- Refine until it sounds like them

---

## Writing to coaching_state.md

After all steps, write to `coaching_state.md` using `file_writer.py` `update_section()`:

- Section `career_highlights`: formatted highlights from Step 1
- Section `positioning_statement`: final version from Step 2
- Section `key_skills_evidence`: evidence list from Step 3
- Section `superpower`: final one-liner from Step 4
- Section `known_concerns_bank`: concerns + counter-narratives from Step 5 (if completed)

For each section, if it already exists → overwrite + add Change Log entry with today's date.

Confirm: "✓ Storybank saved to coaching_state.md"

---

## Closing

Say:
> "Your storybank is ready. Here's what's now unlocked:
>
> - `/content-session` — Start writing content (LinkedIn, Substack, blog) using your storybank as source material
> - `/coach-prep [company]` — Prep briefs that map your stories to a specific interview
>
> To go deeper (interview prep, practice drills), run `/coach-kickoff` — it builds on your storybank without replacing it."
