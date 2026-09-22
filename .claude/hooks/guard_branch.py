#!/usr/bin/env python3
"""PreToolUse hook for Bash: keep the work on a ``release/`` branch.

Work happens on a ``release/`` branch - a feature is never implemented on a
feature, fix, chore or docs branch. So:

* creating a branch that is not ``release/...`` is **refused**, and
* switching to a branch that is not ``release/...`` is **refused**, except for
  the integration branches (``main``/``master``) and ``-``, which are handed
  to the user for confirmation.

Restoring files (``git checkout -- path``, ``git checkout <ref> -- path``,
``git restore``) is not a branch change and is left alone.

This is a guardrail against mistakes, not a sandbox: it splits the command on
shell separators and reads each ``git`` segment with shlex.
"""

from __future__ import annotations

import json
import re
import shlex
import sys

_ALLOWED = re.compile(r"^(?:origin/)?release/")
# Integration branches: switching to one is a decision for the user, not a refusal.
_ASKABLE = {"main", "master", "origin/main", "origin/master", "-"}
_SPLIT = re.compile(r"&&|\|\||[;|\n]|\$\(|`")
# Options of checkout/switch that take a value; the value names the new branch.
_NEW_BRANCH = {"-b", "-B", "-c", "-C", "--orphan", "--create", "--force-create"}
_WITH_VALUE = {"--conflict", "--pathspec-from-file"}


def _targets(tokens: list[str]) -> tuple[list[str], bool]:
    """Branch names a checkout/switch moves to, and whether it creates one."""
    if "--" in tokens:
        return [], False
    new = None
    positional: list[str] = []
    skip = False
    for index, token in enumerate(tokens):
        if skip:
            skip = False
            continue
        if token in _NEW_BRANCH:
            new = tokens[index + 1] if index + 1 < len(tokens) else ""
            skip = True
        elif token.startswith(("--create=", "--force-create=", "--orphan=")):
            new = token.split("=", 1)[1]
        elif token in _WITH_VALUE:
            skip = True
        elif token.startswith("-"):
            continue
        else:
            positional.append(token)
    if new is not None:
        return [new], True
    if not positional:
        return [], False
    if positional == ["."]:
        return [], False
    return [positional[0]], False


def _branch_switches(command: str) -> tuple[list[str], list[str]]:
    """Branches the command switches to, and branches it creates."""
    targets: list[str] = []
    created: list[str] = []
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
        if rest and rest[0] in ("checkout", "switch"):
            names, creates = _targets(rest[1:])
            (created if creates else targets).extend(names)
        elif rest and rest[0] == "branch":
            created.extend(_new_branches(rest[1:]))
        elif rest[:2] == ["worktree", "add"]:
            created.extend(_worktree_branches(rest[2:]))
    return targets, created


def _new_branches(tokens: list[str]) -> list[str]:
    """Branch names ``git branch`` would create (empty for listing or deleting)."""
    if any(token.startswith("-") and token not in ("-f", "--force") for token in tokens):
        return []
    positional = [token for token in tokens if not token.startswith("-")]
    return positional[:1]


def _worktree_branches(tokens: list[str]) -> list[str]:
    """Branch names ``git worktree add`` would create."""
    created: list[str] = []
    skip = False
    for index, token in enumerate(tokens):
        if skip:
            skip = False
            continue
        if token in ("-b", "-B"):
            created.append(tokens[index + 1] if index + 1 < len(tokens) else "")
            skip = True
    return created


def main() -> int:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    targets, created = _branch_switches(command)
    refused = [name for name in created if not _ALLOWED.match(name)]
    refused += [name for name in targets
                if not _ALLOWED.match(name) and name not in _ASKABLE]
    if refused:
        print("Refusing to create or switch to " + ", ".join(repr(name) for name in refused)
              + " - work on this project happens on a release/ branch; a feature is never"
              " implemented on a feature, fix, chore or docs branch. Ask the user which"
              " release branch to use.", file=sys.stderr)
        return 2
    asked = [name for name in targets if not _ALLOWED.match(name)]
    if not asked:
        return 0
    reason = ("Switching to branch " + ", ".join(repr(t) for t in asked)
              + " needs the user's confirmation - only release/ branches are switched to unasked.")
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                      "permissionDecision": "ask",
                                      "permissionDecisionReason": reason}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
