#!/usr/bin/env python3
"""PreToolUse hook for Bash: run /check-changelog-docs before a changelog commit.

A ``git commit`` that carries new ``### Added`` or ``### Changed`` lines in
``CHANGELOG.md`` is denied once, with the instruction to run the
``/check-changelog-docs`` skill and report its result. The same changelog
content then commits on the next attempt: the hook remembers a hash of what it
stopped in ``.git/changelog-docs-checked``, so it never loops, and a later
edit to those entries triggers the check again.

It is a reminder, not a guard: anything it cannot read lets the commit through.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess  # nosec B404
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
CHANGELOG = "CHANGELOG.md"
STAMP = "changelog-docs-checked"
_SPLIT = re.compile(r"&&|\|\||[;|\n]|\$\(|`")
_SECTIONS = ("### Added", "### Changed")


def _git(*args: str) -> str:
    return subprocess.run(  # nosec B603 B607
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout


def _commit_kind(command: str) -> str | None:
    """'index' for a plain commit, 'worktree' when the command stages files itself, None for no commit."""
    commit = stages = False
    for segment in _SPLIT.split(command):
        try:
            tokens = shlex.split(segment, comments=True)
        except ValueError:
            tokens = segment.split()
        while tokens and re.match(r"^\w+=", tokens[0]):
            tokens.pop(0)
        if not tokens or tokens[0] != "git":
            continue
        rest = tokens[1:]
        while rest and rest[0] in ("-C", "-c"):
            rest = rest[2:]
        if not rest:
            continue
        if rest[0] == "add":
            stages = True
        elif rest[0] == "commit":
            commit = True
            options = rest[1:]
            if "--all" in options or any(re.match(r"^-[a-zA-Z]*a", o) for o in options) or CHANGELOG in options:
                stages = True
    if not commit:
        return None
    return "worktree" if stages else "index"


def _new_entry_lines(diff: str) -> list[str]:
    """Added lines that sit under ### Added or ### Changed inside ## [Unreleased]."""
    lines: list[str] = []
    unreleased = relevant = False
    for line in diff.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        text = line[1:] if line[:1] in "+- " else line
        if text.startswith("## "):
            unreleased = text.startswith("## [Unreleased]")
            relevant = False
        elif text.startswith("### "):
            relevant = unreleased and text.strip() in _SECTIONS
        elif line.startswith("+") and relevant and text.strip():
            lines.append(text)
    return lines


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        kind = _commit_kind(payload.get("tool_input", {}).get("command", ""))
        if kind is None:
            return 0
        base = ["diff", "--no-color", "-U100000"]
        diff = _git(*base, *(["HEAD"] if kind == "worktree" else ["--cached"]), "--", CHANGELOG)
        entries = _new_entry_lines(diff)
        if not entries:
            return 0
        digest = hashlib.sha256("\n".join(entries).encode()).hexdigest()
        stamp = os.path.join(ROOT, _git("rev-parse", "--git-path", STAMP).strip())
        try:
            with open(stamp, encoding="utf-8") as handle:
                if handle.read().strip() == digest:
                    return 0
        except OSError:
            pass
        with open(stamp, "w", encoding="utf-8") as handle:
            handle.write(digest + "\n")
    except (OSError, ValueError, subprocess.CalledProcessError):
        return 0
    reason = ("This commit adds CHANGELOG.md entries under ### Added or ### Changed. "
              "Run the /check-changelog-docs skill first and report its table to the user, "
              "then retry the same commit - it will go through unless the entries change again.")
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                      "permissionDecision": "deny",
                                      "permissionDecisionReason": reason}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
