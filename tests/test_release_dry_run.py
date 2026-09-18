"""The release rehearsal and the release agree, and the release publishes last.

`publish-pypi.yml` once uploaded to PyPI before building the .deb, the .rpm
and the web bundle. A failure in any of those left a version on PyPI with no
tag and no GitHub release - and PyPI never takes a version back. The order is
now build everything, then publish, then tag; `release-dry-run.yml` builds the
same things on the pull request. See adr/0045. Both properties are invisible in
a green pipeline, so they are asserted here.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def _steps(name: str) -> list[dict]:
    """Every step of every job in one workflow, in order."""
    document = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    return [step for job in document["jobs"].values() for step in job.get("steps", [])]


def _index(steps: list[dict], name: str) -> int:
    """The position of the step with this name."""
    names = [step.get("name") for step in steps]
    assert name in names, f"no step named {name!r}"
    return names.index(name)


def test_pypi_is_published_only_after_every_other_artifact_is_built():
    """A build failure after the upload leaves a version PyPI will never take back."""
    steps = _steps("publish-pypi.yml")
    publish = _index(steps, "Publish to PyPI")

    for build in (
        "Build package",
        "Build the .deb and the .rpm",
        "Attest the distribution packages",
        "Build the web application bundle",
        "Attest the web application bundle",
        "Build the Docker setup wizard",
        "Attest the Docker setup wizard",
    ):
        assert _index(steps, build) < publish, f"{build!r} runs after the upload"
    assert publish < _index(steps, "Create Git tag") < _index(steps, "Create GitHub release")


def test_a_repeated_release_skips_files_pypi_already_holds():
    """Without --check-url, a retry after a failed tag step fails on "File already exists"."""
    steps = _steps("publish-pypi.yml")
    publish = steps[_index(steps, "Publish to PyPI")]

    assert "--check-url https://pypi.org/simple/" in publish["run"]


def test_the_dry_run_builds_what_the_release_builds():
    """A rehearsal that skips a step cannot catch that step breaking."""
    rehearsed = {step.get("name") for step in _steps("release-dry-run.yml")}

    for name in (
        "Build package",
        "Install nfpm",
        "Build the .deb and the .rpm",
        "Build the web application bundle",
        "Build the Docker setup wizard",
    ):
        assert name in rehearsed


def test_the_dry_run_installs_the_same_nfpm_as_the_release():
    """Two pins that drift apart rehearse a build the release never runs."""
    def nfpm(name: str) -> dict:
        steps = _steps(name)
        return steps[_index(steps, "Install nfpm")]["env"]

    assert nfpm("release-dry-run.yml") == nfpm("publish-pypi.yml")


def test_the_dry_run_can_publish_nothing():
    """It runs on every pull request, so it holds no write token and no publishing step."""
    text = (WORKFLOWS / "release-dry-run.yml").read_text(encoding="utf-8")
    document = yaml.safe_load(text)

    assert document["permissions"] == {"contents": "read"}
    assert all("permissions" not in job for job in document["jobs"].values())
    for forbidden in ("uv publish", "git push", "gh release", "push: true", "actions/attest"):
        assert forbidden not in text
    assert "push: false" in text



def test_the_release_attaches_the_wizard_it_built():
    """A wizard built and attested but never uploaded leaves the documented download a 404."""
    steps = _steps("publish-pypi.yml")
    release = steps[_index(steps, "Create GitHub release")]

    assert "wizard-release/*" in release["run"]


def _condition(step: dict) -> str:
    return step.get("if", "")


def test_a_tag_without_a_published_release_is_resumed_not_skipped():
    """v1.25.0 was tagged, then its release upload failed; every re-run saw the tag and did nothing."""
    steps = _steps("publish-pypi.yml")
    state = steps[_index(steps, "Check what this version still needs")]["run"]

    assert "gh release view" in state
    assert "mode=resume" in state
    assert "mode=done" in state
    for name in ("Build package", "Build the Docker setup wizard", "Publish to PyPI", "Create GitHub release"):
        assert _condition(steps[_index(steps, name)]) == "steps.state.outputs.mode != 'done'", name


def test_a_resumed_release_builds_the_tag_and_leaves_the_notes_alone():
    """Main may have moved on since the tag, and its notes were already committed."""
    steps = _steps("publish-pypi.yml")
    checkout = _index(steps, "Check out the tagged release")

    assert _condition(steps[checkout]) == "steps.state.outputs.mode == 'resume'"
    assert checkout < _index(steps, "Build package")
    for name in (
        "Refresh the OpenCloud release schedule",
        "Build the static frontend search index",
        "Update CHANGELOG.md and RELEASE.md",
        "Commit release notes",
        "Create Git tag",
    ):
        assert _condition(steps[_index(steps, name)]) == "steps.state.outputs.mode == 'release'", name


def test_the_release_is_published_only_once_every_asset_is_on_it():
    """One failed upload must leave a draft to finish, not a latest release missing the wizard."""
    steps = _steps("publish-pypi.yml")
    run = steps[_index(steps, "Create GitHub release")]["run"]

    assert "--draft" in run
    assert "gh release upload" in run
    assert run.index("gh release upload") < run.index("--draft=false")


def test_the_release_can_be_resumed_by_hand_but_never_twice_at_once():
    document = yaml.safe_load((WORKFLOWS / "publish-pypi.yml").read_text(encoding="utf-8"))

    # YAML 1.1 reads the bare key `on` as the boolean true.
    assert "workflow_dispatch" in document[True]
    assert document["concurrency"] == {"group": "release", "cancel-in-progress": False}
