#!/usr/bin/env python3
"""
Hold every Python dependency to a justification, tests and a security review.

    python scripts/check_dependencies.py --check                   # CI
    python scripts/check_dependencies.py --check --base origin/main
    python scripts/check_dependencies.py --list

A package this project installs runs with the same rights as the project: in
the monitoring agent, in the public web service, in CI with a token in reach.
So a new one is a decision, and the decision is written down before the
package is used. ``security/dependencies/<name>.yml`` holds one record per
dependency: why it is needed, which tests exercise it, what a security review
of it found, and who approved it. See ADR 0060 and
``security/dependencies/README.md``.

**What counts as a dependency.** Every requirement in ``pyproject.toml`` -
``[project] dependencies``, every extra, every dependency group and the
``[build-system]`` requirements - and every package a workflow runs with
``uvx``. The scope each one is declared in is part of the record, so moving a
test-only package into the runtime is a change the record has to follow.
Transitive packages are not listed one by one; the record of the package that
pulls them in names them, and ``pip-audit`` covers the locked set.

**What ``--check`` refuses.**

* a declared dependency with neither a record nor a grandfather entry,
* a record that is not ``approved``, or misses a field, or names a test that
  does not exist or never mentions the package,
* a record whose scopes differ from where the package is declared,
* a record, or a grandfather entry, for a package nothing declares, and
* with ``--base``, a grandfather list that gained a name. The list is the set
  of dependencies that predate the policy; it may only shrink.

``tomllib`` is 3.11+ and this project supports 3.10, so the manifest is read
by a small scanner of its own - enough for the arrays of strings this file
uses, and tested against ``tomllib`` wherever that exists.
"""

from __future__ import annotations

import argparse
import datetime
import re
import shlex
import subprocess  # nosec B404 - git is invoked with a fixed argv
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RECORD_DIR = Path("security") / "dependencies"
GRANDFATHERED = RECORD_DIR / "grandfathered.txt"

#: What a record may say it is. Only ``approved`` lets a package be used; a
#: ``proposed`` record is a review in progress and fails the check on purpose.
STATES = ("proposed", "approved")

REQUIRED_FIELDS = (
    "name",
    "import_name",
    "status",
    "reviewed_version",
    "justification",
    "alternatives_considered",
)

#: The questions a security review has to answer, each in its own words.
REVIEW_FIELDS = (
    "reviewer",
    "reviewed_on",
    "known_vulnerabilities",
    "maintenance",
    "provenance",
    "install_time",
    "runtime_network",
    "native_code",
    "transitive_dependencies",
    "license",
)

#: Where the evidence that a package is exercised may live. A workflow counts
#: for a CI tool, because the workflow run is what exercises it.
TEST_ROOTS = ("tests/", ".github/workflows/")

#: ``uvx`` options that take a value, and the two whose value is a package.
UVX_VALUE_OPTIONS = frozenset({"--from", "--with", "--python", "-p", "--index", "--index-url"})
UVX_PACKAGE_OPTIONS = frozenset({"--from", "--with"})

REQUIREMENT_NAME = re.compile(r"^\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")


