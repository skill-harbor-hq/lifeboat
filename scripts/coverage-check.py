#!/usr/bin/env python3
"""Lifeboat coverage guard — generic version.

New folders appear over time (a new project, a new notes directory) and
silently fall outside the backup. This script compares the folders that
actually exist against the backup's folder list and reports anything
important that isn't covered yet.

Usage:
    python3 scripts/coverage-check.py

Exit 0 = everything covered (silent is fine — schedule it).
Exit 1 = gaps found (the report goes to the user).

The user decides which flagged folders join the backup. Never add folders
without their word.
"""

import os
import sys

# ---------------------------------------------------------------- config
# Where the user's "real" folders live — new projects appear here.
SCAN_ROOTS = [
    # os.path.expanduser("~"),
]

# The exact folder list the backup covers (mirror FOLDERS in backup.py).
BACKUP_FOLDERS = [
    # os.path.expanduser("~/ai-memory"),
]

# Folder names that are never worth flagging.
IGNORE_NAMES = {
    ".git", "__pycache__", "node_modules", ".venv", ".cache",
    "Library", ".local", ".npm", ".cargo",
}

# Folders smaller than this (bytes, recursive) are not flagged — they are
# almost always caches or tooling, not the user's work.
MIN_SIZE_BYTES = 50 * 1024
# ----------------------------------------------------------------------


def dir_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_NAMES]
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def main():
    if not SCAN_ROOTS or not BACKUP_FOLDERS:
        print("[lifeboat-coverage] SCAN_ROOTS/BACKUP_FOLDERS not configured — "
              "edit the config at the top of this file first")
        sys.exit(2)

    covered = {os.path.realpath(f) for f in BACKUP_FOLDERS}
    gaps = []
    for root in SCAN_ROOTS:
        try:
            entries = os.listdir(root)
        except OSError as e:
            print(f"[lifeboat-coverage] cannot scan {root}: {e}")
            continue
        for name in entries:
            if name in IGNORE_NAMES or name.startswith("."):
                continue
            path = os.path.realpath(os.path.join(root, name))
            if not os.path.isdir(path) or path in covered:
                continue
            # Skip anything nested inside an already-covered folder.
            if any(path.startswith(c + os.sep) for c in covered):
                continue
            size = dir_size(path)
            if size >= MIN_SIZE_BYTES:
                gaps.append((path, size))

    if not gaps:
        print("[lifeboat-coverage] OK — every folder is covered by the backup")
        sys.exit(0)

    print("[lifeboat-coverage] GAPS FOUND — these folders are NOT in the backup:")
    for path, size in sorted(gaps):
        print(f"  - {path} ({size // 1024} KB)")
    print("Ask the user which ones to add to the backup (backup.py FOLDERS).")
    sys.exit(1)


if __name__ == "__main__":
    main()
