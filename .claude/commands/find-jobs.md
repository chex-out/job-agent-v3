# /find-jobs — Search for Matching Jobs

Search for job listings matching your profile using multiple sources. Scores results and adds them to your pipeline.

---

## Prerequisite Check

1. Check `config/profile.yaml` — must have non-empty `name`, `target_roles`, and `location`. If missing: "Your profile needs to be set up first. Run `/setup` to get started."

---

## How a Search Runs

Every search moves through three stages: **Discover → Score → Enrich**. Discovery pulls from all default sources that apply; the user never has to pick a source.

Flags narrow or extend discovery:
- `/find-jobs` — all default sources below
- `/find-jobs --watchlist` — ATS watchlist only
- `/find-jobs --apify` or `--linkedin` — additionally run that opt-in source (see Additional Sources)

---

## Stage 1 — Discover

Run every default source that applies, in this order. Collect all candidates before scoring.

### Source: ATS Watchlist (applies when the watchlist has ATS entries)

Polls the public job-board JSON APIs (Greenhouse, Lever, Ashby) for every company in `data/target_companies.yaml` that has `ats:` and `board_token:` fields. These are first-party, unauthenticated endpoints — the freshest possible source for a company's openings, with full descriptions included.

1. Execute: `python -m src.ats_poller` (add `--all-roles` if the user asked to see everything, `--company "[name]"` to poll one company). The poller dedupes against the pipeline itself and queues new listings into `data/input_listings.yaml` with `prefetched_text` — do not re-fetch or re-dedup manually.
2. Report what it found per company from its log output (e.g., "Stripe: 240 open jobs, 3 match filters").
3. The queued listings are scored in Stage 2 by `python -m src.scout` (batch mode, uses the prefetched text — no page fetches).

If the user mentions a company that isn't on the watchlist yet, offer to detect and add it via the `/watch-company` flow before polling.

**In `--watchlist` mode:** run ONLY this source. If the watchlist is empty or has no ATS entries, say: *"Your watchlist is empty. Run `/watch-company` to add companies — give me a name and I'll detect whether they're on a supported job platform."* — and stop.

### Source: Indeed (always applies)

Use the `search_jobs` tool from the Indeed MCP. Generate queries from `profile.yaml`:

For each target role in `target_roles`, generate 2-3 search queries using:
- Role title variations (e.g., "Marketing Manager", "Growth Marketing Manager", "Demand Generation Manager")
- Location from `profile.yaml`
- Keywords from `additional_keywords` in `profile.yaml`

For each result, use `get_job_details` to fetch the full listing text. Filter out listings older than `search.max_age_days` in profile.yaml (default: 30 days).

Deduplicate against URLs already in the pipeline. Use `Grep` to search for each URL in `data/processed_listings.yaml` and `data/input_listings.yaml` — never read these files in full.

### Source: Company Career Pages (applies when target companies are identified)

If the user mentions specific companies, or if previous sessions have identified target companies, check their careers pages directly.

For each target company:
1. Find their careers page URL
2. Fetch the page using Firecrawl if configured, otherwise fall back to trafilatura:
   - **Firecrawl (preferred):** Use the `firecrawl_scrape` MCP tool with extraction schema `{ job_title, location, work_mode, apply_url, description }`. Firecrawl handles JavaScript-rendered pages (Ashby, Lever, Greenhouse, Workday) that trafilatura cannot parse.
   - **Fallback:** If `FIRECRAWL_API_KEY` is not set, use `fetch_page_text()` via trafilatura as before.
3. Scrape for open roles matching target titles
4. For each matching role, add to scoring queue

Add confirmed target companies to `data/target_companies.yaml` for future sessions:
```yaml
companies:
  - name: [company]
    careers_url: [url]
    added: [date]
    source: [user_specified/auto_detected]
    ats: [greenhouse/lever/ashby]     # optional — set by /watch-company detection
    board_token: [slug]               # optional — enables watchlist polling
```

When adding a company here, also try ATS detection (`python -m src.ats_poller --detect "[company]"`) so the watchlist source can poll it directly in future runs — the JSON API beats scraping the careers page.

---

## Stage 2 — Score

For each new listing found (not already in pipeline), score it using the profile rubric from `profile.yaml`:

**skills_fit** (0-10): role match, skills alignment, location fit, deal-breakers
**preference_fit** (0-10): company type, AI seriousness, role scope, autonomy signals

Add all scored results to `data/processed_listings.yaml` using `save_yaml()` from `src/utils.py`. (Watchlist candidates queued in `input_listings.yaml` are scored with `python -m src.scout`.)

For listings where both skills_fit ≥ `scoring.threshold_for_coaching.skills_fit_min` AND preference_fit ≥ `scoring.threshold_for_coaching.preference_fit_min`, add an entry to `coaching_state.md` Interview Loops using `update_section()` from `src/file_writer.py`.

---

## Stage 3 — Enrich (Glassdoor, top results only)

After scoring, for the top 5 results by combined score (configurable via `search.glassdoor_enrich_limit` in profile.yaml, max 10):

For each company, search for their Glassdoor page and extract:
- Overall rating
- Top 2-3 "Pros" themes
- Top 2-3 "Cons" / red flags

Flag ratings below 3.0 with ⚠️ in the score card. Add culture notes to the listing record.

Hard cap: never enrich more than `glassdoor_enrich_limit` listings per search run.

---

## Additional Sources (opt-in, flag-gated)

Two more sources exist with real trade-offs (account risk, third-party actors). Never run them by default. If the user asks "can you search LinkedIn?", explain the trade-offs below and the flag to use — do not proceed on the same turn as the explanation.

