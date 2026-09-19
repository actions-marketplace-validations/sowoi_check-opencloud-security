"""The manual mutation-testing setup: mutmut, its config, the skill and the agent.

mutmut itself is never imported here - it is not installed with the test
group, and a run takes minutes. These tests keep the pieces the /mutation-test
skill relies on consistent with one another.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def _table(name: str) -> str:
    """The text of one top-level TOML table (3.10 has no tomllib)."""
    match = re.search(rf"^\[{re.escape(name)}\]\n(.*?)(?=^\[)", PYPROJECT, re.MULTILINE | re.DOTALL)
    assert match, f"[{name}] missing from pyproject.toml"
    return match.group(1)


def _array(table: str, key: str) -> list[str]:
    match = re.search(rf"^{key} = \[(.*?)\]", table, re.MULTILINE | re.DOTALL)
    assert match, f"{key} missing"
    return re.findall(r'"([^"]+)"', re.sub(r"#.*", "", match.group(1)))


def test_mutmut_lives_only_in_its_own_group():
    """CI and a plain `uv sync` must never install the mutation tool."""
    groups = _table("dependency-groups")

    assert any(entry.startswith("mutmut") for entry in _array(groups, "mutation"))
    assert not any(entry.startswith("mutmut") for entry in _array(groups, "test"))
    assert "mutmut" not in _table("project")


def test_mutmut_has_a_dependency_record():
    """ADR 0060: no package without a reviewed record."""
    record = (ROOT / "security/dependencies/mutmut.yml").read_text(encoding="utf-8")

    assert re.search(r"^name: mutmut$", record, re.MULTILINE)
    assert re.search(r"^  - group:mutation$", record, re.MULTILINE)


def test_every_mutmut_test_file_exists_and_runs_in_process():
    """A missing file fails the run; a subprocess test cannot see a mutant."""
    files = _array(_table("tool.mutmut"), "pytest_add_cli_args_test_selection")

    assert files
    for name in files:
        assert (ROOT / name).is_file(), name
        assert "e2e" not in name and "browser" not in name, name


def test_mutmut_only_mutates_the_plugin_and_the_scanner():
    """The web application's verdicts come from these two; nothing else is in scope."""
    assert set(_array(_table("tool.mutmut"), "source_paths")) == {
        "check_opencloud_security.py",
        "opencloud_local_scan/",
    }


def test_the_mutmut_working_copy_is_ignored():
    """mutmut writes a full copy of the tree to mutants/; it must never be committed."""
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "mutants/" in ignored


def test_the_skill_runs_in_the_read_only_agent():
    """/mutation-test forks into mutation-tester, which has no editing tools."""
    skill = (ROOT / ".claude/skills/mutation-test/SKILL.md").read_text(encoding="utf-8")
    agent = (ROOT / ".claude/agents/mutation-tester.md").read_text(encoding="utf-8")

    assert re.search(r"^agent: mutation-tester$", skill, re.MULTILINE)
    assert re.search(r"^context: fork$", skill, re.MULTILINE)
    tools = re.search(r"^tools: (.*)$", agent, re.MULTILINE)
    assert tools
    assert not {"Edit", "Write", "NotebookEdit"} & {t.strip() for t in tools.group(1).split(",")}
    assert "uv run --group test --group mutation mutmut" in agent
