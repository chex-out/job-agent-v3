# /queue-digest — Show Pipeline Status

Display a concise summary of your current job search pipeline. Shows what's scored, prepared, applied, and in progress.

---

## Prerequisite Check

Check that `data/processed_listings.yaml` exists. If not or if empty: "Your pipeline is empty. Run `/find-jobs` to search for roles or `/score-job [URL]` to score a listing."

---

## Reading the Pipeline

Read `data/processed_listings.yaml`. Group listings by status:

| Status | Meaning |
|--------|---------|
| `scored` | Scored but not yet prepared or applied |
| `prepared` | Documents tailored, not yet applied |
| `applied` | Application submitted |
| `interviewing` | Active interview process |
| `offer` | Offer received |
| `skipped` | Deliberately skipped |
| `rejected` | Rejected |
| `under_review` | Application under review |
| `error` | Scoring or prep failed |

Also read `coaching_state.md` Interview Loops section to cross-reference active loops.

---

## Output Format

```
## Your Job Search Pipeline

### Active (needs action)
| Company | Role | Skills | Pref | Status | Next Step |
|---------|------|--------|------|--------|-----------|
| [name] | [role] | [X]/10 | [Y]/10 | Scored | /tailor-docs |
| [name] | [role] | [X]/10 | [Y]/10 | Prepared | Submit application |

### In Progress
| Company | Role | Status | Last Updated |
|---------|------|--------|-------------|
| [name] | [role] | Interviewing | [date] |

### Closed
| Company | Role | Outcome |
|---------|------|---------|
| [name] | [role] | Rejected |
| [name] | [role] | Skipped |

### Summary
- Total listings scored: [N]
- Prepared (docs ready): [N]
- Applied: [N]
- Active interviews: [N]
- Offers: [N]
```

For listings in "Scored" status that are above `scoring.threshold_for_preparation` in `profile.yaml`, show "→ Ready for /tailor-docs" in the Next Step column.

If the pipeline is empty in a section, omit that section header.

---

## Closing

After the digest, suggest the next action:
- If there are scored listings above threshold with no docs: `→ Run /tailor-docs to prepare documents for [company].`
- If there are prepared listings not yet applied: `→ Documents are ready for [company] — apply when you're ready, then run /track-application to update your status.`
- If pipeline looks thin: `→ Run /find-jobs to find new roles.`
- If there are active interviews: `→ Run /coach-prep [company] to prepare for your interview.`
