# Lifeboat

Give your AI a memory that survives the session, and a backup that protects it all.

AI assistants forget everything when the chat ends, and their files can vanish
with one wrong click. Lifeboat is a build you install once: your AI maintains
its own memory in plain files, backs them up on a schedule, and runs a guard
that makes sure nothing slips through the cracks.

## What's inside

- **`SKILL.md`** — the keeper master prompt. Paste it into your AI's
  instructions and it sets everything up: the memory files, the filing
  habit, the backup routine, the coverage guard.
- **`templates/`** — blank templates for the memory file, the operating
  manual, and the dated journals.
- **`scripts/backup.py`** — scheduled backup (local copy with rotation —
  4 most recent snapshots — plus your own private repo holding the latest
  snapshot). Retries transient failures automatically and
  reports final failures instead of failing silently. Secrets are never
  backed up.
- **`scripts/coverage-check.py`** — the anti-gap guard. Compares your real
  folders against the backup list and reports anything new that isn't
  covered yet.
- **`examples/`** — a small filled example so you can see the shape of it
  before you start.

## Quick start

1. Paste the keeper guide (`SKILL.md`) into your AI's instructions.
2. It creates your memory files from the templates and shows them to you.
3. Edit `scripts/backup.py` (the `FOLDERS` list at the top), then schedule
   it weekly. Edit `scripts/coverage-check.py` the same way, schedule it
   monthly.
4. Done. After each session your AI files away what matters; the backup
   and the guard run on their own.

## The "forget X" rule

At any time, tell your AI **"forget X"** and it removes that fact from the
memory files and confirms. Your memory obeys you, not the other way around.

## Uninstall

Ask your AI to uninstall Lifeboat: it lists everything it installed, asks
what to keep (memory files and backups are never deleted without your
explicit word), removes the rest, and confirms.

## Privacy

Everything is plain text you can read. Nothing is uploaded anywhere except
your own private repo. The templates contain zero personal information, and
the guide tells your AI to keep secrets and credentials out of the memory.

## License

MIT — do what you want with it, no warranty.
