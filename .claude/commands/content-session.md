# /content-session — Start a Content Creation Session

Initialize a focused content creation session. Drafts, edits, and manages your content pipeline across all platforms — LinkedIn, Substack, blog, newsletter, X/Twitter, or any combination — using your personal voice guide and storybank as source material.

Run this whenever you want to write, edit, plan, or review content for any platform. Your voice guide and content history persist across sessions — you never explain your style twice.

---

## State Files

This skill reads and writes to two personal files:

- `config/content_voice.md` — your personal voice guide (rules, style, banned phrases, audience, platform-specific notes)
- `data/content_pipeline.md` — content history, pipeline, ideas queue, performance data, saved lines — all platforms in one place

Both are gitignored (personal data, not part of the shared repo).

---

## On Open — Read State Silently

Before saying anything, check the following:

**1. Check profile:**
Read `config/profile.yaml`. If missing: "Run `/setup` first."

**2. Check voice guide:**
Read `config/content_voice.md`. Note whether it exists and is populated, and which platforms are listed.

**3. Check content pipeline:**
Read `data/content_pipeline.md`. Extract:
- Count of published pieces (total + per platform if multiple)
- Last published piece (title/excerpt + platform + date)
- Count of pieces in pipeline (draft or planned) per platform
- Ideas queue entries
- Any saved lines earmarked for specific pieces

**4. Check storybank:**
Read `coaching_state.md`. Check if `### Career Highlights` and `### Superpower` are populated.
If populated: flag as available content source — specific real moments are always preferred over manufactured examples.

---

## First Run — Setup

If `config/content_voice.md` does not exist or is empty, run the full setup before anything else.

### Step 1 — Platforms

Say:
> "Before we start, two quick setup questions — this saves permanently so you never have to explain it again.
>
> **First: which platforms are you publishing on?**
> Common ones: LinkedIn, Substack, personal blog, newsletter, X/Twitter, Medium. List yours — even if you're not active on them yet but planning to be."

Save the platform list to `config/content_voice.md` under `## Active Platforms`.

### Step 2 — Voice Guide

Say:
> "Now your writing voice — three questions:
>
> 1. Who are you writing for? Describe your target reader in one sentence.
> 2. Paste 1-2 examples of writing that sounds like you at your best — a post, an email, anything. (If nothing yet, describe how you want to sound.)
> 3. Any absolute rules? Things you'd never write, phrases that feel wrong, formats you hate?"

After the user answers:

- Analyse the writing examples for: sentence rhythm, paragraph structure, how they use hedging language, how they handle uncertainty, how conclusions land, what they never do
- Extract voice characteristics and hard rules
- Draft the voice guide and show it to the user: "Here's your voice guide — does this capture it? Anything to add or correct?"
- Refine until confirmed

### Step 3 — Platform-Specific Notes

For each active platform, prompt:
> "Any platform-specific constraints I should know for [platform]? For example: topics you avoid there, a different audience than your general one, or formatting preferences."

Skip platforms where the user has no special notes — defaults apply (see Platform Guidance below).

Save the complete voice guide to `config/content_voice.md`.

Confirm: `✓ Voice guide saved to config/content_voice.md`

Then continue to the opening output.

---

## Opening Output

**Show the content status header:**

```
## Content Session — [name from profile.yaml]

Voice guide: [loaded ✓ | not yet set up]
Platforms: [list of active platforms from voice guide]

[If single platform:]
Content: [N] published | [N] in pipeline | [N] ideas queued

[If multiple platforms:]
LinkedIn: [N] published | [N] drafts
Substack: [N] published | [N] drafts
[Other platform]: [N] published | [N] drafts
Ideas queued: [N]

[If any published content:]
Last published: [excerpt of first sentence] — [platform] — [date]

[If storybank is populated:]
Storybank: [N] career highlights available as source material ✓
```

If no content published yet: "No content published yet — let's start your first piece."
If no ideas queued and no pipeline: "Nothing in the queue. Let's find something to write about."

