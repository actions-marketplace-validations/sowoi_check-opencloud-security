#!/usr/bin/env python3
"""PreToolUse hook for Bash: refuse commands the project never lets an agent run.

Publishing an advisory, merging or tagging a release, force-pushing, pushing
to main, discarding work and reformatting the tree are the user's decisions
(AGENTS.md, CLAUDE.md). The hook denies them with the reason, so the model
reports instead of retrying.
"""

from __future__ import annotations

import json
import re
import sys

# Rules match a command only at the start of a segment (after environment
# assignments and a runner such as `uv run` or `python`), so text that merely
# mentions a command - a heredoc, a commit message - does not trip them.
_PREFIX = (r"^\s*(?:\(\s*)?(?:\w+=\S*\s+)*"
           r"(?:(?:uvx|npx|sudo|exec|time|command|env)\s+|uv\s+run(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+"
           r"|python3?(?:\s+-m)?\s+)*")
_GIT = _PREFIX + r"git(?:\s+-[cC]\s+\S+)*\s+"
_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")

_RULES = (
    (
        re.compile(_PREFIX + r"(?:\S*/)?security_advisories\.py\b.*--(?:publish|sync)\b"),
        ("Publishing or syncing security advisories is the user's decision alone "
         "(it raises Dependabot alerts and cannot be undone)."),
    ),
    (
        re.compile(_PREFIX + r"gh\s+pr\s+merge\b"),
        ("Never merge a pull request or enable auto-merge - a version bump landing "
         "on main publishes to PyPI. Leave merging to the user."),
    ),
    (
        re.compile(_PREFIX + r"gh\s+release\s+(?:create|edit|delete|upload)\b"),
        "GitHub releases are made by the release workflow or the user, never by an agent.",
    ),
    (
        re.compile(_PREFIX + r"gh\s+api\b(?=.*security-advisories)(?=.*(?:-X|--method)\s*(?:POST|PATCH|PUT|DELETE)|.*\s-[fF]\s)"),
        "Never write security advisories through the API - publishing stays with the user.",
    ),
    (
        re.compile(_GIT + r"reset\b.*--hard\b"),
        "git reset --hard discards work. Ask the user first.",
    ),
    (
        re.compile(_GIT + r"(?:merge|rebase|cherry-pick)\b.*--abort\b"),
        "Do not abort a merge or rebase on your own - report the state and let the user decide.",
    ),
    (
        re.compile(_GIT + r"clean\b.*-\w*f"),
        "git clean -f deletes untracked files. Ask the user first.",
    ),
    (
        re.compile(_PREFIX + r"ruff(?:@\S+)?\s+format\b"),
        "Only `ruff check` is enforced here - never `ruff format` or reformat the tree.",
    ),
)

_TAG_READ_OPTIONS = ("-l", "--list", "--contains", "--no-contains", "--points-at",
                     "--merged", "--no-merged", "--sort", "-n", "--format", "--column")


def _git_tag_writes(segment: str) -> bool:
    match = re.match(_GIT + r"tag\b(.*)", segment)
    if not match:
        return False
    args = match.group(1).split()
    if not args:
        return False
    return not any(arg.startswith(_TAG_READ_OPTIONS) for arg in args)


def _git_push_problem(segment: str) -> str | None:
    match = re.match(_GIT + r"push\b(.*)", segment)
    if not match:
        return None
    args = match.group(1).split()
    if any(a in ("-f", "--force", "--mirror", "--delete", "-d") or a.startswith("--force")
           or (a.startswith("-") and not a.startswith("--") and "f" in a[1:])
           for a in args):
        return "Never force-push or delete remote refs. Ask the user first."
    if "--tags" in args or "--follow-tags" in args:
        return "Tags are created by the release workflow or the user, never pushed by an agent."
    refspecs = [a for a in args if not a.startswith("-")][1:]
    for ref in refspecs:
        if ref.startswith("+"):
            return "A '+' refspec is a force-push. Ask the user first."
        target = ref.split(":")[-1]
        if target in ("main", "refs/heads/main") or re.fullmatch(r"(?:refs/tags/)?v\d+(?:\.\d+)*", target):
            return "Never push to main or push a tag - a bump on main publishes to PyPI."
    return None


def check(command: str) -> str | None:
    """Return the reason to deny ``command``, or None to let it through."""
    for segment in _SEGMENT_SPLIT.split(command):
        for pattern, reason in _RULES:
            if pattern.match(segment):
                return reason
        if _git_tag_writes(segment):
            return "Creating or deleting tags is the user's decision (tags trigger releases)."
        problem = _git_push_problem(segment)
        if problem:
            return problem
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        print("unreadable hook input - refusing (fail closed)", file=sys.stderr)
        return 2
    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = check(command)
    if reason:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Project guard (.claude/hooks/guard_bash.py): " + reason,
            }
        }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
