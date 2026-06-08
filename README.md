# Job Seeker AI Toolkit

An AI-powered job search assistant that runs entirely inside Claude Code. No coding required — you interact through conversation.

**What it does:**
- Searches for jobs matching your profile
- Scores listings against your skills and preferences
- Generates tailored resumes and cover letters (with fabrication checking)
- Coaches you through interview prep and practice
- Tracks your entire job search pipeline

**What makes it different:** Every output is anchored to your specific profile, career highlights, and positioning. Generic AI tools produce generic outputs. This produces outputs that sound like you.

---

## Prerequisites

Before you start, you need:

1. **Python 3.11 or higher**
2. **Claude Code** (the CLI tool)
3. **An Anthropic API key**
4. **Your resume text** — have it ready to paste during setup (plain text or Markdown is fine)
5. **A cover letter draft** — a rough starting point to tailor from; doesn't need to be polished

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

### Step 8 — Enable Job Search (Indeed MCP)

In the Claude Code terminal, run:

```
claude mcp add @anthropic-ai/mcp-server-indeed
```

Then restart Claude Code (`exit`, then run `claude` again). This enables `/find-jobs` to search Indeed automatically.

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

### Step 8 — Enable Job Search (Indeed MCP)

```bash
claude mcp add @anthropic-ai/mcp-server-indeed
```

Then restart Claude Code (`exit`, then run `claude` again). This enables `/find-jobs` to search Indeed automatically.

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

### Step 8 — Enable Job Search (Indeed MCP)

```bash
claude mcp add @anthropic-ai/mcp-server-indeed
```

Then restart Claude Code (`exit`, then run `claude` again). This enables `/find-jobs` to search Indeed automatically.

If you skip this step, `/find-jobs` will only search company career pages for companies you name manually — no automated Indeed results.

---

## Skills Reference

Once set up, everything happens through conversation in Claude Code.

### Getting Started
| Command | What it does |
|---|---|
| `/setup` | First-time profile creation (run once) |
| `/build-storybank` | Build your career story database (unlocks LinkedIn optimizer) |
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
3. Press `Ctrl+L` to clear context
4. Next session, start fresh with `/job-search-session` or `/coaching-session` — they'll recap where you left off automatically

All your job search data lives in files, not in the conversation. Clearing context only loses the chat thread.

---

## Setting Up Job Search (Indeed MCP)

`/find-jobs` uses the **Indeed MCP** as its primary job source. To enable it, add the Indeed MCP to your Claude Code configuration:

1. In the Claude Code terminal, run:
   ```
   claude mcp add @anthropic-ai/mcp-server-indeed
   ```

2. Restart Claude Code for the change to take effect.

If the Indeed MCP is not configured, `/find-jobs` will skip Mode 1 and fall back to career page searches (Mode 2) and any companies you specify manually. All other skills work without it.

---

## Optional: Enhanced Job Search Integrations

These integrations extend the search stack beyond the default Indeed MCP + trafilatura. All are opt-in — the toolkit works without them.

### Firecrawl — Better Career Page Scraping

By default, `/find-jobs` Mode 2 (career pages) uses trafilatura to fetch page content. Trafilatura works for static pages but fails on modern JavaScript-rendered career sites (Ashby, Lever, Greenhouse, Workday). Firecrawl handles JS rendering and returns clean structured data.

**Setup:**
1. Create an account at [firecrawl.dev](https://www.firecrawl.dev) — free tier includes 500 pages/month
2. Copy your API key
3. Add to `.env`: `FIRECRAWL_API_KEY=your_key_here`
4. The `.mcp.json` file in the repo already has the Firecrawl MCP configured — Claude Code will load it automatically

Once configured, Mode 2 will automatically use Firecrawl for career pages and fall back to trafilatura for any pages it can't handle.

### Apify — LinkedIn and Glassdoor Job Search

Apify provides access to job listings from LinkedIn and Glassdoor via proxy-backed actors. This unlocks `/find-jobs --apify` (Mode 5), which searches those platforms without browser automation.

**Setup:**
1. Create an account at [apify.com](https://apify.com) — free tier available
2. Copy your API token from your account settings
3. Add to `.env`: `APIFY_TOKEN=your_token_here`
4. The `.mcp.json` file already has the Apify MCP configured

**Note:** Using Apify to scrape LinkedIn may conflict with LinkedIn's terms of service. Mode 5 is provided as an opt-in for users who accept that risk.

---

## Optional: Automated Job Digests

You can set up GitHub Actions to run daily job searches and email you a digest. This is entirely optional — the toolkit works great without it.

See `.github/workflows/job_digest.yml` for setup instructions. Requires:
- A [Resend](https://resend.com) account (free tier: 100 emails/day)
- `RESEND_API_KEY`, `DIGEST_FROM_EMAIL`, and `DIGEST_TO_EMAIL` in your `.env`

---

## Privacy

Your data stays local. The toolkit writes everything to files in this repo directory:
- `config/profile.yaml` — your profile (gitignored)
- `coaching_state.md` — your coaching history (gitignored)
- `data/` — job listings and prepared documents (gitignored)

Nothing is sent anywhere except to the Anthropic API to power Claude's responses.

---

## Troubleshooting

**"Your profile hasn't been set up yet"** → Run `/setup` first.

**"I found [N] claim(s) I can't verify"** → This is the anti-fabrication check. Review each flagged claim and either confirm it's accurate or ask Claude to remove it.

**Hook warning about profile.yaml** → Run `/setup` to check and repair your profile. This usually happens if a file write was interrupted.

**Context getting long** → Run `/compact` then `Ctrl+L`. Your progress is preserved.

**Python command not found** → Make sure Python is installed and added to PATH. On macOS/Linux, try `python3` instead of `python`.

**`/find-jobs` returns no results** → Check that the Indeed MCP is configured (see "Setting Up Job Search" above). If it is, try running with specific company names: `/find-jobs Stripe, Linear, Anthropic`.

**Anti-fabrication keeps flagging something that's true** → Confirm it by typing "confirm" when prompted. The validator errs on the side of caution — you're the final check.

**`/setup --migrate` prompt** → Your profile was created with an older version of the toolkit. Run `/setup --migrate` to update it, or `/reset` and `/setup` to start fresh.

---

## FAQ

**Do I need to know how to code?**
No. Everything happens through conversation in Claude Code. The Python files run automatically in the background — you never need to open or edit them.

**Is my data private?**
Yes. Your profile, resume, cover letters, and job search history all stay on your computer. The only external service used is the Anthropic API (to power Claude's responses). Nothing is stored on Anthropic's servers long-term — see [Anthropic's privacy policy](https://www.anthropic.com/privacy).

**How much does it cost?**
You pay for Anthropic API usage. A typical `/setup` session costs about $0.10–0.20. A `/tailor-docs` run with anti-fabrication validation costs about $0.20–0.40. Coaching sessions vary with length.

**Can I use it for multiple job searches over time?**
Yes. Your profile and storybank persist across sessions. Use `/compact` at the end of each session to save a handoff note, then `Ctrl+L` to clear context and start fresh. Run `/reset` only if you want to wipe everything and start over.

**What if I want to apply to a job that /score-job rates poorly?**
You can still run `/tailor-docs` on any listing in your pipeline. The threshold is a recommendation, not a lock.
