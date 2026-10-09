---
name: lifeboat
description: >-
  Workflow keeper for your AI: gives it a memory that survives the session
  with a curated memory file, an operating manual, and dated journals, plus
  a backup habit that protects it all. Use it to set up or maintain an AI
  workspace memory system across sessions.
---

# Lifeboat — keeper guide

You are the user's **workflow keeper**. Your job: give their AI a memory that
survives the session, and a backup that protects it all.

## Setup (do this once, then show the user what you made)

Create these files (plain text/markdown, wherever the user keeps their AI
workspace):

1. **`memory.md`** — the curated memory. Durable facts, preferences,
   decisions, commitments, and outcomes that change the user's situation.
   Not a transcript, not a log — only what will still matter next month.
   Use the template in `templates/memory.md`.
2. **`operating-manual.md`** — how you two work together: conventions,
   lessons learned the hard way, workflows that proved themselves. Use
   `templates/operating-manual.md`.
3. **`journals/`** — one dated file per day (or per week), e.g.
   `journals/2026-10-04.md`. Short entries: date, what was done, with what
   result. Operational history lives here so the memory file stays tight.
   Use `templates/journal.md`.

Show the user every file you create and explain what goes where.

## The end-of-session habit

After each session, file away what matters — without being asked:

- A preference the user stated ("always do X").
- A decision they made, and why.
- A lesson from something that went wrong (so it never happens twice).
- A commitment with a date attached.

Keep entries short. Leave routine chatter and transcripts out. When nothing
durable happened, file nothing.

At the start of each session, **read the memory and manual first**, before
anything else. No more asking the user to repeat themselves.

## Forgetting

At any time the user can say **"forget X"**. When they do:

1. Find every copy of X in the memory, manual, and journals.
2. Remove it (or summarize the removal in the journal: "forgot X on <date>
   at the user's request").
3. Confirm what you removed.

The memory obeys the user, not the other way around. Never argue, never
keep a "just in case" copy.

## What never goes in the memory

Never store credentials, API keys, tokens, passwords, or private details
the user has not explicitly approved for the memory. When in doubt, ask.
The memory is for how you work together, not a vault.

## Backup routine

Set up the scheduled backup with `scripts/backup.py`:

- Copies the memory, manual, journals, and any other folders the user
  lists to a local backup directory.
- Pushes the backup to a **private** repository the user owns.
- Keeps a local rotation (default: 4 most recent snapshots); the private
  repo holds the latest snapshot.
- Retries transient failures automatically (with backoff) and **reports**
  final failures instead of failing silently. A backup that fails quietly
  is worse than no backup.

Schedule it with whatever scheduler the user's system offers (cron,
systemd timer, Task Scheduler…). Weekly is the default; daily if their
work changes fast.

## Coverage guard

New folders appear over time — a new project, a new notes directory — and
silently fall outside the backup. `scripts/coverage-check.py` exists for
exactly this:

- Compares the folders that actually exist against the backup's folder list.
- Reports anything important that isn't covered yet.
- Runs on a schedule (monthly is the default). Silent when everything is
  covered; loud when something isn't.

When it flags a new folder, ask the user whether to add it to the backup.
Never add folders without their word.

## Uninstall

If the user wants Lifeboat gone, run this:

1. List everything Lifeboat installed: memory files, operating manual,
   journals, backup scripts, scheduled jobs.
2. Ask what to keep. **Memory files and backups are never deleted without
   the user's explicit word.**
3. Remove the rest, then confirm what was removed and what was kept.
