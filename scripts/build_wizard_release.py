#!/usr/bin/env python3
"""
Build the Docker setup wizard as a GitHub release attaches it.

    python scripts/build_wizard_release.py
    python scripts/build_wizard_release.py --output-dir wizard-release

The wizard is one file an operator downloads onto a host that has Docker and
nothing else. Downloading it from ``main`` hands them whatever was merged last
and gives them nothing to check it against, so a release attaches its own copy
instead, with two differences from the file in the repository:

* ``RELEASE_VERSION`` is stamped with the version in ``pyproject.toml``, so
  ``setup-wizard.py --version`` names the release it came from without a
  pyproject.toml beside it. The repository copy keeps the line empty -
  pyproject.toml stays the only place a version is written by hand;
* ``setup-wizard.py.sha256`` sits beside it, in the format ``sha256sum
  --check`` reads, and the release workflow attests the file as well.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIZARD = ROOT / "docker" / "setup-wizard.py"
NAME = "setup-wizard.py"

# The exact line the wizard carries, so that a reformatted or renamed constant
# fails the build rather than publishing a copy that reports no version.
UNSTAMPED = re.compile(r'^RELEASE_VERSION = ""$', re.MULTILINE)


def _version() -> str:
    """The version in pyproject.toml, which is the only place it is written."""
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("pyproject.toml has no version")


def stamp(source: str, version: str) -> str:
    """The wizard's source with its release version filled in."""
    if not re.fullmatch(r"\d+\.\d+\.\d+([.-]?[0-9A-Za-z.]+)?", version):
        raise SystemExit(f"not a release version: {version!r}")
    stamped, count = UNSTAMPED.subn(f'RELEASE_VERSION = "{version}"', source)
    if count != 1:
        raise SystemExit(
            f"expected exactly one empty RELEASE_VERSION line in {WIZARD}, found {count}"
        )
    return stamped


def build(output_dir: Path) -> Path:
    """Write the stamped wizard and its checksum, and return the wizard's path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / NAME
    target.write_text(stamp(WIZARD.read_text(encoding="utf-8"), _version()), encoding="utf-8")
    target.chmod(0o755)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (output_dir / f"{NAME}.sha256").write_text(f"{digest}  {NAME}\n", encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "wizard-release",
        help="where to write the wizard and its checksum",
    )
    arguments = parser.parse_args(argv)
    print(build(arguments.output_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