def normalise(name: str) -> str:
    """A package name as PyPI compares it (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement: str) -> str | None:
    """The normalised distribution name of a PEP 508 requirement or a tool spec."""
    match = REQUIREMENT_NAME.match(requirement)
    return normalise(match.group(1)) if match else None


# ------------------------------------------------------------- the manifest


def _array_strings(text: str, start: int) -> tuple[list[str], int]:
    """
    The strings of the TOML array opening at ``text[start]``, and its end.

    Brackets inside strings (``redis[hiredis]``) and comments are skipped;
    inline tables such as ``{include-group = "test"}`` contribute nothing.
    """
    strings: list[str] = []
    depth = 0
    table_depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char in "\"'":
            end = text.index(char, index + 1)
            if table_depth == 0 and depth == 1:
                strings.append(text[index + 1 : end])
            index = end + 1
            continue
        if char == "#":
            index = text.index("\n", index) if "\n" in text[index:] else len(text)
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return strings, index + 1
        elif char == "{":
            table_depth += 1
        elif char == "}":
            table_depth -= 1
        index += 1
    raise ValueError("pyproject.toml has an unterminated array")


def manifest_dependencies(pyproject: str) -> dict[str, set[str]]:
    """Every requirement in ``pyproject.toml``, as name -> scopes."""
    found: dict[str, set[str]] = {}
    table = ""
    position = 0
    line_pattern = re.compile(r"^[ \t]*(\[\[?[^\]\n]+\]\]?|[A-Za-z0-9_.\"'-]+)[ \t]*(=[ \t]*\[)?", re.MULTILINE)
    while True:
        match = line_pattern.search(pyproject, position)
        if match is None:
            return found
        head = match.group(1)
        if head.startswith("["):
            table = head.strip("[]").strip()
            position = match.end()
            continue
        if match.group(2) is None:
            position = pyproject.find("\n", match.end())
            if position == -1:
                return found
            continue
        key = head.strip("\"'")
        strings, position = _array_strings(pyproject, match.end() - 1)
        scope = _scope(table, key)
        if scope is None:
            continue
        for requirement in strings:
            name = requirement_name(requirement)
            if name:
                found.setdefault(name, set()).add(scope)


def _scope(table: str, key: str) -> str | None:
    """The scope an array in ``table`` declares, or None if it declares none."""
    if table == "project" and key == "dependencies":
        return "runtime"
    if table == "project.optional-dependencies":
        return f"extra:{key}"
    if table == "dependency-groups":
        return f"group:{key}"
    if table == "build-system" and key == "requires":
        return "build"
    return None


def uvx_packages(workflow: str) -> set[str]:
    """The packages a workflow runs through ``uvx``."""
    joined = re.sub(r"\\\n", " ", workflow)
    packages: set[str] = set()
    # The rest of the line and the indented lines after it, because a folded
    # scalar (`run: >`) puts a command's arguments on the lines that follow.
    # Parsing stops at the tool name, so whatever comes after it is harmless.
    # Each occurrence is read on its own, so one invocation's continuation
    # never hides the next.
    continuation = re.compile(r"[^\n]*(?:\n[ \t]+[^\n#][^\n]*)*")
    for match in re.finditer(r"(?<![\w-])uvx\b", joined):
        line_start = joined.rfind("\n", 0, match.start()) + 1
        if "#" in joined[line_start : match.start()]:
            continue
        text = continuation.match(joined, match.end())
        tail = text.group(0) if text else ""
        try:
            rest = shlex.split(tail, comments=True)
        except ValueError:
            rest = tail.split()
        packages |= _uvx_invocation_packages(["uvx", *rest])
    return packages


def _uvx_invocation_packages(tokens: list[str]) -> set[str]:
    packages: set[str] = set()
    for start, token in enumerate(tokens):
        if token != "uvx":
            continue
        tool_from_option = False
        index = start + 1
        while index < len(tokens):
            token = tokens[index]
            option, _, inline = token.partition("=")
            if option in UVX_VALUE_OPTIONS:
                value = inline or (tokens[index + 1] if index + 1 < len(tokens) else "")
                if option in UVX_PACKAGE_OPTIONS:
                    for spec in value.split(","):
                        name = requirement_name(spec)
                        if name:
                            packages.add(name)
                    tool_from_option = tool_from_option or option == "--from"
                index += 1 if inline else 2
                continue
            if token.startswith("-"):
                index += 1
                continue
            if not tool_from_option:
                name = requirement_name(token)
                if name:
                    packages.add(name)
            break
    return packages


def declared_dependencies(root: Path) -> dict[str, set[str]]:
    """Every dependency this repository declares, as name -> scopes."""
    found = manifest_dependencies((root / "pyproject.toml").read_text(encoding="utf-8"))
    for workflow in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        for name in uvx_packages(workflow.read_text(encoding="utf-8")):
            found.setdefault(name, set()).add("ci")
    return found


# ------------------------------------------------------------------ records


@dataclass
class Records:
    """The record directory as read, with whatever could not be read."""

    records: dict[str, dict[str, Any]] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)


def grandfathered_names(text: str) -> set[str]:
    """The names on a grandfather list, comments and blank lines ignored."""
    names = set()
    for line in text.splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            names.add(normalise(entry))
    return names


def read_records(root: Path) -> Records:
    """Every ``<name>.yml`` record, keyed by the normalised name."""
    result = Records()
    for path in sorted((root / RECORD_DIR).glob("*.yml")):
        relative = path.relative_to(root).as_posix()
        try:
            record = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            result.problems.append(f"{relative}: not valid YAML ({exc.__class__.__name__}).")
            continue
        if not isinstance(record, dict):
            result.problems.append(f"{relative}: a record is a mapping of fields.")
            continue
        name = normalise(str(record.get("name") or ""))
        if name != path.stem:
            result.problems.append(
                f"{relative}: the file is named after the package; "
                f"expected {name or '<name>'}.yml."
            )
            continue
        result.records[name] = record
    return result


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def record_problems(root: Path, name: str, record: dict[str, Any], scopes: set[str]) -> list[str]:
    """Everything wrong with one record of a declared dependency."""
    where = (RECORD_DIR / f"{name}.yml").as_posix()
    problems = [
        f"{where}: '{key}' is missing or empty."
        for key in REQUIRED_FIELDS
        if not _text(record.get(key))
    ]

    status = record.get("status")
    if status not in STATES:
        problems.append(f"{where}: 'status' is one of {', '.join(STATES)}.")
    elif status != "approved":
        problems.append(
            f"{where}: {name} is '{status}'. A maintainer has to review and approve "
            "it before the package may be used."
        )
    elif not _text(record.get("approved_by")):
        problems.append(f"{where}: an approved record names who approved it in 'approved_by'.")

    recorded_scopes = record.get("scopes")
    if not isinstance(recorded_scopes, list) or set(map(str, recorded_scopes)) != scopes:
        problems.append(
            f"{where}: 'scopes' must be exactly where {name} is declared: "
            f"{', '.join(sorted(scopes))}. A wider scope needs a fresh look."
        )

    review = record.get("review")
    if not isinstance(review, dict):
        problems.append(f"{where}: 'review' is missing.")
    else:
        problems += [
            f"{where}: review.{key} is missing or empty."
            for key in REVIEW_FIELDS
            if not _text(review.get(key))
        ]
        reviewed_on = _text(review.get("reviewed_on"))
        if reviewed_on:
            try:
                datetime.date.fromisoformat(reviewed_on)
            except ValueError:
                problems.append(f"{where}: review.reviewed_on is a YYYY-MM-DD date.")

    problems += _test_problems(root, where, record)
    return problems


def _test_problems(root: Path, where: str, record: dict[str, Any]) -> list[str]:
    tests = record.get("tests")
    if not isinstance(tests, list) or not tests:
        return [f"{where}: 'tests' lists the tests that exercise the package."]
    problems = []
    mentioned = False
    import_name = _text(record.get("import_name"))
    pattern = re.compile(rf"\b{re.escape(import_name)}\b") if import_name else None
    for entry in tests:
        relative = str(entry)
        path = (root / relative).resolve()
        if not relative.startswith(TEST_ROOTS) or root.resolve() not in path.parents:
            problems.append(f"{where}: test {relative!r} is not under {' or '.join(TEST_ROOTS)}.")
            continue
        if not path.is_file():
            problems.append(f"{where}: test {relative} does not exist.")
            continue
        if pattern and pattern.search(path.read_text(encoding="utf-8")):
            mentioned = True
    if not problems and not mentioned:
        problems.append(
            f"{where}: none of the listed tests mentions {import_name!r}, so none "
            "of them is shown to exercise the package."
        )
    return problems


def check(root: Path) -> list[str]:
    """Every way the repository falls short of the dependency policy."""
    declared = declared_dependencies(root)
    loaded = read_records(root)
    grandfather_path = root / GRANDFATHERED
    grandfathered = (
        grandfathered_names(grandfather_path.read_text(encoding="utf-8"))
        if grandfather_path.is_file()
        else set()
    )

    problems = list(loaded.problems)
    for name in sorted(declared):
        record = loaded.records.get(name)
        if record is None:
            if name not in grandfathered:
                problems.append(
                    f"{name} ({', '.join(sorted(declared[name]))}) has no record in "
                    f"{RECORD_DIR.as_posix()}/{name}.yml. A new dependency is justified, "
                    "tested and security-reviewed before it is used - see "
                    f"{RECORD_DIR.as_posix()}/README.md."
                )
            continue
        problems += record_problems(root, name, record, declared[name])
        if name in grandfathered and record.get("status") == "approved":
            problems.append(
                f"{name} now has an approved record; remove it from {GRANDFATHERED.as_posix()}."
            )

    for name in sorted(set(loaded.records) - set(declared)):
        problems.append(
            f"{RECORD_DIR.as_posix()}/{name}.yml describes a package nothing declares; delete it."
        )
    for name in sorted(grandfathered - set(declared)):
        problems.append(
            f"{name} is no longer declared; remove it from {GRANDFATHERED.as_posix()}."
        )
    return problems


def grandfather_growth(
    base_text: str | None,
    head_text: str,
    base_dependencies: set[str],
) -> list[str]:
    """Names entries that are new dependencies, rather than an initial inventory.

    The first pull request that introduces this policy necessarily introduces
    the whole grandfather list as well. In that one case a name is legitimate
    only when the base commit already declared it; this keeps a new dependency
    from being smuggled into the initial inventory. Once the file exists on
    the base, it may only shrink.
    """
    previous = grandfathered_names(base_text or "")
    permitted = base_dependencies if base_text is None else set()
    added = sorted(grandfathered_names(head_text) - previous - permitted)
    return [
        f"{name} was added to {GRANDFATHERED.as_posix()}. That list only holds the "
        "dependencies that predate the policy; a new one needs a reviewed record."
        for name in added
    ]


def _file_at(root: Path, commit: str, path: Path) -> str | None:
    result = subprocess.run(  # nosec B603 B607 - fixed argv, no shell, git from PATH
        ["git", "show", f"{commit}:{path.as_posix()}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def declared_dependencies_at(root: Path, commit: str) -> set[str]:
    """The dependency names declared by ``commit``, including workflow tools."""
    pyproject = _file_at(root, commit, Path("pyproject.toml"))
    if pyproject is None:
        return set()
    declared = manifest_dependencies(pyproject)
    listing = subprocess.run(  # nosec B603 B607 - fixed argv, no shell, git from PATH
        ["git", "ls-tree", "-r", "--name-only", commit, "--", ".github/workflows"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if listing.returncode != 0:
        return set()
    for relative in listing.stdout.splitlines():
        if not relative.endswith((".yml", ".yaml")):
            continue
        workflow = _file_at(root, commit, Path(relative))
        if workflow is None:
            continue
        for name in uvx_packages(workflow):
            declared.setdefault(name, set()).add("ci")
    return set(declared)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Check the dependency policy (ADR 0060).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail on any policy violation. The default.")
    mode.add_argument("--list", action="store_true", help="Print every dependency and its standing.")
    parser.add_argument("--base", help="Also refuse a grandfather list that grew since this commit.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root

    if args.list:
        declared = declared_dependencies(root)
        records = read_records(root).records
        grandfather_path = root / GRANDFATHERED
        grandfathered = (
            grandfathered_names(grandfather_path.read_text(encoding="utf-8"))
            if grandfather_path.is_file()
            else set()
        )
        for name in sorted(declared):
            if name in records:
                standing = str(records[name].get("status"))
            elif name in grandfathered:
                standing = "grandfathered"
            else:
                standing = "NO RECORD"
            print(f"{name:28} {standing:14} {', '.join(sorted(declared[name]))}")
        return 0

    problems = check(root)
    if args.base:
        head = (root / GRANDFATHERED).read_text(encoding="utf-8") if (root / GRANDFATHERED).is_file() else ""
        base = _file_at(root, args.base, GRANDFATHERED)
        problems += grandfather_growth(
            base,
            head,
            declared_dependencies_at(root, args.base),
        )

    for problem in problems:
        print(f"::error::{problem}")
    if not problems:
        print("Every dependency is justified, tested and reviewed, or predates the policy.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
