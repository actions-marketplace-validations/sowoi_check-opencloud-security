# ADR 0049: The Docker wizard is downloaded from a release, and knows its version

- Status: Accepted
- Date: 2026-09-13

## Context

`docker/setup-wizard.py` is documented as one file to download onto a host
that has Docker and nothing else. Every guide fetched it from
`raw.githubusercontent.com/.../main/docker/setup-wizard.py`: whatever had been
merged last, with nothing to check the download against and no way to tell
afterwards which version had written a deployment. The script could not say
either - it carried no version, and pyproject.toml, the only place one is
written, is not beside a downloaded copy.

A literal version in the script would answer that and break the rule that
`pyproject.toml` is the only place a version is written by hand, which exists
because literals drifted before.

## Decision

**A release attaches the wizard, and the documentation downloads that copy.**
`scripts/build_wizard_release.py` writes `setup-wizard.py` and
`setup-wizard.py.sha256` into `wizard-release/`; `publish-pypi.yml` builds and
attests them before publishing and uploads them with the other assets, and
`release-dry-run.yml` builds them on the pull request. The guides fetch
`releases/latest/download/setup-wizard.py` and check the checksum.

**The version is stamped, never written.** The repository copy carries
`RELEASE_VERSION = ""`, and a test fails if it ever holds a number. The build
script replaces exactly that line with the version in `pyproject.toml`, and
fails when the line is not there. `--version` prints the stamp; a checkout or
the web bundle, which have `pyproject.toml` beside the script, read it from
there instead - only from a `[project]` table naming this project; anything
else says the version is unknown rather than guessing.

## Consequences

- A download is a reviewed release, verifiable by checksum and by
  `gh attestation verify`, and reports which release it is.
- Between a merge that changes the wizard and the next release, the documented
  download is the previous release's wizard. That is the point.
- The first release carrying this is the first with the asset: until then,
  `releases/latest/download/setup-wizard.py` answers 404.
- The documentation links the wizard prints point at the release tag it came
  from rather than at `main`.

## Alternatives considered

- **Keep downloading from `main`, add a checksum file there.** A checksum
  committed beside the file it describes proves nothing about who changed both.
- **A generated literal committed on every bump, checked by CI.** A second
  place the version is written, and a bump pull request that fails until
  somebody remembers to regenerate it.
- **Derive the version from `git describe`.** A downloaded file has no
  repository to describe.
