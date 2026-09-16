"""Tests for scripts/check_dependencies.py, the dependency policy (ADR 0060).

A new Python dependency is justified, tested and security-reviewed before it
is used. These tests hold the guard to refusing every way around that, and to
staying quiet for a record that does everything asked of it.
"""

from __future__ import annotations

import importlib.util
import subprocess  # nosec B404 - builds a throwaway repository with fixed argv
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "check_dependencies", REPO_ROOT / "scripts" / "check_dependencies.py"
)
assert SPEC and SPEC.loader
script = importlib.util.module_from_spec(SPEC)
sys.modules["check_dependencies"] = script
SPEC.loader.exec_module(script)

PYPROJECT = """[project]
name = "example"
version = "1.0.0"
dependencies = [
    "requests>=2",  # a comment with ] in it
]

[project.optional-dependencies]
web = ["redis[hiredis]>=5,<6", 'Example_Package.Two>=1']

[dependency-groups]
test = [
    "pytest>=9",
    {include-group = "web"},
]

[tool.other]
dependencies = ["not-a-dependency"]

[build-system]
requires = ["hatchling"]
"""

WORKFLOW = """jobs:
  lint:
    steps:
      # uvx commented-out-tool would be ignored
      - run: uvx ruff@0.9.0 check
      - run: >
          uvx --with bandit-sarif-formatter
          bandit --recursive .
      - run: |
          uvx --from cyclonedx-bom cyclonedx-py environment .venv \\
            --of JSON
      - run: uvx --python 3.12 zizmor==1.30.1 .github/workflows
"""


def _repo(tmp_path: Path, pyproject: str = PYPROJECT, workflow: str = "") -> Path:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / script.RECORD_DIR).mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    if workflow:
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text(workflow, encoding="utf-8")
    return tmp_path


def _grandfather(root: Path, *names: str) -> None:
    (root / script.GRANDFATHERED).write_text("# header\n" + "\n".join(names) + "\n", encoding="utf-8")


def _record(name: str = "requests", **overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": name,
        "import_name": "requests",
        "status": "approved",
        "approved_by": "the maintainer",
        "scopes": ["runtime"],
        "reviewed_version": "2.34.2",
        "justification": "HTTP with sessions and retries.",
        "alternatives_considered": "urllib: no connection pooling.",
        "tests": ["tests/test_http.py"],
        "review": {
            "reviewer": "the maintainer",
            "reviewed_on": "2026-09-16",
            "known_vulnerabilities": "pip-audit: none.",
            "maintenance": "PSF, monthly releases.",
            "provenance": "Trusted publishing.",
            "install_time": "Pure-Python wheel.",
            "runtime_network": "Only what it is asked to fetch.",
            "native_code": "None.",
            "transitive_dependencies": "certifi, idna, urllib3, charset-normalizer.",
            "license": "Apache-2.0.",
        },
    }
    record.update(overrides)
    return record


def _write(root: Path, record: dict[str, Any], filename: str | None = None) -> None:
    name = filename or f"{script.normalise(record['name'])}.yml"
    (root / script.RECORD_DIR / name).write_text(yaml.safe_dump(record), encoding="utf-8")


def _approved_repo(tmp_path: Path) -> Path:
    """A repository whose only unrecorded dependency is `requests`, fully recorded."""
    root = _repo(tmp_path)
    _grandfather(root, "redis", "example-package-two", "pytest", "hatchling")
    (root / "tests" / "test_http.py").write_text("import requests\n", encoding="utf-8")
    _write(root, _record())
    return root


# ------------------------------------------------------------ the manifest


def test_the_manifest_scanner_reads_every_scope_and_nothing_else():
    """Extras in brackets, comments and inline tables must not confuse it."""
    assert script.manifest_dependencies(PYPROJECT) == {
        "requests": {"runtime"},
        "redis": {"extra:web"},
        "example-package-two": {"extra:web"},
        "pytest": {"group:test"},
        "hatchling": {"build"},
    }


def test_the_manifest_scanner_agrees_with_tomllib_on_this_repository():
    """The real pyproject.toml is the one that matters; 3.10 has no tomllib to lean on."""
    tomllib = pytest.importorskip("tomllib")
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    parsed = tomllib.loads(text)
    expected: dict[str, set[str]] = {}

    def add(requirements, scope):
        for requirement in requirements:
            if isinstance(requirement, str):
                expected.setdefault(script.requirement_name(requirement), set()).add(scope)

    add(parsed["project"].get("dependencies", []), "runtime")
    for key, value in parsed["project"].get("optional-dependencies", {}).items():
        add(value, f"extra:{key}")
    for key, value in parsed.get("dependency-groups", {}).items():
        add(value, f"group:{key}")
    add(parsed.get("build-system", {}).get("requires", []), "build")

    assert script.manifest_dependencies(text) == expected


def test_uvx_tools_are_found_with_their_options_and_versions():
    """`--with` adds a package, `--from` names the package instead of the command."""
    assert script.uvx_packages(WORKFLOW) == {
        "ruff",
        "bandit-sarif-formatter",
        "bandit",
        "cyclonedx-bom",
        "zizmor",
    }


