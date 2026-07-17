# /watch-company — Manage Your Company Watchlist

Add companies to your ATS watchlist so `/find-jobs` (Mode 6) can poll their job boards directly. Given a company name, detects whether they host jobs on a supported public platform (Greenhouse, Lever, or Ashby) — the same check crowdsourced job bots run when users contribute a company.

---

## Prerequisite Check

1. Check `config/profile.yaml` — must have a non-empty `name`. If missing: "Your profile needs to be set up first. Run `/setup` to get started."

---

## What the user can say

- **A company name** — "watch Stripe", "/watch-company Grab" → detect and add.
- **A job URL or pasted job alert text** (e.g., from a Telegram/email job bot) → extract the company name(s) from it, then detect and add each.
- **"show my watchlist" / no argument** → list current entries.
- **"remove [company]" / "stop watching [company]"** → remove the entry.

---

## Adding a company

1. Extract the company name from whatever the user provided. If they pasted alert text or a URL containing several companies, confirm the list before proceeding.

2. Run detection:
   ```
   python -m src.ats_poller --detect "[Company Name]"
   ```

3. **If detected** — the command adds the company to `data/target_companies.yaml` and prints the ATS, board token, and open-job count. Report it conversationally:
   > "✓ Stripe hosts jobs on Greenhouse (240 open roles). Added to your watchlist — `/find-jobs --watchlist` will now pick up their new postings. `✓ Saved data/target_companies.yaml`"
   Then offer: *"Want me to poll them now?"* — if yes, run `python -m src.ats_poller --company "[name]"` then `python -m src.scout`, and present score cards.

4. **If not detected** — the company doesn't use a supported public job platform (or uses an unusual board token). Say so plainly:
   > "[Company] doesn't appear to use Greenhouse, Lever, or Ashby with a guessable board name. I can still check their careers page directly during `/find-jobs` (Mode 2) — want me to add them to the watchlist with just their careers page URL?"
   If yes, find their careers URL and append a plain entry (name, careers_url, added, source) to `data/target_companies.yaml` using `save_yaml()` from `src/utils.py`. Confirm: `✓ Saved data/target_companies.yaml`

5. **Known board token** — if the user knows the exact board URL (e.g., `jobs.lever.co/acme-corp`), skip detection: extract the token and ATS from the URL and append the entry directly with `save_yaml()`.

## Listing the watchlist

Read `data/target_companies.yaml` and show a compact table: company, ATS (or "careers page only"), date added, last polled. Suggest `/find-jobs --watchlist` if any ATS entries exist.

## Removing a company

Confirm which entry, remove it from the `companies:` list, save with `save_yaml()`, confirm visibly: `✓ Removed [company] from data/target_companies.yaml`.

---

## Closing

- If ATS entries were added: `→ Run /find-jobs --watchlist to poll your watchlist now.`
- If the watchlist has grown large (15+ companies), note that polling stays polite (one request per company per run) so runs may take a little longer.
