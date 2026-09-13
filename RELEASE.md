## check-opencloud-security 1.22.4

### Changed

- **A pull request documents itself in `CHANGELOG.md` alone.**
  `scripts/check_pull_request.py` no longer requires `RELEASE.md` to change or
  its heading to name the version in `pyproject.toml`, and the test that
  compared the two in the repository is gone. The release workflow writes
  `RELEASE.md` from `## [Unreleased]` and overwrites it, so an entry copied
  there by hand was discarded, and between a bump and its release the file
  rightly still names the last release - which failed the suite on a branch
  with nothing wrong in it. `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md` and the
  pull request template now say to leave it to the release. See ADR 0048.

### Fixed

- **A Docker setup wizard downloaded on its own writes the Authentik
  blueprints.** `docker/README.md` says to `curl` just `setup-wizard.py`, but
  the wizard copied the blueprints from a checkout beside it and skipped any
  it could not find without a word. The generated stack mounted
  `./authentik/blueprints` anyway, Docker created it empty, and Authentik
  started with no provider: `/mcp` refused every token, and the forward auth
  in front of `/admin` answered 404, which nginx turns into a 500. The wizard
  now carries the four blueprints itself, generated into it from
  `authentik/blueprints/` by `scripts/embed_wizard_blueprints.py`, and a test
  fails when the embedded copies differ from those files. A deployment set up
  with an earlier download gets them by re-running the wizard.
- Fixed version bump.
