#!/usr/bin/env python3
"""Stop hook: run the fast generator --check guards CI runs, when their sources changed.

A forgotten regeneration (frontend documentation, embedded wizard blueprints)
or a ### Security entry without an advisory record blocks the stop and sends
the failure back to the model. A stale search index only warns, because CI
rebuilds it on the pull request (ADR 0050). All checks together take ~1s.

The checks need the project's dependencies (markdown, yaml, the repo's own
packages), so they run in the project's virtual environment - `.venv`, else
`uv run --frozen` - and a check that cannot import what it needs is reported
as skipped, never as a stale file.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404
import sys

_MISSING_DEPENDENCY = ("ModuleNotFoundError", "ImportError")

# (label, command, path prefixes that trigger it, blocking)
_CHECKS = (
    ("Frontend documentation", ["scripts/build_frontend_documentation.py", "--check"],
     ("README.md", "docs/", "opencloud_local_scan/README.md", "webapp/README.md",
      "frontend/templates/docs/", "frontend/templates/admin-docs/", "scripts/build_frontend_documentation.py"),
     True),
    ("Embedded wizard blueprints", ["scripts/embed_wizard_blueprints.py", "--check"],
     ("authentik/blueprints/", "docker/setup-wizard.py", "scripts/embed_wizard_blueprints.py"),
     True),
    ("Security advisory records", ["scripts/security_advisories.py", "--check"],
     ("CHANGELOG.md", "security/advisories/", "scripts/security_advisories.py"),
     True),
    ("Search index", ["scripts/build_search_index.py", "--check"],
     ("README.md", "docs/", "frontend/", "webapp/locales/", "opencloud_local_scan/README.md",
      "pyproject.toml", "scripts/build_search_index.py"),
     False),
)


def _changed_paths(root: str) -> list[str]:
    result = subprocess.run(  # nosec B603 B607
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    paths = []
    for line in result.stdout.splitlines():
        entry = line[3:]
        paths.extend(part.strip().strip('"') for part in entry.split(" -> "))
    return paths


def _interpreter(root: str) -> list[str]:
    """The project's Python: .venv, else uv, else whatever runs this hook."""
    for candidate in (os.path.join(root, ".venv", "bin", "python"),
                      os.path.join(root, ".venv", "Scripts", "python.exe")):
        if os.access(candidate, os.X_OK):
            return [candidate]
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "--frozen", "--quiet", "python"]
    return [sys.executable]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if payload.get("stop_hook_active"):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    changed = _changed_paths(root)
    if not changed:
        return 0

    python = _interpreter(root)
    failures, warnings = [], []
    for label, args, prefixes, blocking in _CHECKS:
        if not any(path.startswith(prefixes) for path in changed):
            continue
        try:
            result = subprocess.run(  # nosec B603
                [*python, *args], cwd=root, capture_output=True, text=True, check=False, timeout=90,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            warnings.append(f"{label} skipped: {error}")
            continue
        if result.returncode == 0:
            continue
        output = (result.stdout + result.stderr).strip().splitlines()[-15:]
        if any(marker in line for line in output for marker in _MISSING_DEPENDENCY):
            warnings.append(f"{label} skipped: the project environment is missing a dependency ({output[-1]})")
            continue
        message = "{} failed: python {}\n{}".format(label, " ".join(args), "\n".join(output))
        (failures if blocking else warnings).append(message)

    response = {}
    if failures:
        response["decision"] = "block"
        response["reason"] = (
            "Generated-file guards failed for the uncommitted changes. Regenerate "
            "(run the command without --check, or write the missing security/advisories record "
            "with /security-fix-record) before finishing:\n\n" + "\n\n".join(failures)
        )
    if warnings:
        response["systemMessage"] = "\n".join(
            w.splitlines()[0] if "skipped" in w.splitlines()[0] else w.splitlines()[0] + " (warning only - CI rebuilds it)"
            for w in warnings
        )
    if response:
        json.dump(response, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
