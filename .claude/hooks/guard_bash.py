#!/usr/bin/env python3
"""PreToolUse hook for Bash: refuse commands the project never lets an agent run.

Publishing an advisory, merging or tagging a release, force-pushing, pushing
to main, discarding work and reformatting the tree are the user's decisions
(AGENTS.md, CLAUDE.md). The hook denies them with the reason, so the model
reports instead of retrying.

A shell write - a redirect, ``tee``, ``sed -i``, ``cp``/``mv``/``rm`` - to a
file the Edit guard protects gets the same decision as an Edit would
(guard_edit.path_rule), so Bash is not a way around it.

This is a guardrail against mistakes, not a sandbox. It splits a command into
the commands it runs - including ``$(...)``, backticks, ``bash -c``/``eval``
strings and ``xargs`` - on a "shape" of the command in which quoted text,
heredoc bodies and comments are masked, so text that merely mentions a
command (a commit message, a heredoc) does not trip it. It does not execute
or fully parse shell; substitutions inside an unquoted heredoc are not seen.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))

# Rules match a command only at the start of a segment, after environment
# assignments, grouping and a runner such as `uv run`, `xargs` or `python`.
_PREFIX = (r"^\s*(?:[({!]\s*)*(?:\w+=\S*\s+)*"
           r"(?:(?:uvx|npx|sudo|exec|eval|time|command|builtin|env|nohup)\s+"
           r"|nice(?:\s+-n\s*-?\d+)?\s+|timeout(?:\s+-\S+)*\s+\S+\s+"
           r"|xargs(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+"
           r"|uv\s+run(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+"
           r"|python3?(?:\s+-m)?\s+)*")
_GIT = _PREFIX + r"git(?:\s+-[cC]\s+\S+)*\s+"
# `&&`, `||`, `$(`, a lone `&` (not part of `>&`, `&>` or `2>&1`), and the
# other separators and grouping characters.
_SEGMENT_SPLIT = re.compile(r"&&|\|\||\$\(|(?<![<>&])&(?![>&])|[;|\n`(){}]")
_INNER = re.compile(r"(?:\b(?:ba|z|da|k)?sh(?:\s+-\w+)*\s+-\w*c|\beval)\s+(['\"])(.*?)\1", re.DOTALL)
_HEREDOC = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][\w.-]*)\2")
_REDIRECT = re.compile(r"\d*(?:>>?|<)\|?&?\s*[^\s;&|<>\0]+|&>>?\s*[^\s;&|<>\0]+")
_WRITE_REDIRECT = re.compile(r"(?:\d*>>?|&>>?)\|?\s*([^\s;&|<>\0]+)")
_BODY = "\0"  # marks heredoc text in a shape; it is data, not part of the command

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
        re.compile(_PREFIX + r"ruff(?:@\S+)?\s+format\b(?!.*\s--(?:check|diff)\b)"),
        "Only `ruff check` is enforced here - never `ruff format` or reformat the tree.",
    ),
)

_TAG_READ_OPTIONS = ("-l", "--list", "--contains", "--no-contains", "--points-at",
                     "--merged", "--no-merged", "--sort", "-n", "--format", "--column")


# --- reading a command ------------------------------------------------------

def shape(command: str) -> str:
    """A same-length copy of ``command`` in which literal text cannot look like shell.

    Quoted text and comments become ``x`` - except command substitutions
    (``$(...)``, backticks) inside double quotes, which run and keep their
    own shape - and heredoc bodies become NUL.
    """
    out = list(command)
    n, i = len(command), 0
    # Contexts: "code" (unquoted, also inside $(...) with its paren depth),
    # "`" (inside backticks), "'" and '"'.
    stack: list[list] = [["code", 0]]
    heredocs: list[tuple[str, bool]] = []
    while i < n:
        c = command[i]
        kind = stack[-1][0]
        if kind == "'":
            if c == "'":
                stack.pop()
            else:
                out[i] = "x"
            i += 1
        elif kind == '"':
            if c == "\\":
                out[i:i + 2] = "x" * len(out[i:i + 2])
                i += 2
            elif c == '"':
                stack.pop()
                i += 1
            elif c == "`":
                stack.append(["`", 0])
                i += 1
            elif command.startswith("$(", i):
                stack.append(["code", 0])
                i += 2
            else:
                out[i] = "x"
                i += 1
        elif c == "\\":
            out[i:i + 2] = "x" * len(out[i:i + 2])
            i += 2
        elif c in "'\"":
            stack.append([c, 0])
            i += 1
        elif c == "`":
            if kind == "`":
                stack.pop()
            else:
                stack.append(["`", 0])
            i += 1
        elif command.startswith("$(", i):
            stack.append(["code", 0])
            i += 2
        elif c == "(" and len(stack) > 1:
            stack[-1][1] += 1
            i += 1
        elif c == ")" and len(stack) > 1 and kind == "code":
            if stack[-1][1]:
                stack[-1][1] -= 1
            else:
                stack.pop()
            i += 1
        elif c == "#" and (i == 0 or command[i - 1] in " \t\n;&|()"):
            end = command.find("\n", i)
            end = n if end < 0 else end
            out[i:end] = "x" * (end - i)
            i = end
        elif (match := _HEREDOC.match(command, i)):
            heredocs.append((match.group(3), match.group(1) == "-"))
            i = match.end()
        elif c == "\n" and heredocs:
            # The bodies follow this line, one after the other; each ends with
            # a line holding only its delimiter. Everything up to the newline
            # after the last delimiter is data.
            pos = i
            for delimiter, strip_tabs in heredocs:
                while pos < n:
                    start = pos + 1
                    end = command.find("\n", start)
                    pos = n if end < 0 else end
                    line = command[start:pos]
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                        break
            out[i:pos] = _BODY * (pos - i)
            heredocs = []
            i = pos
        else:
            i += 1
    return "".join(out)


class Segment:
    """One command inside a Bash input: its text and its shape, the same length."""

    def __init__(self, raw: str, form: str) -> None:
        self.raw, self.shape = raw, form

    def match(self, pattern: str | re.Pattern) -> re.Match | None:
        return re.match(pattern, self.shape)

    def rest(self, match: re.Match) -> Segment:
        return Segment(self.raw[match.end():], self.shape[match.end():])

    def words(self) -> list[str]:
        """Shell words, without redirections and heredoc bodies."""
        chars = list(self.raw)
        for m in _REDIRECT.finditer(self.shape):
            chars[m.start():m.end()] = " " * (m.end() - m.start())
        text = "".join(c for c, s in zip(chars, self.shape, strict=True) if s != _BODY)
        try:
            return shlex.split(text)
        except ValueError:
            return text.split()

    def redirect_targets(self) -> list[str]:
        targets = []
        for m in _WRITE_REDIRECT.finditer(self.shape):
            raw = self.raw[m.start(1):m.end(1)]
            try:
                targets.extend(shlex.split(raw))
            except ValueError:
                targets.append(raw)
        return targets


def segments(command: str) -> list[Segment]:
    """The commands ``command`` runs, including those inside ``bash -c``/``eval`` strings."""
    form = shape(command)
    parts, last = [], 0
    for m in _SEGMENT_SPLIT.finditer(form):
        parts.append(Segment(command[last:m.start()], form[last:m.start()]))
        last = m.end()
    parts.append(Segment(command[last:], form[last:]))
    for m in _INNER.finditer(form):
        parts.extend(segments(command[m.start(2):m.end(2)]))
    return parts


def tokens(text: str) -> list[str]:
    """Shell words of a plain string (no heredoc), without redirections."""
    return Segment(text, shape(text)).words()


# --- rules ------------------------------------------------------------------

def _git_tag_writes(segment: Segment) -> bool:
    match = segment.match(_GIT + r"tag\b")
    if not match:
        return False
    args = segment.rest(match).words()
    return bool(args) and not any(arg.startswith(_TAG_READ_OPTIONS) for arg in args)


def push_arguments(segment: Segment) -> list[str] | None:
    """The arguments of a `git push` segment, or None if it is not one."""
    match = segment.match(_GIT + r"push\b")
    return segment.rest(match).words() if match else None


def positional_push_arguments(args: list[str]) -> list[str]:
    """Remote and refspecs of `git push`, including a remote passed by `--repo`."""
    positional, pending = [], None
    for arg in args:
        if pending:
            if pending == "remote":
                positional.append(arg)
            pending = None
        elif arg == "--repo":
            pending = "remote"
        elif arg.startswith("--repo="):
            positional.append(arg.split("=", 1)[1])
        elif arg in ("-o", "--push-option", "--receive-pack", "--exec"):
            pending = "value"
        elif not arg.startswith("-"):
            positional.append(arg)
    return positional


def _git_push_problem(segment: Segment) -> str | None:
    args = push_arguments(segment)
    if args is None:
        return None
    if any(a in ("-f", "--force", "--mirror", "--delete", "-d") or a.startswith("--force")
           or (a.startswith("-") and not a.startswith("--") and "f" in a[1:])
           for a in args):
        return "Never force-push or delete remote refs. Ask the user first."
    if "--tags" in args or "--follow-tags" in args:
        return "Tags are created by the release workflow or the user, never pushed by an agent."
    for ref in positional_push_arguments(args)[1:]:
        if ref.startswith("+"):
            return "A '+' refspec is a force-push. Ask the user first."
        target = ref.split(":")[-1]
        if target in ("main", "refs/heads/main") or re.fullmatch(r"(?:refs/tags/)?v\d+(?:\.\d+)*", target):
            return "Never push to main or push a tag - a bump on main publishes to PyPI."
    return None


def check(command: str) -> str | None:
    """Return the reason to deny ``command``, or None to let it through."""
    for segment in segments(command):
        for pattern, reason in _RULES:
            if segment.match(pattern):
                return reason
        if _git_tag_writes(segment):
            return "Creating or deleting tags is the user's decision (tags trigger releases)."
        problem = _git_push_problem(segment)
        if problem:
            return problem
    return None


# --- shell writes to protected files ----------------------------------------

_ALL_ARGUMENTS = {"tee", "rm", "truncate", "shred", "unlink", "mv"}
_LAST_ARGUMENT = {"cp", "install", "rsync", "ln", "scp"}
_IN_PLACE = {"sed", "gsed", "perl", "ruby"}
_NOT_FILES = ("/dev/null", "/dev/stdout", "/dev/stderr", "-")


def _load_guard_edit():
    spec = importlib.util.spec_from_file_location("guard_edit", os.path.join(HOOK_DIR, "guard_edit.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _in_place(name: str, args: list[str]) -> bool:
    if name not in _IN_PLACE:
        return False
    return any(a.startswith("--in-place") or re.fullmatch(r"-[a-zA-Z]*i\S*", a) for a in args)


def write_targets(segment: Segment) -> list[str]:
    """Files a shell segment writes to, as far as a word-level look can tell."""
    targets = segment.redirect_targets()
    prefix = segment.match(_PREFIX)
    words = (segment.rest(prefix) if prefix else segment).words()
    if words:
        name, args = os.path.basename(words[0]), words[1:]
        files = [a for a in args if not a.startswith("-")]
        if name in _ALL_ARGUMENTS:
            targets += files
        elif name in _LAST_ARGUMENT and files:
            targets.append(files[-1])
        elif _in_place(name, args):
            # sed's first operand is the script unless -e/-f supplied it; perl/ruby take -e.
            script_given = any(a.startswith(("-e", "-f")) for a in args)
            targets += files if script_given else files[1:]
        elif name == "dd":
            targets += [a[3:] for a in args if a.startswith("of=")]
    return [t for t in targets if t not in _NOT_FILES]


def write_decision(command: str, cwd: str, root: str) -> tuple[str, str] | None:
    """The Edit guard's decision for the protected files a command writes, if any."""
    guard_edit = _load_guard_edit()
    asked = None
    for segment in segments(command):
        for target in write_targets(segment):
            path = os.path.realpath(os.path.join(cwd, os.path.expanduser(target)))
            rel = os.path.relpath(path, os.path.realpath(root)).replace(os.sep, "/")
            if rel.startswith(".."):
                continue
            rule = guard_edit.path_rule(rel, whole_file=True)
            if rule and rule[0] == "deny":
                return rule
            asked = asked or rule
    return asked


def decide(command: str, cwd: str, root: str) -> tuple[str, str] | None:
    """(decision, reason) for a Bash command, or None to let it through."""
    reason = check(command)
    if reason:
        return "deny", reason
    return write_decision(command, cwd, root)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        print("unreadable hook input - refusing (fail closed)", file=sys.stderr)
        return 2
    command = (payload.get("tool_input") or {}).get("command") or ""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    result = decide(command, payload.get("cwd") or root, root)
    if result:
        decision, reason = result
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": "Project guard (.claude/hooks/guard_bash.py): " + reason,
            }
        }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
