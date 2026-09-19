#!/usr/bin/env python3
"""Run the existing Claude hook scripts with Codex hook input.

The Claude scripts already consume the shared JSON fields used by Codex
(``tool_name``, ``tool_input`` and ``cwd``). This adapter keeps the original
scripts authoritative while translating Claude's conditional hook groups into
Codex's event/matcher model.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B603 - the script paths are fixed below
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLAUDE_HOOKS = ROOT / ".claude" / "hooks"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "hook",
        choices=(
            "guard-bash",
            "guard-branch",
            "privacy-pre-tool-use",
            "changelog-docs-gate",
            "guard-edit",
            "stop-checks",
            "privacy-stop",
        ),
    )
    arguments = parser.parse_args()
    payload = sys.stdin.buffer.read()
    try:
        event = json.loads(payload or b"{}")
    except json.JSONDecodeError:
        event = {}
    command = (event.get("tool_input") or {}).get("command", "")
    tool_name = event.get("tool_name", "")

    conditional = {
        "guard-branch": command.lstrip().startswith("git "),
        "privacy-pre-tool-use": command.lstrip().startswith(("git ", "gh ")),
        "changelog-docs-gate": command.lstrip().startswith("git "),
        "guard-edit": tool_name in {"apply_patch", "Edit", "Write"},
    }
    if arguments.hook in conditional and not conditional[arguments.hook]:
        return 0

    script_name = {
        "guard-bash": "guard_bash.py",
        "guard-branch": "guard_branch.py",
        "privacy-pre-tool-use": "privacy_guard.py",
        "changelog-docs-gate": "changelog_docs_gate.py",
        "guard-edit": "guard_edit.py",
        "stop-checks": "stop_checks.py",
        "privacy-stop": "privacy_guard.py",
    }[arguments.hook]
    args = [sys.executable, str(CLAUDE_HOOKS / script_name)]
    if arguments.hook == "privacy-pre-tool-use":
        args.append("pre-tool-use")
    elif arguments.hook == "privacy-stop":
        args.append("stop")
    environment = os.environ.copy()
    environment.setdefault("CLAUDE_PROJECT_DIR", str(ROOT))
    result = subprocess.run(  # nosec B603 - fixed repository hook target
        args,
        cwd=ROOT,
        input=payload,
        capture_output=True,
        check=False,
        env=environment,
    )
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
