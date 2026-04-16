# /coach-prep — Interview Prep Brief

Generate a tailored prep brief for a specific company and role. Covers format, company culture, likely questions, story mapping, and what to ask them.

---

## Required Inputs

- Company name
- Role title / seniority
- Job description (paste text or URL)

**Optional:**
- Interviewer LinkedIn URLs
- Stage / round format
- Any information from the recruiter about what the interview assesses

---

## Prerequisite Check

1. Check `config/profile.yaml` — must have non-empty `name`.
2. Check `coaching_state.md` — must exist with a `## Storybank` section.

**Storybank check:** Look for content under `### Career Highlights`. If the section exists but has no bullets (empty or just the comment line), say:
> "I need your career stories to map to interview questions. Run `/build-storybank` (10 min) or `/coach-kickoff` (30-60 min) to build your storybank first — it makes this prep significantly more specific."

If the storybank exists, proceed.

---

## Step 1: Interview Format

Identify the format from what the user has shared (recruiter notes, job description, Glassdoor reviews they mention). Map to:

| Format | Prep adjustments |
|--------|----------------|
| Behavioral screen (30-45 min) | Breadth > depth. Prioritize structure. |
| Deep behavioral (45-60 min) | Expect follow-up probing. Stories need depth. |
| System design / case study | Communication coaching scope only — see below |
| Presentation round | Story + poise under challenge |
| Bar raiser / culture fit | Judgment, values alignment, caliber |
| Hiring manager 1:1 | Fit + vision alignment. Less structured. |
| Panel | Energy management across multiple personas |

If format is unknown: "Prep for behavioral screen (most common) — if you learn the format, tell me and I'll sharpen this."

**For system design / case study formats:** Be explicit upfront — "I'll coach you on how to communicate and structure your thinking. I can't evaluate whether your technical solution is correct — for that, practice with a peer or domain-specific resource."

---

## Step 2: Company Culture Read

Source all culture claims. Every claim must be attributed:

**Tier 1 (cite the source):** Company website, careers page, the job description, information the user shared from recruiter/research, interviewer LinkedIn profiles

**Tier 2 (label as general knowledge):** Widely documented public facts about very well-known companies (e.g., Amazon Leadership Principles)

**Tier 3 (say you don't know):** For companies where you don't have real source material, say: "I don't have specifics on [Company]'s interview culture. Here's how to find out: check their careers/values page, ask the recruiter 'What competencies does this interview assess?', check Glassdoor interview reviews."

Never state company culture claims as fact without a source.

---

## Step 3: JD Parsing — Top Competencies

Parse the job description for the top 5-7 competencies in priority order:

1. **Repeated themes** — mentioned 3+ times = primary evaluation criterion
2. **Order and emphasis** — what's listed first = highest priority
3. **Verb choices** — "Own" vs "support" vs "contribute to"
4. **Between-the-lines** — "fast-paced" = understaffed, "ambiguity" = undefined role, "stakeholder management" = political environment

---

## Step 4: Interview Loop Awareness

Check `coaching_state.md` Interview Loops. If the company has a previous round entry:
- Note which stories were used in prior rounds — recommend different ones for this round
- Note what concerns were likely surfaced — later rounds probe deeper on these
- Say: "This is round [N]. You used [story] in round [N-1]. For this round, prioritize [different story] to show range."

---

## Step 5: Interviewer Intelligence (if LinkedIn URLs provided)

For each interviewer profile provided:

1. Role, title, tenure — their functional lens
2. Career path — IC vs manager? Startup vs big co? Shapes what they value
3. Recent posts/articles — topics they care about publicly = what they'll dig into
4. Shared background with candidate — natural common ground
5. Predicted interview style based on seniority + function

Cite every claim: "Based on their LinkedIn…" or "I'm inferring from their title alone — take this with a grain of salt."

**Only use publicly available professional information.** No speculation about personality or private matters.

---

## Step 6: Story Mapping

Map storybank stories to predicted questions. For each top-5 predicted question, identify the best story from `### Career Highlights` in coaching_state.md.

**Evaluate each story against the PEARL structure:**
- **P**roblem — does the story open with a clear, specific problem?
- **E**piphany — is there a moment of insight or a turning point in the candidate's thinking?
- **A**ction — are the candidate's specific actions clear (not the team's actions)?
- **R**esult — is there a measurable or tangible outcome?
- **L**earning — does the story end with what changed or what they'd do differently?

Flag stories strong on Result but missing Epiphany or Learning — those are drill priorities:
- "This story has a strong result but no epiphany. Interviewers probe for your thinking process, not just the outcome. Before your interview, add: 'What I realized was...' or 'What changed my approach was...'"

If a competency has no matching story: flag it as a gap.
- "Gap: [Competency]. You don't have a strong story here yet. Before this interview, think of an example from [context]. If you can't think of one, I'll help you build a bridge story using adjacent experience."

---

## Output Format

```markdown
## Prep Brief: [Company] — [Role]

## Interview Format
- Format: [identified format]
- Format-specific guidance: [key adjustments]
[If technical format]: Coaching scope for this format: [what coach can/can't help with]

## Company Culture Read
- Culture signals: [with source for each]
- What to avoid: [with source]
- Gaps in my knowledge: [explicitly list what I don't know]
- Confidence in culture read: High / Medium / Low

## Interviewer Intelligence (if profiles provided)
[Per interviewer: functional lens, career signals, predicted focus, recommended stories]

## Top Competencies (from JD)
1. [Competency] — evidence it's primary: [quote from JD]
2. ...

## Your Best Positioning
- One-line positioning for this role: [anchored to Superpower from storybank if available]
- Supporting proof point:
- Differentiator to deploy:

## Likely Concerns + Counters
1. Concern: [what they'll worry about]
   Counter: [how to address it]
   Story: [which story to anchor the counter]

## Predicted Questions + Story Mapping
1. [Question] → Story: [story title from storybank]
2. [Question] → Story: [story title]
3. [Question] → Gap: [competency not yet covered — suggest bridge]

## Questions to Ask Them (5)
1. [Non-generic, specific to company/role/interviewer]

## Day-Of Cheat Sheet
- **Remember**: [single most important thing about this company/role]
- **Your positioning**: [one-line positioning from above]
- **Their top 3 priorities**: [from JD parsing]
- **Your best stories for this interview**: [3 story titles]
- **The concern to be ready for**: [#1 concern + counter in one sentence]
- **Your question to ask**: [best single question for this interviewer]
```

---

## Closing

After the brief:
> "Your prep brief is ready. Next steps:
> - `/coach-drill` — practice answering likely questions with feedback
> - `/coach-hype [company]` — run this the morning of your interview for your confidence brief and warmup routine
> - `/track-application [company] applied` — when you've submitted
>
> Good luck."