### Apify LinkedIn Search (`--apify` flag required)

**Only run if the user explicitly invokes `/find-jobs --apify`.**

Apify provides authenticated LinkedIn job search via proxy-backed actors — without browser automation. Returns skills data, applicant insights, and recruiter details that unauthenticated scraping cannot access. Requires `APIFY_TOKEN` in `.env`.

If `APIFY_TOKEN` is not set, respond: *"Apify search requires an API token. Add `APIFY_TOKEN=your_token` to your `.env` file. You can get one at apify.com."* — then stop.

**Cookie consent (required before any setup or run):**

Before the first Apify run in a session, display this and require explicit confirmation:
> "Before we set this up, understand what LinkedIn session cookies are:
> - They grant **complete access to your LinkedIn account** — anyone holding them can act as you
> - They will be stored in **plain text** at `config/linkedin_cookies.json` on this machine (gitignored, never committed)
> - Each search sends them to an **Apify cloud actor written by a third-party developer** (`curious_coder`), not by Apify or Anthropic
> - To revoke them at any time: log out of LinkedIn in the browser you exported from, or change your LinkedIn password — both invalidate the exported cookies
>
> Comfortable proceeding?"

Do not proceed without a clear yes.

**Authentication setup (one-time):**

1. **LinkedIn cookies** — required. Check for `config/linkedin_cookies.json`. If missing, prompt:
   > "Apify mode needs your LinkedIn session cookies. Export them using the Cookie-Editor Chrome extension while logged into LinkedIn (export as JSON array), then save the file to `config/linkedin_cookies.json`."
   Do not proceed until the file exists.

2. **User agent** — check `profile.yaml` for `linkedin.user_agent`. If missing or empty, prompt the user to paste their browser's user agent string (find it at `whatismybrowser.com`) and save it to `profile.yaml` under `linkedin.user_agent` using `save_yaml()` from `src/utils.py`. This is a one-time setup.

**Search URL construction:**
Construct a LinkedIn Jobs search URL programmatically (do NOT open a browser):
- Base: `https://www.linkedin.com/jobs/search/?`
- `keywords=` — URL-encoded target role title from profile.yaml
- `location=` — URL-encoded location from profile.yaml
- `f_JT=F` — Full-time filter

Example: `https://www.linkedin.com/jobs/search/?keywords=Product%20Manager&location=Singapore&f_JT=F`

If the user has a preferred LinkedIn geoId for their location, they can add it to `profile.yaml` under `linkedin.geo_id` and the URL should use `geoId=` instead of `location=`.

**Actor:** `curious_coder/linkedin-jobs-search-scraper`

**Actor input:**
```json
{
  "searchUrl": "[constructed LinkedIn Jobs URL]",
  "cookies": [contents of config/linkedin_cookies.json],
  "userAgent": "[from profile.yaml linkedin.user_agent]",
  "count": 25,
  "scrapeJobDetails": true,
  "scrapeSkills": true,
  "scrapeCompany": false
}
```

**Cookie rejection handling:** If Apify returns an auth error or zero results, prompt:
> "Your LinkedIn cookies may have expired. Re-export them using Cookie-Editor while logged into LinkedIn, then replace `config/linkedin_cookies.json`."

Results from this source go through Stages 2-3 like any other. Deduplicate against URLs already in the pipeline.

**Note:** Even via API, scraping LinkedIn may conflict with their terms of service. This source is opt-in for users who accept that risk. Claude does not endorse scraping any platform in violation of its ToS.

### LinkedIn via Chrome Extension (`--linkedin` flag required)

**Only run if the user explicitly invokes `/find-jobs --linkedin`.**

Before running, display this consent prompt and require confirmation:
> "Searching LinkedIn via browser may violate LinkedIn's terms of service and could result in account restrictions. I will only read job listings — no profile interactions, no messages sent, no applications submitted. Continue?"

If confirmed:
- Use the Chrome Extension to navigate to LinkedIn Jobs
- Search for target role titles + location
- Extract listing titles, companies, and URLs only
- Do NOT interact with profiles, send messages, or take any action beyond reading listings

This source is strictly read-only on job listings. Any other action is out of scope.

---

## Output Format

Present results as ranked score cards:

```
## Search Results — [date]

Found [N] new listings. Scored [N]. Above threshold: [N].

### Top Matches

**[Company] — [Role]**
Skills: [X]/10 | Preference: [Y]/10 | [Assessment]
📍 [Location] | [Source]
[1 sentence: why this is a strong match]
Strengths: [bullet 1], [bullet 2]
Concerns: [concern if any]
[Glassdoor: [rating]/5 — [1-line culture note]] (if enriched)
→ Run /tailor-docs to prepare documents

---

**[Company] — [Role]**
...
```

Show top matches first (both axes at or above `scoring.threshold_for_preparation`), then watchlist (within 1 point of either axis), then passed — or omit passed if the list is long.

---

## Updating the Pipeline

After showing results:
- Ask: "Want me to prepare documents for [top company] now?"
- If yes: run `/tailor-docs` logic for that listing immediately.

---

## Closing

After results:
- `✓ Pipeline updated: [N] new listings added`
- `✓ Updated coaching_state.md with [N] Interview Loop entries`
- Suggest: `→ Run /tailor-docs to prepare documents for [top match]` or `→ Run /queue-digest to see your full pipeline.`

**Storybank nudge:** If any Interview Loop entries were written this run AND `### Career Highlights` in `coaching_state.md` is empty, add one line:
> `→ Strong matches are heading toward interviews, but your storybank is empty — 10 minutes on /build-storybank now makes every prep brief and tailored document sharper.`
