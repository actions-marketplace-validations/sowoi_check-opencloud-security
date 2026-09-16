#!/usr/bin/env python3
"""Keep real instances, scan output and personal data out of commits.

AGENTS.md: the live test server's hostname must never appear in code, tests,
documentation or commit messages, and examples use opencloud.example.com.
This guard looks at what is about to be (or already was) committed. Only
values that are **new** count - not already on the base branch, not reserved
for documentation (example.com, .test, .invalid, .localhost, .internal, RFC
5737/3849 addresses) and not in ``privacy_allowlist.txt``.

Blocking findings:

- a hostname that looks like an instance or scan target (a cloud/files/drive
  style name, or used as a target: after -H, --host, target_url, "scanned",
  or with an OpenCloud path such as /status.php);
- a public IP address (outside tests/, where boundary cases are reviewed)
  and a personal e-mail address;
- output of a scan - a result document, plugin output in any --format, a web
  application export (``scan-<uuid>.*``) - in a data file outside tests/;
- credentials: private keys and well-known token formats.

Review findings (any other new hostname, a role mailbox such as support@,
a bearer token or JWT under tests/) are shown for confirmation, not blocked.

Two entry points, both configured in .claude/settings.json:

- ``PreToolUse`` (Bash): ``git commit`` checks the staged changes (and the
  working tree when the command stages files itself) plus the message,
  ``git push`` checks the commits it would push, ``gh pr create/edit`` checks
  the body. A blocking finding denies the command, a review finding asks.
- ``Stop``: checks the staged changes and every commit not yet pushed. A
  blocking finding blocks the stop once, so the model deals with it; if it is
  still there, the user gets a warning. Review findings are only shown.

It is a text heuristic, not a proof: it catches the likely leaks, and an
approved public reference host goes into privacy_allowlist.txt - which only the
user may extend.
"""

from __future__ import annotations

import fnmatch
import importlib.util
import ipaddress
import json
import os
import re
import subprocess  # nosec B404
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
ALLOWLIST = os.path.join(HOOK_DIR, "privacy_allowlist.txt")
SKIP_PATHS = (".claude/hooks/privacy_guard.py", ".claude/hooks/privacy_allowlist.txt")
MAX_FINDINGS = 25

# --- what counts as reserved / harmless -------------------------------------

_RESERVED_DOMAINS = ("example.com", "example.net", "example.org", "example.edu")
_RESERVED_SUFFIXES = ("example", "test", "invalid", "localhost", "local", "internal", "lan",
                      "home.arpa", "corp", "intranet", "private")
_ALWAYS_ALLOWED = ("*@users.noreply.github.com", "noreply@github.com", "noreply@anthropic.com")

# Top-level domains a bare token must end in to count as a hostname. Kept to
# ones that do not collide with file extensions or attribute names
# (.py, .md, .sh, .app, .info, .email, .network ... are deliberately missing).
_TLDS = ("com|net|org|eu|de|at|ch|nl|be|fr|es|it|uk|io|cloud|co|biz|xyz|me|cz|se|dk|fi|lu|li|pl|pt|"
         "ie|us|ca|au|tv|cc|gmbh|berlin|hamburg|koeln|bayern")
_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_URL_HOST = re.compile(r"\b[a-z][a-z0-9+.-]*://(?:[^\s/@'\"<>]*@)?(\[[0-9a-f:.]+\]|[a-z0-9.-]+)", re.IGNORECASE)
_BARE_HOST = re.compile(r"(?<![\w.@/-])((?:" + _LABEL + r"\.)+(?:" + _TLDS + r"))(?![\w-]|\.\w|\()", re.IGNORECASE)
_QUOTED_HOST = re.compile(r"[\"'`]((?:" + _LABEL + r"\.)+(?:" + _TLDS + r"))(?=[\"'`/:])", re.IGNORECASE)
_EMAIL = re.compile(r"(?<![\w.%+-])([a-z0-9._%+-]+@((?:" + _LABEL + r"\.)+[a-z]{2,}))\b", re.IGNORECASE)
_IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?![\w]|\.\d)")
_IPV6 = re.compile(r"(?<![\w:.])((?:[0-9a-f]{1,4})?(?::[0-9a-f]{0,4}){2,7})(?![\w:.])", re.IGNORECASE)
_CODE_SUFFIXES = (".py", ".js", ".mjs", ".cjs", ".ts", ".css", ".jinja", ".j2")