---

## Scope Statement

After the header, say:

> "This is your content session. I have your voice guide loaded and will stay in character throughout.
>
> What would you like to do?
> - **Draft** a new piece (from your ideas queue, or a fresh idea)
> - **Edit** a draft that's in progress
> - **Add** something to your ideas queue
> - **Review** what's coming up in the pipeline
> - **Repurpose** an existing piece for a different platform"

---

## Voice Guide — How to Apply It

When writing or editing any piece, always:

1. Load the full `config/content_voice.md` before generating any draft
2. Apply every rule in the voice guide — hard rules are non-negotiable
3. Apply platform-specific structural guidance (see Platform Guidance below) on top of the voice rules
4. When a storybank moment is relevant (Career Highlights, Key Skills with Evidence, Superpower), use the specific real detail instead of a generic example — specificity is what separates authentic posts from AI-generated ones
5. Before showing any draft, do a self-check against hard rules — if any rule is violated, fix it silently before presenting

---

## Drafting a Piece

When drafting, ask first:
> "What's the piece about, and which platform is it for? Give me the seed — a sentence, a moment, an observation, or just point me to an idea in your queue."

Then:
1. Confirm the platform if not specified — it determines the structural guidance applied
2. Check the storybank for relevant career moments that could ground the piece
3. Check the ideas queue in `data/content_pipeline.md` for related notes or saved lines
4. Draft using the voice guide + platform guidance (see below)
5. Show the draft and invite feedback: "How does this feel? Does it sound like you?"
6. Iterate until confirmed

When confirmed, save to `data/content_pipeline.md` under `## In Pipeline` with status: draft and platform noted.

Confirm: `✓ Draft saved to data/content_pipeline.md`

---

## Platform Guidance

Apply these structural rules on top of the voice guide. Platform rules govern structure and format; voice guide rules govern language and tone. Both apply simultaneously.

### LinkedIn
- **Opening:** Establish a tension, contradiction, or personal moment — never a claim or conclusion first
- **Middle:** Show thinking evolving — not a finished argument delivered from a position of authority
- **Ending:** Land quietly on an honest observation — no calls to action, no "what do you think?", no engagement bait
- **Length:** 150–800 words. Shorter is almost always better.
- **Format:** Short paragraphs (1-3 sentences). No bullet lists in most posts — use them only when genuinely enumerating distinct items.
- **Avoid:** Hashtag spam (0-2 max), "I'm thrilled to announce", open-ended questions to drive comments, performative humility

### Substack / Newsletter
- **Subject line:** Write this first — it's the most important line. Should create curiosity or signal value without clickbait.
- **Preview text:** Second line the reader sees in their inbox — complements, doesn't repeat, the subject.
- **Opening:** Hook the reader in the first paragraph — a question, a surprising fact, or a personal moment that grounds the piece
- **Structure:** Headers are expected and helpful for longer pieces. Each section should earn its place.
- **Length:** 400–2000 words depending on depth of topic. Don't pad; don't truncate if the piece needs room.
- **CTA:** One, at the end — natural, not desperate. "Reply if this resonated" or "share with someone who'd find this useful" are fine.
- **Tone:** More personal and direct than a blog post — you're writing a letter to a reader you know.

### Blog / Medium
- **Headline:** Should communicate the specific value of the piece. Avoid vague titles.
- **Intro:** First paragraph should immediately answer "why should I read this?" — state the problem or insight upfront.
- **Structure:** Use headers. Readers scan. Each header should be substantive, not just a label.
- **Length:** Match depth to topic — 600 to 2500 words is a wide but reasonable range.
- **Conclusion:** Summarise the core insight; optionally point to related work or next steps.
- **SEO awareness:** If SEO matters for this piece, note the target keyword and make sure it appears naturally in the headline and first paragraph.