def test_a_commented_uvx_line_is_not_a_dependency():
    """A comment is not something CI runs."""
    assert script.uvx_packages("# run uvx something-else later\n") == set()


def test_names_are_compared_the_way_pypi_compares_them():
    """PyYAML, pyyaml and py_yaml are one package; the record must be found for all."""
    assert script.requirement_name("PyYAML>=6") == "pyyaml"
    assert script.requirement_name("Example_Package.Two[x]>=1") == "example-package-two"


# ------------------------------------------------------------------ the rule


def test_this_repository_satisfies_its_own_policy():
    """The guard CI runs has to pass on the tree it guards."""
    assert script.check(REPO_ROOT) == []


def test_a_complete_approved_record_passes(tmp_path):
    """The positive case: without it every refusal below proves nothing."""
    assert script.check(_approved_repo(tmp_path)) == []


def test_a_new_dependency_without_a_record_is_refused(tmp_path):
    """The whole point of the policy."""
    root = _approved_repo(tmp_path)
    (root / script.RECORD_DIR / "requests.yml").unlink()

    problems = script.check(root)

    assert len(problems) == 1
    assert "requests (runtime) has no record" in problems[0]


def test_a_new_uvx_tool_without_a_record_is_refused(tmp_path):
    """A CI tool runs next to the repository token; it is a dependency too."""
    root = _approved_repo(tmp_path)
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "      - run: uvx some-linter check\n", encoding="utf-8"
    )

    assert any("some-linter (ci) has no record" in p for p in script.check(root))


def test_a_proposed_record_is_not_yet_permission(tmp_path):
    """A drafted review is not an approval; only a maintainer turns it into one."""
    root = _approved_repo(tmp_path)
    _write(root, _record(status="proposed", approved_by=""))

    problems = script.check(root)

    assert any("'proposed'" in p and "approve" in p for p in problems)


def test_an_approval_names_who_approved_it(tmp_path):
    """An approval nobody signed is indistinguishable from none."""
    root = _approved_repo(tmp_path)
    _write(root, _record(approved_by=""))

    assert any("approved_by" in p for p in script.check(root))


@pytest.mark.parametrize("missing", ["justification", "alternatives_considered", "reviewed_version"])
def test_a_record_without_its_justification_is_refused(tmp_path, missing):
    """Every field is a question; an empty one is a question skipped."""
    root = _approved_repo(tmp_path)
    _write(root, _record(**{missing: "  "}))

    assert any(f"'{missing}' is missing" in p for p in script.check(root))


@pytest.mark.parametrize("missing", script.REVIEW_FIELDS)
def test_a_record_without_every_review_answer_is_refused(tmp_path, missing):
    """A security review that skipped a question has not answered it."""
    root = _approved_repo(tmp_path)
    record = _record()
    del record["review"][missing]
    _write(root, record)

    assert any(f"review.{missing}" in p for p in script.check(root))


def test_a_review_date_must_be_a_date(tmp_path):
    """"Last week" cannot be compared against a release date."""
    root = _approved_repo(tmp_path)
    record = _record()
    record["review"]["reviewed_on"] = "last week"
    _write(root, record)

    assert any("reviewed_on is a YYYY-MM-DD" in p for p in script.check(root))


def test_a_record_without_tests_is_refused(tmp_path):
    """Untested is not allowed, however good the justification."""
    root = _approved_repo(tmp_path)
    _write(root, _record(tests=[]))

    assert any("'tests' lists" in p for p in script.check(root))


def test_a_test_that_does_not_exist_is_refused(tmp_path):
    """A path nobody created is a claim, not a test."""
    root = _approved_repo(tmp_path)
    _write(root, _record(tests=["tests/test_missing.py"]))

    assert any("does not exist" in p for p in script.check(root))


def test_a_test_that_never_mentions_the_package_is_refused(tmp_path):
    """A test that does not touch the package does not show it works."""
    root = _approved_repo(tmp_path)
    (root / "tests" / "test_http.py").write_text("import json\n", encoding="utf-8")

    assert any("none of the listed tests mentions 'requests'" in p for p in script.check(root))


def test_a_test_outside_the_test_roots_is_refused(tmp_path):
    """Pointing at the module itself, or outside the repository, proves nothing."""
    root = _approved_repo(tmp_path)
    (root / "module.py").write_text("import requests\n", encoding="utf-8")
    _write(root, _record(tests=["module.py", "tests/../../outside.py"]))

    problems = script.check(root)

    assert sum("is not under" in p for p in problems) == 2


def test_a_wider_scope_than_was_reviewed_is_refused(tmp_path):
    """A test-only package promoted to the runtime reaches production; look again."""
    root = _approved_repo(tmp_path)
    _write(root, _record(scopes=["group:test"]))

    assert any("'scopes' must be exactly" in p for p in script.check(root))


