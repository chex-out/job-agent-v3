# /track-application — Update Application Status

Update the status of a job in your pipeline via conversation. No YAML editing required.

---

## Prerequisite Check

Check that `data/processed_listings.yaml` exists and has listings. If not: "Your pipeline is empty. Run `/score-job [URL]` to add a listing first."

---

## Input Handling

The user may say things like:
- "I applied to Anthropic"
- "Mark Stripe as applied"
- "I got rejected by Supabase"
- "I have an interview at Automattic"
- "Skip the Adyen listing"
- "I got an offer from Linear"

Extract:
- **Company name** — fuzzy match against `data/processed_listings.yaml` company names
- **Status keyword** — map to one of: applied, interviewing, rejected, offer, skipped, under_review

If the company name is ambiguous (multiple close matches), show the matches and ask: "Did you mean [A] or [B]?"

If no listing is found for the company: "I don't have [company] in your pipeline. Have you scored this listing yet? Run `/score-job [URL]` to add it."

---

## Status Mapping

| User says | Status set | Coaching state updated |
|-----------|-----------|------------------------|
| applied, submitted | applied | Loop: Applied |
| interviewing, interview, screen, phone screen | interviewing | Loop: Interviewing |
| rejected, didn't get it, passed | rejected | Outcome Log: rejected |
| offer, got an offer | offer | Outcome Log: offer |
| skip, skipping, not interested | skipped | No coaching state change |
| under review, reviewing, reviewing my application | under_review | No coaching state change |

---

## Updating State

1. Update `data/processed_listings.yaml` — set the `status` field for the matching listing
2. Update `coaching_state.md` Interview Loops — update Status field for the company entry (if it exists)
3. For rejected/offer outcomes: add a row to the Outcome Log table in `coaching_state.md`

Confirm each update:
- `✓ Updated [Company] → [Status]`
- `✓ Updated coaching_state.md`

---

## Follow-Up Cadence

After updating status, check the listing's `last_contact_date` in `data/processed_listings.yaml` against today's date and surface a follow-up alert:

**Cadence rules:**

| Status | First follow-up | Interval after that | Cap |
|--------|----------------|---------------------|-----|
| applied (no response) | 7 days | 7 days | 2 attempts |
| company responded | 1 day | 3 days | none |
| interviewing | 1 day (send thank-you) | 3 days | none |

**Alert levels — show one if triggered:**
- **URGENT** — company has responded; reply within 24 hours. Draft a reply now if the user wants.
- **OVERDUE** — past the follow-up window with no contact; offer to draft a follow-up message.
- **WAITING** — on track; state the next follow-up date clearly.
- **COLD** — 2+ follow-up attempts with no response; suggest a closure message or moving on.

If `last_contact_date` is not set on the listing, skip the cadence check silently and suggest the user update it when they next make contact.

When drafting follow-up messages:
- Reference something specific from the company or role — not "just checking in"
- Lead with a new signal or question, not a repeat of the last message
- Keep it short: 2-3 sentences maximum

Update `last_contact_date` in `data/processed_listings.yaml` whenever the user reports making contact.

---

## Post-Update Suggestions

After updating status and showing any cadence alert:

| New Status | Suggested next step |
|-----------|---------------------|
| applied | "Great! Run `/coach-prep [company]` to start interview preparation in case they reach out." |
| interviewing | "Run `/coach-prep [company]` to get a tailored prep brief, or `/coach-drill` to practice." |
| offer | "Congratulations! Run `/analyze-offer` when you're ready to think through the decision." (note: v1.1 skill) |
| rejected | "Sorry to hear it. Run `/queue-digest` to see what else is in your pipeline." |
| skipped | "Noted. Run `/find-jobs` if you want to search for more roles." |
