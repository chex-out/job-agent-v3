# Job Seeker AI Toolkit

An AI-powered job search assistant that runs entirely inside Claude Code. No coding required — you interact through conversation.

**What it does:**
- Searches for jobs matching your profile
- Scores listings against your skills and preferences
- Generates tailored resumes and cover letters (with fabrication checking)
- Coaches you through interview prep and practice
- Tracks your entire job search pipeline

**What makes it different:** Every output is anchored to your specific profile, career highlights, and positioning. Generic AI tools produce generic outputs. This produces outputs that sound like you.

**See it before you install:** [full walkthrough with sample outputs](docs/walkthrough.md) · [interactive demo](https://chex-out.github.io/job-agent-v3/demo.html) (no install needed)

---

## Prerequisites

Before you start, you need:

1. **A Claude subscription** (Pro or higher) — Claude Code requires a paid plan
2. **The Claude desktop app** (recommended, easiest) — or the Claude Code CLI if you prefer a terminal
3. **Python 3.11 or higher** — used by the toolkit's helper scripts
4. **Your resume text** — have it ready to paste during setup (plain text or Markdown is fine)
5. **A cover letter draft** — a rough starting point to tailor from; doesn't need to be polished

You do **not** need an API key for normal use — everything runs inside your Claude Code session on your subscription. An API key only matters if you later enable the optional GitHub Actions automation.

---

## Try It in 2 Minutes (before committing to full setup)

You don't need the full setup to see what this does — the taster needs only the Claude app and this folder. No Python, no configuration:

1. **Get the toolkit:** on this GitHub page, click the green **Code** button → **Download ZIP**, and extract it somewhere permanent (e.g. Documents)
2. **Open it in Claude:** install the [Claude desktop app](https://claude.ai/download) if you haven't, sign in, click the **Code** tab → **Local** → **Select folder** → choose the extracted folder
3. Type `/try-it`, then paste your resume and one job listing you're eyeing

You'll get a scored match report — strengths, honest gaps, a legitimacy check on the posting, and a sample tailored pitch. **Nothing is saved.** If you like what you see, the full setup below takes about 10 minutes and unlocks the job pipeline, tailored documents, and interview coaching.

---

## Setup: Claude Desktop App (recommended)

The friendliest way to run the toolkit — one app, no terminal for day-to-day use.

### Step 1 — Install the Claude app

Download from [claude.ai/download](https://claude.ai/download) (macOS or Windows), install, and sign in with your Claude account.

### Step 2 — Install Git (Windows only)

Claude Code's local sessions on Windows require Git. Download from [git-scm.com/download/win](https://git-scm.com/download/win) and install with default options. Macs already include it.

### Step 3 — Install Python

Download Python 3.11 or higher from [python.org/downloads](https://www.python.org/downloads/). On Windows, check **"Add Python to PATH"** during installation.

### Step 4 — Get the toolkit

On this GitHub page: green **Code** button → **Download ZIP** → extract somewhere permanent (e.g. Documents). (If you're comfortable with git, `git clone https://github.com/chex-out/job-agent-v3.git` works too and makes updates easier.)

### Step 5 — Open it in Claude Code

In the Claude app: **Code** tab → **Local** → **Select folder** → choose the toolkit folder.

### Step 6 — Let Claude install the dependencies

In the session, type:

> Install this project's Python dependencies

Claude runs the install itself — approve the command when prompted. That's the only "technical" step, and Claude does it for you.

### Step 7 — Run Setup

Type `/setup` and follow the conversation — Claude asks you questions and builds your profile automatically. Takes about 10 minutes. (Or start with `/try-it` if you haven't yet.)

### Step 8 — Enable Job Search (Indeed Connector)

`/find-jobs` uses Claude's official Indeed connector as its primary job source:

1. Go to [claude.com/connectors/indeed](https://claude.com/connectors/indeed) in your browser
2. Click **Add connector** and sign in with the same Claude account
3. Start a new Claude Code session for it to take effect

If you skip this step, `/find-jobs` will only search company career pages for companies you name manually — no automated Indeed results.

---

## Setup: Terminal (CLI) — alternative

Prefer a terminal? The CLI runs the same engine and shares all configuration with the desktop app.

1. **Install Node.js** (LTS from [nodejs.org](https://nodejs.org)), then:
   ```
   npm install -g @anthropic-ai/claude-code
   ```
2. **Install Python 3.11+** ([python.org/downloads](https://www.python.org/downloads/); on Ubuntu/Debian `sudo apt install python3.11 python3-pip`; on macOS `brew install python@3.11`). Windows users: check **"Add Python to PATH"**.
3. **Clone and install:**
   ```
   git clone https://github.com/chex-out/job-agent-v3.git
   cd job-agent-v3
   python -m pip install -e .
   ```
   (macOS/Linux: `pip3 install -e .`)
4. **Start Claude Code and authenticate:**
   ```
   claude
   ```
   A browser window opens to sign in with your Claude account on first run.
5. **Run `/setup`** (or `/try-it` first), then follow Step 8 above to enable the Indeed connector — after adding it, restart with `exit` then `claude`.

---

## Skills Reference

Once set up, everything happens through conversation in Claude Code.

### Getting Started
| Command | What it does |
|---|---|
| `/try-it` | Zero-setup taster — paste your resume + one job, get a scored match report (nothing saved) |
| `/setup` | First-time profile creation (run once) |
| `/build-storybank` | Build your career story database (source material for content and coaching) |
| `/job-search-session` | Start a focused job search session — shows pipeline status and where you left off |
| `/coaching-session` | Start a focused coaching session — shows storybank status and active interviews |

### Finding & Applying to Jobs
| Command | What it does |
|---|---|
| `/find-jobs` | Search for roles matching your profile |
| `/score-job [URL]` | Score a specific job listing |
| `/tailor-docs` | Generate tailored resume + cover letter |
| `/track-application` | Update a job's status |
| `/queue-digest` | See your full pipeline at a glance |

### Interview Coaching
| Command | What it does |
|---|---|
| `/coach-kickoff` | Full coaching intake — positioning, stories, concerns |
| `/coach-prep` | Prep brief for a specific company |
| `/coach-drill` | Practice answering questions with feedback |
| `/coach-hype` | Pre-interview confidence brief — hype reel, 3x3, warmup routine |

### Personal Brand
| Command | What it does |
|---|---|
| `/content-session` | Draft, edit, and manage content across platforms — LinkedIn, Substack, blog, newsletter, X/Twitter — persistent voice guide, platform-specific guidance, storybank as source material |

### Session Management
| Command | What it does |
|---|---|
| `/compact` | Save session notes before clearing context |
| `/reset` | Wipe all state and start fresh (with confirmation) |

---

## Starting a Focused Session

If you're doing one type of work (job searching OR coaching — not both), use a session launcher instead of starting fresh. Launchers read your current state and tell you exactly where you left off.

```
/job-search-session    → for finding jobs, scoring listings, preparing documents
/coaching-session      → for storybank, interview prep, practice drills
```

Each launcher shows a compact status summary and suggests the single best next action. You don't need to remember where you were.

---

## Managing Long Sessions

Claude Code has a context window limit. For long job search sessions:

1. When the session feels long (or Claude suggests it), run `/compact`
2. `/compact` saves everything to `data/session_notes/` — nothing is lost
3. Type `/clear` to clear context
4. Next session, start fresh with `/job-search-session` or `/coaching-session` — they'll recap where you left off automatically

All your job search data lives in files, not in the conversation. Clearing context only loses the chat thread.

---

## Optional: Enhanced Job Search Integrations

These integrations extend the search stack beyond the default Indeed connector + trafilatura. All are opt-in — the toolkit works without them.

Each one needs a key in a `.env` file at the toolkit's root. If that file doesn't exist yet, just ask Claude in your session: *"Copy .env.example to .env and add my Firecrawl key: [paste key]"* — it handles the file for you.

### Firecrawl — Better Career Page Scraping

By default, `/find-jobs` Mode 2 (career pages) uses trafilatura to fetch page content. Trafilatura works for static pages but fails on modern JavaScript-rendered career sites (Ashby, Lever, Greenhouse, Workday). Firecrawl handles JS rendering and returns clean structured data.

**Setup:**
1. Create an account at [firecrawl.dev](https://www.firecrawl.dev) — free tier includes 500 pages/month
2. Copy your API key
3. Add to `.env`: `FIRECRAWL_API_KEY=your_key_here`
4. The `.mcp.json` file in the repo already has the Firecrawl MCP configured — Claude Code will load it automatically

Once configured, Mode 2 will automatically use Firecrawl for career pages and fall back to trafilatura for any pages it can't handle.

### Apify — LinkedIn Job Search

Apify provides authenticated access to LinkedIn job listings via proxy-backed actors. This unlocks `/find-jobs --apify` (Mode 5), which searches LinkedIn without browser automation and returns skills data, applicant insights, and recruiter details unavailable from public scraping.

**Setup:**
1. Create an account at [apify.com](https://apify.com) — free tier available
2. Copy your API token from your account settings
3. Add to `.env`: `APIFY_TOKEN=your_token_here`
4. The `.mcp.json` file already has the Apify MCP configured

**Note:** Using Apify to scrape LinkedIn may conflict with LinkedIn's terms of service. Mode 5 is provided as an opt-in for users who accept that risk.

---

## Optional: Automated Job Digests

You can set up GitHub Actions to run job searches and email you a digest. This is entirely optional — the toolkit works great without it.

The workflows in `.github/workflows/` run manually (Actions tab → Run workflow); add a `schedule:` block if you want them automated. They require these **GitHub Actions secrets** (repo Settings → Secrets and variables → Actions — not your local `.env`):
- `ANTHROPIC_API_KEY` — for scoring and document preparation
- `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` — for ingesting job URLs from email
- `RESEND_API_KEY`, `DIGEST_FROM_EMAIL`, `DIGEST_TO_EMAIL` — [Resend](https://resend.com) account for sending the digest (free tier: 100 emails/day)

> ⚠️ **The digest workflows commit your job-search data (pipeline files, coaching state) back to this repository.** If your copy of this repo is public, that data becomes public. The workflows refuse to run on public repos by default — make your copy private before enabling them.

---

## Privacy

Your data stays local by default. The toolkit writes everything to files in this repo directory, all gitignored:
- `config/` — your profile, resume, cover letter, and any integration credentials
- `coaching_state.md` — your coaching history
- `data/` — job listings, prepared documents, session notes

**What leaves your machine, and when:**

| Service | What is sent | When |
|---|---|---|
| Anthropic API | Your prompts, profile, resume, and job listings — to power Claude's responses | Always (this is how the toolkit works) |
| Indeed connector | Your search queries | If you enable it (Step 8) |
| Firecrawl | URLs of career pages you scan | Only if you add a `FIRECRAWL_API_KEY` |
| Apify | LinkedIn search queries + your LinkedIn session cookies | Only if you run `/find-jobs --apify` |
| Resend | Your scored job list, emailed to you | Only if you enable the digest workflow |
| Gmail (IMAP) | Read access to your inbox via app password | Only if you enable email ingestion |

Everything in the right two columns is opt-in. If you never add those keys, nothing beyond the Anthropic API is contacted. For how Anthropic handles API data, see [Anthropic's privacy policy](https://www.anthropic.com/privacy).

---

## Troubleshooting

**"Your profile hasn't been set up yet"** → Run `/setup` first.

**"I found [N] claim(s) I can't verify"** → This is the anti-fabrication check. Review each flagged claim and either confirm it's accurate or ask Claude to remove it.

**Hook warning about profile.yaml** → Run `/setup` to check and repair your profile. This usually happens if a file write was interrupted.

**Context getting long** → Run `/compact` then `/clear`. Your progress is preserved.

**Python command not found** → Make sure Python is installed and added to PATH. On macOS/Linux, try `python3` instead of `python`.

**`/find-jobs` returns no results** → Check that the Indeed connector is enabled (see Step 8 in the setup section above). If it is, try running with specific company names: `/find-jobs Stripe, Linear, Anthropic`.

**Anti-fabrication keeps flagging something that's true** → Confirm it by typing "confirm" when prompted. The validator errs on the side of caution — you're the final check.

**Profile version warning** → Your profile was created with an older version of the toolkit. Run `/reset` (your resume and cover letter are preserved) and then `/setup` to rebuild it in the current format.

---

## FAQ

**Do I need to know how to code?**
No. Everything happens through conversation in Claude Code. The Python files run automatically in the background — you never need to open or edit them.

**Is my data private?**
Your profile, resume, cover letters, and job search history all stay on your computer by default. The Anthropic API powers Claude's responses; optional integrations (Indeed, Firecrawl, Apify, Resend, Gmail) each send specific data only if you enable them — see the Privacy section above for exactly what goes where. For Anthropic's data handling and retention, see [Anthropic's privacy policy](https://www.anthropic.com/privacy).

**How much does it cost?**
It depends on your Claude plan. On a Claude subscription (Pro/Max), skill sessions count against your plan's usage like any other Claude Code conversation — no separate bill. On API-key billing, costs scale with session length; scoring a job or tailoring documents are typically cents rather than dollars per run, with coaching sessions varying by length.

**Can I use it for multiple job searches over time?**
Yes. Your profile and storybank persist across sessions. Use `/compact` at the end of each session to save a handoff note, then `/clear` to clear context and start fresh. Run `/reset` only if you want to wipe everything and start over.

**What if I want to apply to a job that /score-job rates poorly?**
You can still run `/tailor-docs` on any listing in your pipeline. The threshold is a recommendation, not a lock.