def test_a_record_for_an_undeclared_package_is_refused(tmp_path):
    """A stale record says a package is vetted that nobody installs any more."""
    root = _approved_repo(tmp_path)
    _write(root, _record(name="left-behind"))

    assert any("left-behind.yml describes a package nothing declares" in p for p in script.check(root))


def test_a_record_must_be_named_after_its_package(tmp_path):
    """Otherwise one file could quietly stand in for another package."""
    root = _approved_repo(tmp_path)
    _write(root, _record(name="PyYAML"), filename="requests.yml")

    assert any("expected pyyaml.yml" in p for p in script.check(root))


def test_a_record_that_is_not_yaml_is_refused(tmp_path):
    """Unreadable is not the same as approved."""
    root = _approved_repo(tmp_path)
    (root / script.RECORD_DIR / "requests.yml").write_text("name: [unclosed\n", encoding="utf-8")

    problems = script.check(root)

    assert any("not valid YAML" in p for p in problems)
    assert any("requests (runtime) has no record" in p for p in problems)


def test_a_grandfathered_package_needs_no_record(tmp_path):
    """The policy covers new dependencies; the old ones are listed, not blocked."""
    root = _approved_repo(tmp_path)
    (root / script.RECORD_DIR / "requests.yml").unlink()
    _grandfather(root, "redis", "example-package-two", "pytest", "hatchling", "requests")

    assert script.check(root) == []


def test_an_approved_package_leaves_the_grandfather_list(tmp_path):
    """Otherwise the list stops describing what is still unreviewed."""
    root = _approved_repo(tmp_path)
    _grandfather(root, "redis", "example-package-two", "pytest", "hatchling", "requests")

    assert any("remove it from" in p for p in script.check(root))


def test_a_dropped_package_leaves_the_grandfather_list(tmp_path):
    """A stale entry would wave the package back in the day somebody re-adds it."""
    root = _approved_repo(tmp_path)
    _grandfather(root, "redis", "example-package-two", "pytest", "hatchling", "gone-now")

    assert any("gone-now is no longer declared" in p for p in script.check(root))


def test_the_grandfather_list_may_shrink_but_never_grow():
    """Growing it is the way around the policy, so it is refused by name."""
    base = "# header\nrequests\nredis\n"

    declared = {"requests", "redis", "brand-new"}

    assert script.grandfather_growth(base, "requests\n", declared) == []
    assert script.grandfather_growth(base, base, declared) == []
    # Declared on the base is no excuse once the list exists there.
    grown = script.grandfather_growth(base, base + "Brand_New\n", declared)
    assert len(grown) == 1
    assert grown[0].startswith("brand-new was added")


def test_the_first_inventory_may_only_name_what_the_base_already_declared():
    """
    The policy's own pull request brings the whole list; it must not smuggle.

    With no list on the base, a name is accepted only when the base commit
    already declared the package - a dependency added in the same pull
    request is not "predating the policy".
    """
    inventory = "requests\nredis\nsneaked-in\n"

    grown = script.grandfather_growth(None, inventory, {"requests", "redis"})

    assert len(grown) == 1
    assert grown[0].startswith("sneaked-in was added")
    assert script.grandfather_growth(None, "requests\nredis\n", {"requests", "redis"}) == []


def test_the_command_line_compares_the_grandfather_list_with_the_base(tmp_path):
    """The CI invocation, end to end, against a real git history."""
    root = _approved_repo(tmp_path)

    def git(*args: str) -> None:
        subprocess.run(  # nosec B603 B607 - fixed argv
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
            cwd=root,
            check=True,
            capture_output=True,
        )

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "base")

    assert script.main(["--check", "--base", "HEAD", "--root", str(root)]) == 0

    (root / script.RECORD_DIR / "requests.yml").unlink()
    _grandfather(root, "redis", "example-package-two", "pytest", "hatchling", "requests")

    # Passes on its own, which is exactly why the base comparison exists.
    assert script.main(["--check", "--root", str(root)]) == 0
    assert script.main(["--check", "--base", "HEAD", "--root", str(root)]) == 1


def test_the_first_inventory_is_checked_against_the_base_manifest(tmp_path):
    """End to end: the base has no list yet, and one name was never declared there."""
    root = _approved_repo(tmp_path)
    grandfather = root / script.GRANDFATHERED
    inventory = grandfather.read_text(encoding="utf-8")
    grandfather.unlink()

    def git(*args: str) -> None:
        subprocess.run(  # nosec B603 B607 - fixed argv
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
            cwd=root,
            check=True,
            capture_output=True,
        )

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "before the policy")

    grandfather.write_text(inventory, encoding="utf-8")
    assert script.main(["--check", "--base", "HEAD", "--root", str(root)]) == 0

    # A package that arrives together with the list is not grandfathered.
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace('"pytest>=9",', '"pytest>=9",\n    "sneaked-in",'),
        encoding="utf-8",
    )
    grandfather.write_text(inventory + "sneaked-in\n", encoding="utf-8")
    assert script.main(["--check", "--root", str(root)]) == 0
    assert script.main(["--check", "--base", "HEAD", "--root", str(root)]) == 1
