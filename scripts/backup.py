#!/usr/bin/env python3
"""Lifeboat backup script — generic version.

Copies the folders listed in FOLDERS to a local backup directory, then
pushes the backup to a private git repository. Keeps a local rotation of
the most recent snapshots; the private repo always holds the latest
snapshot.

Usage:
    python3 scripts/backup.py            # full backup (local + repo)
    python3 scripts/backup.py --dry-run  # show what would be copied

Configuration is at the top of this file — edit it before the first run.

Design rules (do not remove):
- Transient failures are retried automatically with backoff.
- A final failure is REPORTED (non-zero exit + clear message), never
  silent. A backup that fails quietly is worse than no backup.
- Secrets are never backed up: filenames matching SECRET_PATTERNS are
  skipped, and the script refuses to run if FOLDERS contains a known
  secrets location.
"""

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

# ---------------------------------------------------------------- config
# Folders to back up (absolute paths). The user approves this list.
FOLDERS = [
    # os.path.expanduser("~/ai-memory"),
]

# Where local snapshots go. Each run creates backup-YYYY-MM-DD-HHMM/.
LOCAL_BACKUP_ROOT = os.path.expanduser("~/lifeboat-backups")

# Private repo for off-site copies (the user owns it). Empty string =
# local-only mode (no push).
GIT_REPO = ""          # e.g. "git@github.com:you/lifeboat-backups.git"
GIT_BRANCH = "main"

# Rotation (local snapshots): keep this many most recent snapshots.
# The private repo always holds the latest snapshot (force-pushed mirror).
KEEP_SNAPSHOTS = 4

# Retry policy for transient failures (network, API).
MAX_ATTEMPTS = 4
BACKOFF_BASE_SECONDS = 5

# Files that are never backed up, even if a folder contains them.
SECRET_PATTERNS = (
    ".env", ".pem", ".key", "id_rsa", "id_ed25519",
    "credentials.json", "secrets.json", ".netrc",
)

# Folder names that are always secrets locations — the script refuses to
# back these up at all (see check_folders).
SECRET_DIR_NAMES = (".ssh", ".gnupg", ".aws")

DRY_RUN = "--dry-run" in sys.argv
# ----------------------------------------------------------------------


def log(msg):
    print(f"[lifeboat-backup] {msg}", flush=True)


def fail(msg):
    # Loud failure: non-zero exit AND a clear message. Never silent.
    print(f"[lifeboat-backup] FAILED: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def is_secret_path(path):
    name = os.path.basename(path).lower()
    return any(pat in name for pat in SECRET_PATTERNS)


def check_folders(folders):
    for f in folders:
        name = os.path.basename(os.path.normpath(f)).lower()
        if is_secret_path(f) or name in SECRET_DIR_NAMES:
            fail(f"refusing to back up a secrets location: {f}")
        if not os.path.isdir(f):
            fail(f"folder does not exist: {f}")


def copy_tree(src, dst):
    for root, dirs, files in os.walk(src):
        # Skip common junk and secret-looking dirs.
        dirs[:] = [d for d in dirs
                   if d not in (".git", "__pycache__", "node_modules", ".venv")]
        for name in files:
            spath = os.path.join(root, name)
            if is_secret_path(spath):
                log(f"  skip (secret pattern): {spath}")
                continue
            rel = os.path.relpath(spath, src)
            dpath = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(dpath), exist_ok=True)
            shutil.copy2(spath, dpath)


def run_with_retry(cmd, cwd=None):
    """Run cmd, retrying transient failures with backoff. Returns True on
    success; raises on final failure (loud, never silent)."""
    last_err = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            subprocess.run(cmd, cwd=cwd, check=True,
                           capture_output=True, text=True, timeout=300)
            return True
        except subprocess.CalledProcessError as e:
            last_err = (e.stderr or e.stdout or str(e)).strip()[:300]
        except (subprocess.TimeoutExpired, OSError) as e:
            last_err = str(e)[:300]
        if attempt < MAX_ATTEMPTS:
            wait = BACKOFF_BASE_SECONDS * attempt
            log(f"  attempt {attempt}/{MAX_ATTEMPTS} failed ({last_err}) — "
                f"retry in {wait}s")
            time.sleep(wait)
    fail(f"command failed after {MAX_ATTEMPTS} attempts: "
         f"{' '.join(cmd)} — last error: {last_err}")


def prune_local(root):
    snaps = sorted(d for d in os.listdir(root)
                   if d.startswith("backup-")
                   and os.path.isdir(os.path.join(root, d)))
    for old in snaps[:-KEEP_SNAPSHOTS]:
        log(f"  prune local: {old}")
        if not DRY_RUN:
            shutil.rmtree(os.path.join(root, old))


def git_push(snapshot_dir):
    if not GIT_REPO:
        log("no GIT_REPO configured — local-only mode, skipping push")
        return
    work = os.path.join(LOCAL_BACKUP_ROOT, ".push-work")
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    run_with_retry(["git", "init", "-b", GIT_BRANCH], cwd=work)
    run_with_retry(["git", "remote", "add", "origin", GIT_REPO], cwd=work)
    # Copy snapshot into the work tree.
    copy_tree(snapshot_dir, work)
    run_with_retry(["git", "add", "-A"], cwd=work)
    # Nothing to commit is fine (identical snapshot).
    r = subprocess.run(["git", "status", "--porcelain"], cwd=work,
                       capture_output=True, text=True)
    if not r.stdout.strip():
        log("  repo already up to date")
        return
    run_with_retry(
        ["git", "-c", "user.name=lifeboat", "-c", "user.email=lifeboat@local",
         "commit", "-m", f"lifeboat backup {os.path.basename(snapshot_dir)}"],
        cwd=work)
    run_with_retry(["git", "push", "-f", "origin", GIT_BRANCH], cwd=work)
    log("  pushed to remote")


def main():
    if not FOLDERS:
        fail("FOLDERS is empty — edit the config at the top of this file first")
    check_folders(FOLDERS)
    stamp = datetime.now().strftime("backup-%Y-%m-%d-%H%M")
    snapshot_dir = os.path.join(LOCAL_BACKUP_ROOT, stamp)

    log(f"starting backup -> {snapshot_dir}")
    if DRY_RUN:
        log("DRY RUN — nothing will be written")
    for folder in FOLDERS:
        dest = os.path.join(snapshot_dir, os.path.basename(folder.rstrip("/")))
        log(f"  copy {folder}")
        if not DRY_RUN:
            os.makedirs(dest, exist_ok=True)
            copy_tree(folder, dest)

    if not DRY_RUN:
        os.makedirs(LOCAL_BACKUP_ROOT, exist_ok=True)
        prune_local(LOCAL_BACKUP_ROOT)
        git_push(snapshot_dir)

    log("backup complete")


if __name__ == "__main__":
    main()