_SECRETS = (
    ("private key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{24,}=*")),
)

# --- what scan output looks like --------------------------------------------

_SCAN_FINGERPRINTS = (
    ("scanner result document", (re.compile(r'"scannedAt"\s*:'), re.compile(r'"ratingExplanation"\s*:'))),
    ("plugin JSON output", (re.compile(r'"plugin"\s*:\s*"check-opencloud-security"'), re.compile(r'"exit_code"\s*:'))),
    ("SARIF report", (re.compile(r'"name"\s*:\s*"check-opencloud-security"'), re.compile(r'"results"\s*:'))),
    ("JUnit report", (re.compile(r'<testsuites name="check-opencloud-security"'),)),
    ("Prometheus output", (re.compile(r'opencloud_security_rating_score\{[^}\n]*\}\s+\d'),)),
    ("Nagios/Icinga output", (re.compile(r'OpenCloud \S+ on \S+, rating: \S+, last scanned:'),)),
    ("Checkmk output", (re.compile(r'"OpenCloud_Security_[^"\n]+" rating=\d'),)),
    ("OTLP export", (re.compile(r'"resourceMetrics"\s*:'), re.compile(r'"stringValue"\s*:\s*"check-opencloud-security"'))),
    ("CSV report", (re.compile(r'^check-opencloud-security,\d', re.MULTILINE), re.compile(r'^Instance,', re.MULTILINE))),
)
_DATA_SUFFIXES = (".json", ".jsonl", ".ndjson", ".sarif", ".xml", ".csv", ".tsv", ".prom", ".txt",
                  ".log", ".out", ".pdf", ".har", ".yml", ".yaml")
# Generated from files that are checked themselves; RELEASE.md is written by the release workflow.
GENERATED_PATHS = ("frontend/static/search-index*.json", "webapp/data/admin-search-index*.json",
                   "frontend/templates/docs/*",
                   "frontend/templates/admin-docs/*", "RELEASE.md")
_EXPORT_NAME = re.compile(r"(?:^|/)scan-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.", re.IGNORECASE)


def _git(*args: str) -> str:
    result = subprocess.run(  # nosec B603 B607
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False,
        encoding="utf-8", errors="replace",
    )
    return result.stdout if result.returncode == 0 else ""


def _ref_exists(ref: str) -> bool:
    return bool(_git("rev-parse", "--verify", "--quiet", ref + "^{commit}").strip())


def _base_ref() -> str | None:
    for ref in ("origin/main", "main"):
        if _ref_exists(ref):
            return ref
    return None


def _push_range() -> str | None:
    """The commits `git push` would send: upstream..HEAD, else base..HEAD."""
    upstream = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}").strip()
    base = upstream or _base_ref()
    return base + "..HEAD" if base else None


# --- collecting what is new ---------------------------------------------------

