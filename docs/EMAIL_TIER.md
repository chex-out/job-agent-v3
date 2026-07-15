# Email Mode — the toolkit without Claude Code

Run the job agent for someone who has no Claude subscription, no Claude Code, and no interest in either. After a one-time setup, they interact **entirely by email**:

1. They email job links they've spotted → the agent rates each one against their profile and preferences and emails back a scored digest
2. They reply `PREPARE 2 5` → a tailored resume + cover letter (anti-fabrication validated) arrive as attachments

There's no hosted service, no server, and nobody's data leaves their own private GitHub repo except through the integrations listed below. GitHub Actions is the engine; email is the interface.

> Interview coaching, practice drills, and content writing are conversational by nature and are **not** part of email mode. Anyone who wants those can run the full toolkit in Claude Code — which is free software and works with just an API key (see the README).

---

## How it works

```
friend's inbox                    private GitHub repo                 friend's inbox
──────────────                    ───────────────────                 ──────────────
"JOB: <links>"  ──► agent Gmail ──► job_digest.yml:                ┌► scored digest
                                    ingest → score → digest  ──────┘   [1] [2] [3]...
"PREPARE 2"     ──► agent Gmail ──► prepare_selected.yml:          ┌► resume.md
                                    parse reply → tailor →   ──────┘   cover_letter.md
                                    validate → email docs              notes.md
```

Two workflows, both manual by default (run from the Actions tab) — add a `schedule:` block to automate (e.g. `cron: '0 */6 * * *'` for every 6 hours; reply latency = the schedule interval).

---

## Setup (operator does this once per person, ~15 minutes)

**Choose an ownership model first:**

| | Operator-owned (family) | Self-owned (friends) |
|---|---|---|
| GitHub repo | Yours, private | Theirs, private |
| API key + billing | Yours — you pay their usage | Theirs (console.anthropic.com, card required) |
| Who sees their data | You can (say so openly) | Only them |
| Their setup effort | Zero — email only | One guided session |

**Steps** (identical either way — "you" = whoever owns the repo):

1. **Create the repo**: use this repository as a template (GitHub → Use this template → **Private**). Name it e.g. `job-agent-mum`. The workflows refuse to run on public repos — this protects their career data.
2. **Create a dedicated agent Gmail** for this person (e.g. `mum.jobagent@gmail.com`). Enable 2FA, then create an **App Password** (myaccount.google.com/apppasswords). One mailbox per person — the pipeline marks messages as read, so sharing an inbox across repos breaks.
3. **Get a Resend account** ([resend.com](https://resend.com), free tier 100 emails/day) — one account can serve all your repos.
4. **Add repository secrets** (repo Settings → Secrets and variables → Actions):

   | Secret | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | The owner's API key (console.anthropic.com) |
   | `GMAIL_ADDRESS` | The agent Gmail address |
   | `GMAIL_APP_PASSWORD` | Its app password |
   | `AUTHORIZED_SENDER` | **The friend's personal email** — the only address allowed to send commands |
   | `RESEND_API_KEY` | From Resend |
   | `DIGEST_FROM_EMAIL` | A sender on your verified Resend domain (or `onboarding@resend.dev` to test) |
   | `DIGEST_TO_EMAIL` | The friend's personal email |
   | `FIRECRAWL_API_KEY` | *(optional)* enables JS-heavy career-page links (Ashby/Lever/Workday) |

5. **Create their profile**: Actions tab → **Profile Setup (email tier)** → Run workflow. Paste their resume text, target roles, location, and a sentence or two about what they want / deal-breakers. (Re-run any time their resume or preferences change.)
6. **Enable schedules** (optional): edit both workflow files and add a `schedule:` block, or leave them manual and trigger runs yourself.
7. **Test it**: send a `JOB:` email from the friend's address with one real listing link → run **Job Digest** → confirm the digest arrives → reply `PREPARE 1` → run **Prepare Selected Documents** → confirm the attachments arrive.

---

## The friend's guide (copy-paste this to them)

> **Your job-search agent**
>
> - **Found a job you like?** Email the link(s) to `<agent address>` with the subject **JOB:** — you'll get back a scored report on how well each one fits you, with honest strengths and gaps.
> - **Want application documents?** Reply to the report with **PREPARE** and the listing numbers (e.g. `PREPARE 2 5`). A tailored resume and cover letter arrive by email. **Read the attached notes file before submitting** — it lists what to double-check.
> - **Keep it posted**: reply `applied <company>`, `rejected <company>`, `offer <company>` and it tracks your pipeline.
> - Replies are processed on a schedule, so responses can take a few hours.
> - Everything is checked against your real resume — it will never invent experience you don't have.

---

## Security & privacy — read before offering this to someone

- **Only their address is obeyed.** Commands are accepted solely from `AUTHORIZED_SENDER`. Residual risk: email From-addresses can be spoofed by a determined sender who also knows the agent address. Worst case is unwanted API spend and unwanted emails to the friend — not data exposure. Keep the agent address private.
- **The repo owner can read everything.** In the operator-owned model, you can see their resume, scores, and application history. Tell them this before you set it up.
- **Career data is committed to the private repo** — that's the state store. The workflows hard-refuse to run on public repos.
- **Gmail app password = full-mailbox access** for that agent account. That's why each person gets a dedicated agent mailbox, not a shared or personal one.
- **API costs** land on whoever's key is in the secrets. Scoring a digest of ~5 listings or preparing one document each cost cents; there's no cap built in, so keep schedules modest.
