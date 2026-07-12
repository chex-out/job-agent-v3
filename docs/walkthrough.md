# What Using This Toolkit Actually Looks Like

A complete walkthrough with a fictional job seeker. Every output below is in the real format the toolkit produces — persona, company, and numbers are invented, but this is genuinely what you see on screen.

> **Meet Alex Chen** — Product Manager in Singapore, 6 years of experience, strongest at data-informed roadmap work at B2B SaaS companies. Led a 0→1 payments feature launch at a Series B fintech. Two honest concerns: no enterprise-scale experience, and a 14-month tenure at his second company. *(This is the example persona from [`config/profile.yaml.example`](../config/profile.yaml.example).)*

<!-- Score card format: canonical shape lives in .claude/commands/score-job.md's Output Format block. Keep this file, try-it.md, and demo.html in sync with it. -->

---

## Minute 1: `/try-it` — before any setup

Alex clones the repo, opens Claude Code, types `/try-it`, and pastes his resume plus a job listing he's been eyeing.

```
— sample output, fictional persona —

## Score: Meridian Pay — Senior Product Manager, Merchant Payments

**Skills Fit: 8/10** | **Preference Fit: 🔒 unlocked by /setup** | Strong Match

### Why this works for you
- Your 0→1 payments feature launch maps directly to the JD's "own merchant
  payments products end-to-end" — same domain, same motion
- "Comfortable in SQL and data tooling" appears verbatim in the requirements;
  your dashboard work is direct evidence
- Singapore hybrid matches your stated arrangement

### Concerns
- The role wants "experience serving enterprise merchants" — your track record
  is SMB and mid-market; expect this question in the first interview
- "Senior" is one seniority step up from your current title — bridgeable,
  but the JD asks for 7+ years and you have 6

### Posting Legitimacy
**Confidence: High**
- Company named ✓ · Description specific ✓ · Posted 12 days ago ✓ ·
  Apply link resolves to Greenhouse ✓

### Sample cover letter opening
I spent the last two years taking a merchant payments feature from zero to
$2M ARR at a Series B fintech — the same product motion Meridian Pay is
describing for this role. That launch ran on the same rails this JD names:
SQL-heavy discovery, tight sales feedback loops, and shipping into a
regulated space.
```

Preference matching shows locked because Alex hasn't told the toolkit what he *wants* yet — that's the difference between "can I do this job" and "do I want this job," and it's what `/setup` unlocks.

**Nothing was saved.** If Alex walked away now, no trace of his resume remains.

---

## Minute 10: `/setup` — the commitment

Alex decides it's worth it. `/setup` asks him about target roles, preferences, deal-breakers, and takes his resume and cover letter. At the end:

```
— sample output —

✓ Saved config/profile.yaml
✓ Saved config/resume_base.md
✓ Saved config/cover_letter_base.md
✓ Created coaching_state.md

You're all set. Here's what you can do now:
- /find-jobs — Search for roles matching your profile
- /score-job [URL] — Score a specific job listing
```

---

## Day 2: `/score-job` — now with the full preference model

Same listing, scored with his complete profile:

```
— sample output, fictional persona —

## Score: Meridian Pay — Senior Product Manager, Merchant Payments

**Skills Fit: 8/10** | **Preference Fit: 7/10** | Strong Match

### Why this works for you
- 0→1 payments launch maps directly to "own merchant payments end-to-end"
- SQL/data tooling requirement is direct evidence from your dashboard work
- Singapore hybrid matches your preference

### Concerns
- Enterprise merchant experience gap — prepare your SMB-to-enterprise story
- 7+ years asked, you have 6 — lead with scope, not tenure

### Company fit
Series B payments company with a product-led motion — clears your minimum bar
and hits your fintech ideal signal. AI appears in the JD as tooling, not
strategy; that's why preference fit is 7 and not higher.

### Posting Legitimacy
**Confidence: High**
- Company named ✓ · Description specific ✓ · Posted 12 days ago ✓ ·
  Apply link resolves to Greenhouse ✓

→ Run /tailor-docs to prepare your application.
```

The score lands in Alex's pipeline. `/queue-digest` will show it alongside everything else he's considering.

---

## Day 2: `/tailor-docs` — the anti-fabrication moment

This is the part generic AI tools get wrong. Watch what happens:

```
— sample output, fictional persona —

Checking your draft for accuracy...

I found 1 claim I can't verify against your resume:

1. [cover letter] "managed a team of five product managers" — your resume
   shows cross-functional leadership but no direct reports.

Options:
- Reply with numbers to confirm they're accurate (e.g., "1 is correct")
- Say "remove them" to edit them out
- Say "confirm all" to save as-is (adds a note that you confirmed)
```

Alex says "remove it." The final documents contain only claims traceable to his real resume:

```
— cover letter opening, after validation —

I spent the last two years taking a merchant payments feature from zero to
$2M ARR at a Series B fintech — the same product motion Meridian Pay is
describing for this role. Meridian's JD asks for someone who can run
SQL-heavy discovery and ship into a regulated space; that is precisely how
that launch ran.

✓ Documents saved to data/prepared/meridian-pay/senior-product-manager/
✓ Updated pipeline status → prepared
```

And the notes file tells him what to double-check before submitting:

```
— notes.md excerpt —

## Verify Before Submitting
- JD asks for "experience with payment scheme compliance" — your exposure
  is adjacent (regulated fintech), not direct. Be ready to speak to it.

## Watch Out For
- Enterprise merchant gap will likely come up in the hiring manager screen.
```

---

## Week 2: `/coach-prep` — interview scheduled

Meridian Pay calls back. Alex runs `/coach-prep meridian`:

```
— sample output, fictional persona —

## Prep Brief: Meridian Pay — Senior PM, Merchant Payments

### What they'll probe (from the JD)
1. End-to-end product ownership in payments — your strongest ground
2. Enterprise merchant experience — your known gap; counter-narrative below
3. Data-driven prioritisation — direct evidence available

### Story mapping
| Their question | Your story | Angle |
|---|---|---|
| "Walk me through a product you owned end-to-end" | Payments feature 0→$2M ARR | Emphasise regulated-space shipping |

### The gap, handled
When enterprise experience comes up: don't apologise. Your SMB-to-mid-market
work shipped faster feedback loops than enterprise PMs ever see...
```

---

## The point

Every output above came from the same profile — built once, reused everywhere. The scoring, the tailored documents, the coaching: all anchored to what Alex actually did, with a validator that catches anything that isn't.

**Try it yourself in 2 minutes:** clone the repo, run `/try-it`, paste your resume and one job listing. Nothing is saved until you decide.

→ [Setup guide](../README.md) · [Interactive demo (no install needed)](https://chex-out.github.io/job-agent-v3/demo.html)
