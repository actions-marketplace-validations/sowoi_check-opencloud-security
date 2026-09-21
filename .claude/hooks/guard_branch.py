#!/usr/bin/env python3
"""PreToolUse hook for Bash: ask the user before switching branches.

Only a switch to a ``release/`` branch goes through unasked. Every other
``git checkout``/``git switch`` to a branch - fix, bugfix, feature, main or
anything else - is handed to the user for confirmation. Restoring files
(``git checkout -- path``, ``git checkout <ref> -- path``, ``git restore``)
is not a branch change and is left alone.

This is a guardrail against mistakes, not a sandbox: it splits the command on
shell separators and reads each ``git`` segment with shlex.
"""

from __future__ import annotations

import json
import re
import shlex
import sys

_ALLOWED = re.compile(r"^(?:origin/)?release/")
_SPLIT = re.compile(r"&&|\|\||[;|\n]|\$\(|`")
# Options of checkout/switch that take a value; the value names the new branch.
_NEW_BRANCH = {"-b", "-B", "-c", "-C", "--orphan", "--create", "--force-create"}
_WITH_VALUE = {"--conflict", "--pathspec-from-file"}


def _targets(tokens: list[str]) -> list[str]:
    """Branch names a checkout/switch token list moves to (empty for file restores)."""
    if "--" in tokens:
        return []
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
        return [new]
    if not positional:
        return []
    if positional == ["."]:
        return []
    return [positional[0]]


def _branch_switches(command: str) -> list[str]:
    targets: list[str] = []
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
            targets.extend(_targets(rest[1:]))
    return targets


def main() -> int:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    asked = [target for target in _branch_switches(command) if not _ALLOWED.match(target)]
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
