# ADR 0048: RELEASE.md is written by the release, not by a pull request

- Status: Accepted
- Date: 2026-09-13
- Supersedes: the `RELEASE.md` requirement in ADR 0045 and ADR 0046

## Context

ADR 0045 and ADR 0046 had `scripts/check_pull_request.py` refuse a pull
request that did not change `RELEASE.md`, or whose `RELEASE.md` heading named
a version other than the one in `pyproject.toml`, and
`tests/test_check_pull_request.py` asserted the same against the repository's
own files.

But `RELEASE.md` is not a source. When a bump reaches `main`,
`publish-pypi.yml` runs `scripts/release_notes.py --version <version>`, which
takes the notes from `## [Unreleased]` in `CHANGELOG.md` (or a section already
headed with that version), overwrites `RELEASE.md` with them, and uses the
result as the body of the GitHub release. Whatever a pull request wrote there
is replaced.

So the rule asked every contributor to hand-copy an entry into a file the
release discards, and it declared an ordinary state broken: between a bump and
the release that follows it, `RELEASE.md` correctly still names the last
release. The 1.22.4 release branch failed the test suite on exactly that, with
nothing wrong in it.

## Decision

**A pull request documents a change in `CHANGELOG.md` alone.**
`scripts/check_pull_request.py` still requires a new entry under
`## [Unreleased]` or the declared version, honours `skip-changelog` and the bot
exemptions, and keeps every version-bump rule of ADR 0046. It no longer reads
`RELEASE.md`, and the repository test comparing its heading with
`pyproject.toml` is removed.

`RELEASE.md` is written only by `scripts/release_notes.py` during a release.
Between releases it describes the last one. `AGENTS.md`, `CLAUDE.md`,
`CONTRIBUTING.md` and the pull request template say to leave it alone.

## Consequences

- A contributor writes a change up once, in the file the release reads.
- A bump no longer has to be accompanied by an edit to `RELEASE.md` to pass
  the local check or the test suite.
- `RELEASE.md` on a branch is not a preview of the next release notes.
  `python scripts/release_notes.py --version 0.0.0 --date 2000-01-01` on a
  scratch copy, and `release-dry-run.yml` on the pull request, remain the way
  to see them.

## Alternatives considered

- **Keep the requirement and fix the heading on every bump.** Busywork on a
  file that is overwritten anyway, and the failure it caught was not a defect.
- **Keep only a test that the `RELEASE.md` heading parses.** Nothing parses it
  any more; the release writes it and GitHub reads it as prose.
