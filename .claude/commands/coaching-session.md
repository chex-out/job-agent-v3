# /coaching-session — Start a Coaching Session

Initialize a focused interview coaching and storybank session. This skill reads your coaching state and tells you exactly where you left off — no scrolling required.

Run this at the start of any session where you want to build your storybank, do a coaching intake, prepare for an interview, or practice answering questions.

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

**3. Check storybank completeness:**
Read `coaching_state.md`. For each of these sections, check if it has content beyond a placeholder comment:
- `### Career Highlights` — populated?
- `### Positioning Statement` — populated?
- `### Superpower` — populated?
- `### Known Concerns` — populated? (optional but valuable)

A section is **populated** if it contains at least one bullet or paragraph of non-comment text.
Track which sections are missing.

**4. Check interview loops:**
Read `## Interview Loops` section. Extract any entries with status `Interviewing` or `Applied` — these are active.

**5. Check last coaching session:**
Read the last entry in `## Session Log`. Extract the date and first sentence of the summary.
If Session Log is empty or only has the setup entry: no prior coaching sessions.

**6. Check coaching notes:**
Read the last entry in `## Coaching Notes`. If none: no coaching notes yet.

---

## Opening Output

**If recent session notes exist (within 7 days), say this first:**
> "I found notes from your last session on [date]. Want me to recap where you left off before we start?"
Wait for their answer. If yes, read the file and summarize the Next Actions section. Then continue.

**Then print the status header:**

```
## Coaching Session — [name from profile.yaml]

Storybank: [complete ✓ | incomplete — missing: Career Highlights, Superpower, ...]

[If active interviews:]
Active: [Company — Interviewing], [Company — Applied]

[If prior sessions:]
Last session: [date] — [first sentence of last Session Log entry]

[If coaching notes:]
Coach note: [last line of Coaching Notes]
```

If `coaching_state.md` doesn't exist or is completely empty:
> "Your coaching state hasn't been initialized yet. Run `/setup` first, then come back here."
Stop here.

If storybank is fully empty (all sections are placeholders):
> "Your storybank is empty — we'll need to build that before coaching is most effective."

---

## Scope Statement

After the header, always say:

> "This is your coaching session. I'll focus on: `/build-storybank`, `/coach-kickoff`, `/coach-prep [company]`, `/coach-drill`, `/coach-hype`.
>
> For job searching and applications, start a fresh session with `/job-search-session`."

---

## Suggested Next Action

Pick **one** based on current state (priority order):

| State | Suggestion |
|---|---|
| No profile / no coaching_state | Already handled above — stop |
| Storybank completely empty | `→ Run /build-storybank to build your career story database (~10 min). This unlocks everything else.` |
| Storybank partial (some sections missing) | `→ Run /build-storybank to complete your storybank — [list missing sections] are still missing.` |
| Storybank complete, no kickoff ever done | `→ Run /coach-kickoff for a full coaching intake — it builds on your storybank and sets your coaching strategy.` |
| Active interview loop (Interviewing status, interview today/tomorrow) | `→ Run /coach-hype [Company] — your interview is soon. Get your confidence brief and warmup routine.` |
| Active interview loop (Interviewing status, prep done) | `→ Run /coach-drill to sharpen your answers, or /coach-hype [Company] when the interview is close.` |
| Active interview loop (Applied status) | `→ Run /coach-prep [Company] to get ready in case they reach out — you've applied there.` |
| Kickoff done, no recent drill | `→ Run /coach-drill to practice answering questions. Pick a type: behavioral, motivation, situational, or role-specific.` |
| Recently drilled | `→ Run /coach-drill [next type] to keep building. Or run /coach-prep [Company] for targeted prep.` |

---

## End-of-Session Reminder

Embed this note at the bottom of your opening message:

> *When this session gets long, run `/compact` to save your progress, then `Ctrl+L` to clear context. Your storybank and coaching notes are always preserved in `coaching_state.md`.*
