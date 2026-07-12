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

1. **Python 3.11 or higher**
2. **Claude Code** (the CLI tool)
3. **An Anthropic API key**
4. **Your resume text** — have it ready to paste during setup (plain text or Markdown is fine)
5. **A cover letter draft** — a rough starting point to tailor from; doesn't need to be polished

---

## Try It in 2 Minutes (before committing to full setup)

You don't need the full setup to see what this does. The taster needs only Claude Code and the cloned repo — no Python install, no API key file:

1. Clone the repo and open it:
   ```
   git clone https://github.com/chex-out/job-agent-v3.git
   cd job-agent-v3
   claude
   ```
2. Type `/try-it`
3. Paste your resume and one job listing you're eyeing

You'll get a scored match report — strengths, honest gaps, a legitimacy check on the posting, and a sample tailored pitch. **Nothing is saved.** If you like what you see, the full setup below takes about 10 minutes and unlocks the job pipeline, tailored documents, and interview coaching.

---

## Setup: Windows

### Step 1 — Check Python

Open **Command Prompt** (search for `cmd` in the Start menu) and run:

```
python --version
```

You should see `Python 3.11.x` or higher. If you see an error or an older version, download Python from [python.org/downloads](https://www.python.org/downloads/) and install it. Make sure to check **"Add Python to PATH"** during installation.

### Step 2 — Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create an account
3. Click **API Keys** → **Create Key**
4. Copy your key — you'll need it in Step 5

### Step 3 — Install Claude Code

Open Command Prompt and run:

```
npm install -g @anthropic-ai/claude-code
```

If you see `npm not found`, you need Node.js first: [nodejs.org](https://nodejs.org) → download and install the LTS version, then retry.

### Step 4 — Clone and Set Up the Repo

In Command Prompt:

```
git clone https://github.com/chex-out/job-agent-v3.git
cd job-agent-v3
python -m pip install -e .
```

### Step 5 — Add Your API Key

```
copy .env.example .env
notepad .env
```

In Notepad, replace `your_api_key_here` with your actual API key. Save and close.

### Step 6 — Start Claude Code

```
claude
```

A browser window will open to authenticate. Follow the prompts.

### Step 7 — Run Setup

Once Claude Code is running in your terminal, type:

```
/setup
```

Follow the conversation — Claude will ask you questions and build your profile automatically. Takes about 10 minutes.

### Step 8 — Enable Job Search (Indeed Connector)

`/find-jobs` uses Claude's official Indeed connector as its primary job source:

1. Go to [claude.com/connectors/indeed](https://claude.com/connectors/indeed) in your browser
2. Click **Add connector** and sign in with the same Claude account you use for Claude Code
3. Restart Claude Code (`exit`, then run `claude` again)

If you skip this step, `/find-jobs` will only search company career pages for companies you name manually — no automated Indeed results.

---

## Setup: macOS

### Step 1 — Check Python

Open **Terminal** (Spotlight → `Terminal`) and run:

```bash
python3 --version
```

You should see `Python 3.11.x` or higher. If not, install Python via [python.org/downloads](https://www.python.org/downloads/) or with Homebrew:

```bash
brew install python@3.11
```

### Step 2 — Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create an account
3. Click **API Keys** → **Create Key**
4. Copy your key — you'll need it in Step 5

### Step 3 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

If `npm` is not found, install Node.js: [nodejs.org](https://nodejs.org) → download LTS, then retry.

### Step 4 — Clone and Set Up the Repo

```bash
git clone https://github.com/chex-out/job-agent-v3.git
cd job-agent-v3
pip3 install -e .
```

### Step 5 — Add Your API Key

```bash
cp .env.example .env
open -e .env
```

Replace `your_api_key_here` with your actual API key. Save and close.

### Step 6 — Start Claude Code

```bash
claude
```

A browser window will open to authenticate.

### Step 7 — Run Setup

```
/setup
```

Claude will walk you through profile creation. Takes about 10 minutes.

### Step 8 — Enable Job Search (Indeed Connector)

`/find-jobs` uses Claude's official Indeed connector as its primary job source:

1. Go to [claude.com/connectors/indeed](https://claude.com/connectors/indeed) in your browser
2. Click **Add connector** and sign in with the same Claude account you use for Claude Code
3. Restart Claude Code (`exit`, then run `claude` again)

If you skip this step, `/find-jobs` will only search company career pages for companies you name manually — no automated Indeed results.

---

## Setup: Linux

### Step 1 — Check Python

```bash
python3 --version
```

Should show `3.11.x` or higher. If not:

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3.11 python3-pip
```

**Fedora/RHEL:**
```bash
sudo dnf install python3.11
```

### Step 2 — Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create an account
3. Click **API Keys** → **Create Key**
4. Copy your key

### Step 3 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Install Node.js if needed: [nodejs.org](https://nodejs.org) or via your package manager (`apt install nodejs npm`).

### Step 4 — Clone and Set Up the Repo

```bash
git clone https://github.com/chex-out/job-agent-v3.git
cd job-agent-v3
pip3 install -e .
```

### Step 5 — Add Your API Key

```bash
cp .env.example .env
nano .env
```

Replace `your_api_key_here` with your actual key. Save with `Ctrl+O`, exit with `Ctrl+X`.

### Step 6 — Start Claude Code

```bash
claude
```

### Step 7 — Run Setup

```
/setup
```

### Step 8 — Enable Job Search (Indeed Connector)

`/find-jobs` uses Claude's official Indeed connector as its primary job source:

1. Go to [claude.com/connectors/indeed](https://claude.com/connectors/indeed) in your browser
2. Click **Add connector** and sign in with the same Claude account you use for Claude Code
3. Restart Claude Code (`exit`, then run `claude` again)

If you skip this step, `/find-jobs` will only search company career pages for companies you name manually — no automated Indeed results.

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

**`/find-jobs` returns no results** → Check that the Indeed connector is enabled (see Step 8 in your OS setup section above). If it is, try running with specific company names: `/find-jobs Stripe, Linear, Anthropic`.

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
