"""The Docker setup wizard a release attaches, and the version it reports.

The wizard is downloaded as one file. The copy a release attaches has to say
which release it is and come with something to check it against; the copy in
the repository has to keep pyproject.toml the only place a version is written.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import subprocess  # nosec B404 - runs the built wizard with --version
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = _load(ROOT / "scripts" / "build_wizard_release.py", "build_wizard_release")


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match
    return match.group(1)


def test_the_repository_copy_writes_no_version_of_its_own() -> None:
    """A literal in the source is a second place the version is written, and drifts."""
    source = (ROOT / "docker" / "setup-wizard.py").read_text(encoding="utf-8")

    assert re.search(r'^RELEASE_VERSION = ""$', source, re.MULTILINE)
    assert not re.search(r'^RELEASE_VERSION = "\d', source, re.MULTILINE)


def test_the_release_copy_names_its_release_and_carries_a_checksum(tmp_path: Path) -> None:
    """Without a pyproject.toml beside it, the stamp is the only way it knows."""
    wizard = builder.build(tmp_path)

    # Run from a directory of its own, as a download is.
    alone = tmp_path / "alone"
    alone.mkdir()
    copy = alone / "setup-wizard.py"
    copy.write_bytes(wizard.read_bytes())
    printed = subprocess.run(  # nosec B603 - the file just built, fixed arguments
        [sys.executable, str(copy), "--version"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert printed.strip() == f"setup-wizard.py {_pyproject_version()}"

    digest, name = (tmp_path / "setup-wizard.py.sha256").read_text(encoding="utf-8").split()
    assert name == "setup-wizard.py"
    assert digest == hashlib.sha256(wizard.read_bytes()).hexdigest()
    assert wizard.stat().st_mode & 0o111


def test_an_unstamped_download_says_it_does_not_know(tmp_path: Path) -> None:
    """Guessing a version is worse than admitting there is none to report."""
    copy = tmp_path / "setup-wizard.py"
    copy.write_bytes((ROOT / "docker" / "setup-wizard.py").read_bytes())

    printed = subprocess.run(  # nosec B603 - a copy of the repository file, fixed arguments
        [sys.executable, str(copy), "--version"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert "version unknown" in printed
    assert _pyproject_version() not in printed


def test_a_source_without_the_marker_line_fails_the_build() -> None:
    """A renamed constant must not publish a wizard that reports no version."""
    with pytest.raises(SystemExit):
        builder.stamp("VERSION = ''\n", "1.2.3")
    with pytest.raises(SystemExit):
        builder.stamp('RELEASE_VERSION = ""\n', "not a version")
    assert 'RELEASE_VERSION = "1.2.3"' in builder.stamp('RELEASE_VERSION = ""\n', "1.2.3")