### X / Twitter
- **Hook tweet:** The first tweet in a thread is the entire game — if it doesn't earn the click, nothing else matters.
- **Thread structure:** Each tweet should be a self-contained thought that also advances the larger argument. Don't split one sentence across two tweets.
- **Single tweet:** If it fits in one, don't thread. Forced threads are obvious.
- **Length:** 280 chars per tweet. Shorter usually performs better.
- **Ending:** Either a conclusion tweet or a call to read the full piece (if repurposing from another platform).

### Cross-Platform Repurposing
When adapting a piece from one platform to another:
1. Don't copy-paste — restructure for the platform's format and reader expectation
2. LinkedIn ↔ newsletter: The insight is the same; the framing, length, and ending differ significantly
3. Long-form → LinkedIn: Extract one core tension or moment, not the whole argument
4. LinkedIn → long-form: Use the post as the opener or hook; develop the argument further
5. Always tell the reader if you've published a longer version elsewhere — don't hide cross-posting

---

## Editing a Draft

Load the full draft from `data/content_pipeline.md`. Read it against the voice guide and the platform guidance, then note:
- Any hard rule violations (flag immediately — never silently keep)
- Any structural issues specific to the platform (wrong opening for LinkedIn, no subject line for newsletter, etc.)
- Any places where a storybank moment could replace a vague reference
- Any place where the ending resolves too neatly or asks for something from the reader it hasn't earned

Present observations as editorial notes, then ask: "Want me to take a pass at these, or walk through them together?"

---

## Marking a Piece as Published

When the user says a piece is live, update `data/content_pipeline.md`:
- Move from `## In Pipeline` → `## Published`
- Add the platform, date, and any performance data if provided

If performance data is given, note any patterns against existing benchmarks in the file.

Confirm: `✓ Marked as published in data/content_pipeline.md`

---

## Ideas Queue

When the user wants to add something to the queue, collect:
- The core observation or moment
- The intended platform (or "undecided")
- Any angle or tension they're already thinking about
- Any saved lines they want to earmark (log these in `## Saved Lines` with the piece they're intended for)

Save to `## Ideas Queue` in `data/content_pipeline.md`.

Confirm: `✓ Added to ideas queue`

---

## File Schemas

### `config/content_voice.md`
```markdown
# Content Voice Guide — [Name]
Last updated: [date]

## Active Platforms
[List of platforms: LinkedIn, Substack, Blog, Newsletter, X/Twitter, etc.]

## Audience
[Who I'm writing for — one sentence that applies across platforms]

## Voice characteristics
- [Characteristic 1]
- [Characteristic 2]

## Hard rules — never do these
- [Rule 1]
- [Rule 2]

## Core writing structure
**Opening:** [how to open — applies across platforms unless overridden below]
**Middle:** [how to develop]
**Ending:** [how to close]

## Spelling and mechanics
[British/American English, punctuation preferences]

## Privacy constraints
[What not to discuss publicly]

## Platform-specific notes
### LinkedIn
[Any overrides or additions to defaults]

### Substack
[Any overrides or additions to defaults]

### [Other platform]
[Any overrides or additions to defaults]

## Performance benchmarks
[Baseline data once enough content exists — per platform]
```

### `data/content_pipeline.md`
```markdown
# Content Pipeline — [Name]

## Published

### [Title or First Line] — [Platform] — [Date]
[Full text or excerpt]
*Performance: [N] reactions / impressions / opens / clicks — whatever is relevant to this platform*

---

## In Pipeline

### [Title or working description]
Platform: [LinkedIn | Substack | Blog | Newsletter | X | Other]
Status: draft | planned
[Draft text or outline]

---

## Ideas Queue

- [Idea] — [Platform] — [angle or tension]

---

## Saved Lines

- "[Exact line]" — earmarked for [post title or description]
```

---

## Closing

End sessions with:
> "✓ Everything saved. Your pipeline and voice guide are up to date.
>
> When this session gets long, run `/compact` before clearing with `/clear`."