class Source:
    """Added text, grouped by path: {path: [(line_number, text), ...]}."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.files: dict[str, list[tuple[int, str]]] = {}
        self.messages: list[str] = []

    def add_line(self, path: str, number: int, text: str) -> None:
        self.files.setdefault(path, []).append((number, text))

    def add_path(self, path: str) -> None:
        self.files.setdefault(path, [])


def _parse_patch(text: str, source: Source) -> None:
    path, number = None, 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            match = re.search(r" b/(.+)$", line)
            path = match.group(1) if match else None
            if path:
                source.add_path(path)
        elif line.startswith("+++ "):
            path = None if line[4:] == "/dev/null" else line[6:]
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            number = int(match.group(1)) if match else 0
        elif path and line.startswith("+"):
            source.add_line(path, number, line[1:])
            number += 1


def _diff(source: Source, *args: str) -> None:
    _parse_patch(_git("diff", *args, "-U0", "--no-color", "--no-ext-diff", "--no-renames"), source)


def _untracked(source: Source) -> None:
    for path in _git("ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if not path:
            continue
        source.add_path(path)
        full = os.path.join(ROOT, path)
        try:
            if os.path.getsize(full) > 2_000_000:
                continue
            with open(full, encoding="utf-8") as handle:
                for number, text in enumerate(handle, 1):
                    source.add_line(path, number, text.rstrip("\n"))
        except (OSError, UnicodeDecodeError):
            continue


def _commits(source: Source, rev_range: str) -> None:
    log = _git("log", "-p", "-U0", "--no-color", "--no-ext-diff", "--no-renames",
               "--format=%x01%h%x02%B%x03", rev_range)
    for chunk in log.split("\x01")[1:]:
        _, _, rest = chunk.partition("\x02")
        message, _, patch = rest.partition("\x03")
        source.messages.append(message)
        _parse_patch(patch, source)


# --- judging ------------------------------------------------------------------

BLOCK, REVIEW = "block", "review"

# A new host is treated as a real instance - not as a reference link - when
# its name or the line around it looks like one.
_INSTANCE_WORDS = re.compile(
    r"(?:^|[.-])(?:\w*cloud\w*|ocis|files?|drive|share|sync|webdav|dav|storage|nas)(?:[.-]|$)", re.IGNORECASE)
# ... or when it is used as one: right after a target flag or verb, or with a
# path only an OpenCloud (or ownCloud/Nextcloud) server answers.
_TARGET_BEFORE = (r"(?:\s-H|--host(?:name)?|--url|target(?:_url)?|\bhost(?:name)?|\bdomain|\bscann?(?:ed|ing)?"
                  r"|\bscan of|\baudit(?:ed)? of|\bagainst)\s*[:=]?\s*[\"'`]?(?:https?://)?")
_TARGET_AFTER = r"(?::\d+)?/(?:status\.php|ocs/|remote\.php|dav/|graph/|\.well-known/openid)"


def _used_as_target(host: str, text: str) -> bool:
    escaped = re.escape(host)
    return bool(re.search(_TARGET_BEFORE + escaped + r"(?![\w.-])", " " + text, re.IGNORECASE)
                or re.search(escaped + _TARGET_AFTER, text, re.IGNORECASE))


_ROLE_MAILBOX = re.compile(
    r"^(?:support|security|noreply|no-reply|info|contact|abuse|postmaster|hostmaster|webmaster|admin|"
    r"privacy|legal|press|hello|team|help|sales|dependabot|bot|git)(?:[+.-][^@]*)?@", re.IGNORECASE)
_STRONG_SECRETS = ("private key", "GitHub token", "Anthropic API key", "AWS access key", "Slack token", "GitLab token")


def _load_allowlist() -> list[str]:
    try:
        with open(ALLOWLIST, encoding="utf-8") as handle:
            entries = [line.split("#", 1)[0].strip().lower() for line in handle]
    except OSError:
        entries = []
    return [entry for entry in entries if entry] + list(_ALWAYS_ALLOWED)


def _allowlisted(value: str, allowlist: list[str]) -> bool:
    value = value.lower()
    return any(value == entry or fnmatch.fnmatch(value, entry) for entry in allowlist)


def _reserved_host(host: str) -> bool:
    host = host.lower().strip(".[]")
    if host == "localhost" or ("." not in host and ":" not in host):
        return True
    try:
        return not ipaddress.ip_address(host).is_global
    except ValueError:
        pass
    if any(host == d or host.endswith("." + d) for d in _RESERVED_DOMAINS):
        return True
    return any(host == s or host.endswith("." + s) for s in _RESERVED_SUFFIXES)


def _public_ip(text: str) -> str | None:
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        return None
    if address.version == 6 and "::" not in text and text.count(":") != 7:
        return None
    return text if address.is_global else None


def _candidates(path: str, text: str):
    """Yield (tier, kind, value) for everything worth checking in one added line."""
    code = path.endswith(_CODE_SUFFIXES)
    tests = path.startswith("tests/")
    email_domains = set()
    for match in _EMAIL.finditer(text):
        email_domains.add(match.group(2).lower())
        if not _reserved_host(match.group(2)):
            role = _ROLE_MAILBOX.match(match.group(1))
            yield (REVIEW if role else BLOCK), ("role e-mail address" if role else "e-mail address"), match.group(1)
    hosts = {m.group(1) for m in _URL_HOST.finditer(text)}
    hosts |= {m.group(1) for m in (_QUOTED_HOST if code else _BARE_HOST).finditer(text)}
    hosts = {h.strip(".[]").lower() for h in hosts}
    for host in hosts:
        if host in email_domains or _reserved_host(host):
            continue
        if _public_ip(host):
            yield (REVIEW if tests else BLOCK), "IP address", host
        elif _INSTANCE_WORDS.search(host) or _used_as_target(host, text):
            yield BLOCK, "hostname (looks like an instance or scan target)", host
        else:
            yield REVIEW, "hostname", host
    for pattern in (_IPV4, _IPV6):
        for match in pattern.finditer(text):
            address = _public_ip(match.group(1))
            if address and address.lower() not in hosts:
                yield (REVIEW if tests else BLOCK), "IP address", address
    for kind, pattern in _SECRETS:
        for match in pattern.finditer(text):
            tier = BLOCK if kind in _STRONG_SECRETS or not tests else REVIEW
            yield tier, kind, match.group(0)


def _known_on_base(values: set[str], base: str | None) -> set[str]:
    """The values that already appear somewhere on the base branch."""
    if not base or not values:
        return set()
    args = ["grep", "-F", "-i", "-o", "-h", "--no-color", "-I"]
    for value in sorted(values):
        args += ["-e", value]
    found = _git(*args, base, "--", ".", ":!.claude/hooks").splitlines()
    known = {line.strip().lower() for line in found}
    return {value for value in values if value.lower() in known}


def _scan_output_kind(path: str, text: str) -> str | None:
    if path.startswith("tests/"):
        return None
    name = os.path.basename(path)
    if not (path.lower().endswith(_DATA_SUFFIXES) or "." not in name):
        return None
    for kind, patterns in _SCAN_FINGERPRINTS:
        if all(p.search(text) for p in patterns):
            return kind
    return None


def _mask(kind: str, value: str) -> str:
    if "hostname" in kind or "address" in kind:
        return value
    return value[:6] + "..." if len(value) > 6 else "***"


def evaluate(sources: list[Source]) -> dict[str, list[str]]:
    """Return {"block": [...], "review": [...]}, one line per finding."""
    base = _base_ref()
    allowlist = _load_allowlist()
    raw: list[tuple[str, str, str, str, str]] = []  # (tier, where, kind, value, source)
    structural: list[str] = []
    for source in sources:
        for path, lines in source.files.items():
            if path in SKIP_PATHS or any(fnmatch.fnmatch(path, g) for g in GENERATED_PATHS):
                continue
            if _EXPORT_NAME.search(path):
                structural.append(f"{source.label}: {path} - a web application scan export (scan-<uuid>.*)")
            kind = _scan_output_kind(path, "\n".join(text for _, text in lines))
            if kind:
                structural.append(f"{source.label}: {path} - looks like {kind}; scan results never belong in the repository")
            for number, text in lines:
                for tier, kind, value in _candidates(path, text):
                    raw.append((tier, f"{path}:{number}", kind, value, source.label))
        for message in source.messages:
            for tier, kind, value in _candidates("COMMIT_MESSAGE", message):
                raw.append((tier, "message", kind, value, source.label))
    values = {value for _, _, _, value, _ in raw if not _allowlisted(value, allowlist)}
    known = _known_on_base(values, base)
    result = {BLOCK: list(dict.fromkeys(structural)), REVIEW: []}
    seen = set()
    for tier, where, kind, value, label in raw:
        if value not in values or value in known or (where, value) in seen:
            continue
        seen.add((where, value))
        result[tier].append(f"{label}: {where} - new {kind} {_mask(kind, value)}")
    return result


def _bullets(findings: list[str]) -> str:
    shown = findings[:MAX_FINDINGS]
    more = len(findings) - len(shown)
    return "\n".join("  - " + f for f in shown) + (f"\n  - ... and {more} more" if more else "")


def _block_report(findings: list[str]) -> str:
    return (
        "Privacy guard (.claude/hooks/privacy_guard.py) found data that must never be committed - "
        "a real instance, scan output, personal data or a credential:\n" + _bullets(findings) + "\n\n"
        "Replace hosts with opencloud.example.com (or another reserved name, a 192.0.2.x / 2001:db8:: "
        "address), remove scan output and credentials, and do not push. If a commit already contains it, "
        "stop and tell the user - rewriting history (amend/rebase) is their decision. If a finding is a "
        "public reference (documentation, vendor, public resolver) rather than an instance or a person, "
        "ask the user to add it to .claude/hooks/privacy_allowlist.txt; never add it yourself."
    )


def _review_report(findings: list[str]) -> str:
    return (
        "Privacy guard: new hostnames or role addresses that are not on the base branch. Confirm each is "
        "a public reference, not a real instance or a person (approved ones belong in "
        ".claude/hooks/privacy_allowlist.txt):\n" + _bullets(findings)
    )


# --- entry points -------------------------------------------------------------

def _load_guard_bash():
    spec = importlib.util.spec_from_file_location("guard_bash", os.path.join(HOOK_DIR, "guard_bash.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _body_file(command: str) -> Source | None:
    match = re.search(r"--body-file[= ]\s*(['\"]?)([^'\"\s]+)\1", command)
    if not match:
        return None
    source = Source("pull request body")
    try:
        with open(os.path.join(ROOT, match.group(2)), encoding="utf-8") as handle:
            for number, text in enumerate(handle, 1):
                source.add_line(match.group(2), number, text.rstrip("\n"))
    except (OSError, UnicodeDecodeError):
        return None
    return source


def pre_tool_use(command: str) -> dict[str, list[str]]:
    guard = _load_guard_bash()
    segments = guard._SEGMENT_SPLIT.split(command)
    commit = any(re.match(guard._GIT + r"commit\b", s) for s in segments)
    push = any(re.match(guard._GIT + r"push\b", s) for s in segments)
    pull_request = any(re.match(guard._PREFIX + r"gh\s+pr\s+(?:create|edit|comment)\b", s) for s in segments)
    if not (commit or push or pull_request):
        return {BLOCK: [], REVIEW: []}
    sources = []
    if commit or pull_request:
        text = Source("commit command" if commit else "pull request command")
        text.messages.append(command)
        sources.append(text)
    if commit:
        staged = Source("staged")
        _diff(staged, "--cached")
        sources.append(staged)
        stages_itself = re.search(r"\bgit\b[^;&|]*\badd\b|\bcommit\b[^;&|]*\s(?:-[a-zA-Z]*a[a-zA-Z]*|--all)\b", command)
        if stages_itself:
            working = Source("working tree")
            _diff(working)
            _untracked(working)
            sources.append(working)
    if push:
        rev_range = _push_range()
        if rev_range:
            commits = Source(f"commit in {rev_range}")
            _commits(commits, rev_range)
            sources.append(commits)
    if pull_request:
        body = _body_file(command)
        if body:
            sources.append(body)
    return evaluate(sources)


def stop() -> dict[str, list[str]]:
    staged = Source("staged")
    _diff(staged, "--cached")
    sources = [staged]
    rev_range = _push_range()
    if rev_range:
        commits = Source(f"unpushed commit ({rev_range})")
        _commits(commits, rev_range)
        sources.append(commits)
    return evaluate(sources)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "stop"
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        if mode == "pre-tool-use":
            print("unreadable hook input - refusing (fail closed)", file=sys.stderr)
            return 2
        payload = {}
    if mode == "pre-tool-use":
        found = pre_tool_use((payload.get("tool_input") or {}).get("command") or "")
        if found[BLOCK]:
            decision, reason = "deny", _block_report(found[BLOCK])
        elif found[REVIEW]:
            decision, reason = "ask", _review_report(found[REVIEW])
        else:
            return 0
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }}, sys.stdout)
        return 0

    found = stop()
    response: dict[str, str] = {}
    if found[BLOCK]:
        if payload.get("stop_hook_active"):
            response["systemMessage"] = "Privacy guard - unresolved, do not push:\n" + _bullets(found[BLOCK])
        else:
            response["decision"] = "block"
            response["reason"] = _block_report(found[BLOCK])
    if found[REVIEW] and not payload.get("stop_hook_active"):
        note = _review_report(found[REVIEW])
        response["systemMessage"] = (response.get("systemMessage", "") + "\n" + note).strip()
    if response:
        json.dump(response, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
