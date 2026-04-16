# /compact — Save Session Before Clearing Context

This skill creates a structured handoff note before you clear context with Ctrl+L. It reads your current job search state from files — nothing is lost when you clear, because everything important lives in files, not in conversation memory.

Run this whenever a session is getting long, or when Claude suggests it.

---

## What This Does

1. Reads all state files to capture current status
2. Captures any mid-session decisions or instructions from this conversation
3. Writes a structured handoff note to `data/session_notes/{today}.md`
4. Confirms it's safe to clear

---

## Reading State

Read the following (silently — don't show raw file contents to the user):

**From `data/processed_listings.yaml`:**
- Count of listings by status (scored, prepared, applied, etc.)
- Any listings in "prepared" status that haven't been tracked as applied yet

**From `coaching_state.md`:**
- Interview Loops: any loops with recent activity (status changes in last session)
- Session Log: last 2 entries

**From `data/session_log.md`:**
- Last 3 lines (recent activity summary)

**From this conversation:**
- What was the user working on in this session?
- What decisions were made? (e.g., "decided to skip Automattic", "updated positioning focus for Deel application")
- Any instructions the user gave that should carry forward?
- What was left unfinished?

---

## Writing the Handoff Note

Write to `data/session_notes/{today's date}.md`. If a file for today already exists, append a new timestamped entry rather than overwriting.

Use these sections (via `file_writer.py` SECTION_KEYS):

```markdown
## Session Summary
**Date:** {today}
**Time:** {current time}

What was worked on:
- {bullet list from conversation}

## Decisions Made
- {key decisions from this session — be specific}

## Next Actions
Priority actions for next session:
1. {most important next step}
2. {second priority}
3. {etc.}

## Pipeline Status
- Listings scored: {count}
- Docs prepared: {count}
- Applied: {count}
- Active interviews: {count}

## Instructions for Next Session
{Any specific instructions the user gave that should carry forward.
If none: "Resume from Next Actions above."}
```

---

## Closing

After writing the file, say:

> "✓ Session note saved to `data/session_notes/{date}.md`
>
> Safe to clear. When you start your next session, say:
> **'Read my last session note'**
> and I'll recap exactly where you left off.
>
> Press **Ctrl+L** to clear context now."

---

## Note on What Gets Preserved

Your job search state is always in files — nothing in the conversation history is load-bearing:
- Job scores and pipeline → `data/processed_listings.yaml`
- Interview loops and coaching state → `coaching_state.md`
- Your profile and preferences → `config/profile.yaml`
- Tailored documents → `data/prepared/{company}/{role}/`

Clearing context only loses the conversation thread. The handoff note captures the thread.
