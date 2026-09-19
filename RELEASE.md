## check-opencloud-security 1.27.1

### Added

- Codex can use the repository's Claude Code skills, hooks, subagent roles and
  Playwright MCP configuration through portable `.agents/` and `.codex/`
  compatibility files. The original `.claude/` setup remains unchanged.

- The operator's area shows the running release and whether a newer one is
  published on GitHub (cached six hours, `COS_WEB_UPDATE_CHECK`), and a button
  installs it: the release's web bundle is verified against its Sigstore build
  attestation from this repository's release workflow, unpacked on a tmpfs
  (`COS_WEB_ADMIN_UPDATE_DIR`, mounted by every compose file) and the web and
  worker processes restart on it - a short downtime, lasting until the
  containers restart. The Docker setup wizard sets it up whenever it enables
  the operator's area. The web image now installs the `signing` extra
  ([ADR 0070](adr/0070-the-operator-area-installs-attested-releases-in-place.md)).

### Changed

- mypy now also checks the bodies of functions without annotations
  (`check_untyped_defs` in `mypy.ini`), so CI type-checks the test suite
  too. The 98 errors that surfaced - all in `tests/` - are fixed.

### Fixed

- The Codex scan driver no longer prints the raw scanner document, which could
  expose TLS inspection data in its JSON output; `scan --json` now emits only
  the version, verdict and failed checks.

- The operator area's **Releases** tab never listed the release it was running
  on: the image is built from the version-bump commit, before the release
  workflow renames `[Unreleased]`. The page is now generated with that section
  under the `pyproject.toml` version when the changelog has no heading for it.
