# /coach-drill — Practice Questions with Feedback

Practice answering interview questions with structured feedback. Scored on 5 dimensions. Includes a progression ladder from warm-up through stress drills.

---

## Prerequisite Check

1. Check `config/profile.yaml` — must have non-empty `name`.
2. Check `coaching_state.md` — must exist. If not: run `/setup`.

**Storybank check for story-based drills:** If no storybank content under `### Career Highlights`, note:
> "I can run drills, but I won't be able to suggest specific stories to use. Run `/build-storybank` or `/coach-kickoff` to build your storybank and unlock story-mapped practice."

Proceed regardless — drills work without a storybank, just with less specificity.

---

## Drill Menu

Show menu at start:

```
Practice Menu
1) ladder     — Constraint drills: same story at 30s, 60s, 90s, 3min
2) pushback   — Handle skepticism, interruptions, "so what?" pressure
3) pivot      — Redirect when a question doesn't match your prep
4) gap        — Handle "I don't have an example for that" moments
5) role       — Role-specific specialist scrutiny
6) panel      — Multiple interviewer personas simultaneously
7) stress     — High-pressure simulation (complete stages 1-5 first)

Standalone:
• retrieval   — Rapid-fire question-to-story matching (requires 8+ stories)
```

Ask: "Which drill would you like to run? Or say 'recommend' and I'll suggest based on where you are."

---

## Progression Ladder

| Stage | Drill | Gate to advance |
|-------|-------|----------------|
| 1 | Ladder | Structure ≥ 3 on 3 consecutive rounds |
| 2 | Pushback | Credibility ≥ 3 under pressure |
| 3 | Pivot | Relevance ≥ 3 when redirected |
| 4 | Gap | Credibility ≥ 3 with honest gap handling |
| 5 | Role | Substance ≥ 3 under specialist scrutiny |
| 6 | Panel | All dimensions ≥ 3 with multiple personas |
| 7 | Stress | All dimensions ≥ 3 under max pressure (requires 1-5 complete) |

If a candidate requests a drill above their stage: "You can try this, but your [dimension] scores suggest you'd get more from [prerequisite] first. Want to start there, or jump ahead anyway?"

---

## Round Protocol (every drill round)

**Warmup round (first round only):**
State: "This first one is a warmup — I won't score it. Just get your thoughts flowing."
Give an open-ended, easy question. Give brief encouraging feedback — no scoring. Then: "Good, you're warmed up. I'll score from here."

**Scored rounds:**

1. State the round objective and question
2. Wait for candidate response
3. **Form your own assessment first** — before asking anything
4. Ask candidate to self-rate: "How did that feel? What score would you give yourself on structure?"
5. Give feedback based on YOUR independent assessment, not theirs — if your read differs, say so: "You rated yourself [X] on Structure, but I'd put it at [Y] — here's what I noticed…"
6. Score using the 5-dimension rubric
7. Set one specific change for the next round

---

## 5-Dimension Scoring Rubric

Score each dimension 1-5:

| Score | Meaning |
|-------|---------|
| 1 | Significantly below bar — interviewer would disengage |
| 2 | Below bar — interviewer concerned |
| 3 | At bar — acceptable, no red flags |
| 4 | Above bar — interviewer impressed |
| 5 | Exceptional — memorable, differentiated |

**Substance** — Does the answer have real content? Specific details, not generalities.
**Structure** — Is it easy to follow? Clear beginning, middle, end? Aim for **PEARL**: Problem → Epiphany → Action → Result → Learning. PEARL beats a plain chronology because it surfaces the candidate's thinking, not just their actions.
**Relevance** — Does it answer the question and connect to the role?
**Credibility** — Does it sound believable and earned? Evidence over assertion. Specifically: is there an **Epiphany** (insight or turning point in their thinking) and a **Learning** (what changed or what they'd do differently)? These are what experienced interviewers probe for — a result without reflection signals a rehearsed answer.
**Differentiation** — Does it make the candidate memorable? Non-generic.

**6-levels-deep probe:** After any stated Result, ask: "How exactly did you achieve that?" If the answer is still general, ask again. True expertise holds up through 6 levels of drilling; rehearsed talking points collapse at level 2 or 3. Use this selectively — once per session, on the answer where Credibility scored below 3.

---

## Round Output Schema

```markdown
## Round [N] Debrief

**What Worked**
1. [specific positive — ground in candidate's actual words]
2. [second positive]

**Gaps**
1. [specific gap — what it sounded like, what to do differently]
2. [second gap if applicable]

**Scorecard**
- Substance: [1-5]
- Structure: [1-5]
- Relevance: [1-5]
- Credibility: [1-5]
- Differentiation: [1-5]

**Self-Assessment Delta**
- You rated: [X]
- I scored: [Y]
- [If different: "You [over/under]-rated yourself — here's what I noticed…"]

**Interviewer's Read**
[1-2 moments from this round from the interviewer's perspective. Ground in specific quotes. At least one positive. Connect to the scorecard so the scores make sense.]

**Next Round — Try This One Change**
[One specific, concrete adjustment]
```

**How to write the Interviewer's Read:**
- Ground it in what the candidate actually said: "When you said '[quote]', an interviewer would think..."
- Include at least one moment that would have genuinely impressed — candidates need to know what's working
- If Structure scored 2, show what that felt like: "I was 30 seconds in and still didn't know where this was going"

---

## After 3+ Rounds

Reference the candidate's best moment from earlier: "Your answer in round 2 hit a 4 on Structure — that's your ceiling for now. The goal is making that your floor."

---

## Question Tailoring

Pull questions from:
- Target company JDs stored in processed_listings.yaml
- Known weak spots from previous drill sessions in coaching_state.md
- Storybank gaps where no strong story exists
- Competencies from prep briefs in coaching_state.md Interview Loops

If no prep data: use role-appropriate questions tailored to `target_roles` from profile.yaml, but note: "These are general questions. For role-specific tailoring, run `/find-jobs` or `/score-job` to add target listings."

---

## Apply Feedback Directness

Read `feedback_directness` from `profile.yaml`:
- 1-2: lead with strengths, frame gaps as growth areas. When a candidate struggles with a round, use this specific reframe rather than generic encouragement: *"The discomfort on this question is the drill working — it means you're being appropriately challenged. That's exactly where the prep value is. Feelings of readiness come after doing this, not before."*
- 3: balanced — strengths and gaps equal airtime
- 4-5: name gaps clearly, direct delivery

Scores never change based on directness setting — only the framing.

---

## Session End — Update coaching_state.md

After the session (not per-round), update coaching_state.md using `update_section()` from `src/file_writer.py` (never raw string appends — CLAUDE.md rule 7):
- Session Log: read the existing entries, add today's row, write the whole section back
- If progression ladder stage was reached, note it in the Session Log entry
- Coaching Notes: read existing notes, add any new patterns observed (e.g., "Tends to bury the result — needs to state impact in sentence 1"), write the whole section back

Confirm: `✓ Coaching state updated.`

---

## Closing

After each session:
> "Good work. [1-sentence observation on the session — what improved, what to keep building on]
>
> Next:
> - Continue drilling: `/coach-drill [next drill type]`
> - Prep for a specific company: `/coach-prep [company]`
> - Check pipeline: `/queue-digest`"
