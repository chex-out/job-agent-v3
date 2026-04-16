# /reset — Clear Job Search State

This skill wipes your job search state cleanly so you can start fresh. It requires explicit confirmation before deleting anything.

**What gets deleted:** Your profile, job pipeline, coaching state, session notes, and prepared documents.

**What is NOT deleted:** Your resume (`config/resume_base.md`) and cover letter (`config/cover_letter_base.md`) — your actual documents are always preserved.

---

## Confirmation Required

Before doing anything, say exactly this:

> "⚠️ This will permanently delete:
> - Your profile (config/profile.yaml)
> - Your job pipeline (data/processed_listings.yaml, data/input_listings.yaml)
> - Your coaching state (coaching_state.md)
> - Your prepared documents (data/prepared/)
> - Your session notes (data/session_notes/)
>
> Your resume and cover letter files will NOT be deleted.
>
> Type **'yes, reset everything'** to confirm, or anything else to cancel."

Only proceed if the user types exactly "yes, reset everything" (case-insensitive). Any other response cancels.

---

## What to Delete

If confirmed, delete/clear the following:

**Delete files:**
- `config/profile.yaml`
- `data/processed_listings.yaml`
- `data/input_listings.yaml`
- `data/processed_reply_ids.yaml`
- `data/session_log.md`
- `data/hook_errors.log`

**Delete directories (recursively):**
- `data/prepared/`
- `data/session_notes/`

**Reset to empty template (do not delete):**
- `coaching_state.md` — overwrite with the empty template (same format as after /setup, but with no data)

**Recreate empty directories:**
- `data/prepared/`
- `data/session_notes/`
- `data/.gitkeep`

---

## Closing

After completing, confirm each deletion and say:

> "✓ Reset complete. All job search state has been cleared.
>
> Your resume and cover letter are still in `config/` — they were not touched.
>
> Run `/setup` to start fresh."
